"use client";
import React, { useState, useMemo, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import useAuth from '@/store/auth';
import { apiClient, isUnauthorizedError } from '@/lib/api';

interface Booking {
  id: string;
  pnr: string | null;
  status: string;
  created_at: string;
  ticket_url: string | null;
}

interface PaginatedBookingsResponse {
  items: Booking[];
  total: number;
  skip: number;
  limit: number;
}

interface CancelModalState {
  isOpen: boolean;
  bookingId: string | null;
  pnr: string | null;
  isLoading: boolean;
}

interface CancelBookingResponse {
  id: string;
  status: string;
  message: string;
}

const BOOKING_STATUS = {
  CONFIRMED: "confirmed",
  PAID: "paid",
  PENDING: "pending",
  CANCELLED: "cancelled",
  REVERSED: "reversed",
  FAILED: "failed",
  REFUNDED: "refunded",
} as const;

export default function MyBookingsAndTicketsPage() {
  const isAuthenticated = useAuth((state) => state.isAuthenticated);
  const logout = useAuth((state) => state.logout);
  const router = useRouter();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalBookings, setTotalBookings] = useState(0);
  const [search, setSearch] = useState("");
  const [isHydrated, setIsHydrated] = useState(false);
  const [cancelModal, setCancelModal] = useState<CancelModalState>({
    isOpen: false,
    bookingId: null,
    pnr: null,
    isLoading: false,
  });
  const [cancelError, setCancelError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  const PAGE_SIZE = 20;

  const handleDownloadTicket = async (ticketUrl: string, bookingId: string) => {
    try {
      const response = await fetch(ticketUrl);
      const blob = await response.blob();
      
      // Detect file extension from content type or URL
      let extension = 'pdf';
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('image/jpeg') || contentType?.includes('image/jpg')) {
        extension = 'jpg';
      } else if (contentType?.includes('image/png')) {
        extension = 'png';
      } else if (ticketUrl.match(/\.(jpg|jpeg|png|pdf)$/i)) {
        extension = ticketUrl.match(/\.(jpg|jpeg|png|pdf)$/i)![1].toLowerCase();
      }
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ticket-${bookingId}.${extension}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading ticket:', error);
    }
  };

  const handleViewTicket = (ticketUrl: string) => {
    window.open(ticketUrl, '_blank');
  };

  const canCancelBooking = (status: string): boolean => {
    const cancellableStatuses: string[] = [
      BOOKING_STATUS.CONFIRMED,
      BOOKING_STATUS.PENDING,
      BOOKING_STATUS.PAID,
    ];
    return cancellableStatuses.includes(status);
  };

  const openCancelModal = (bookingId: string, pnr: string | null) => {
    setCancelError(null);
    setCancelModal({
      isOpen: true,
      bookingId,
      pnr,
      isLoading: false,
    });
  };

  const closeCancelModal = () => {
    setCancelModal({
      isOpen: false,
      bookingId: null,
      pnr: null,
      isLoading: false,
    });
    setCancelError(null);
  };

  const handleCancelBooking = async () => {
    if (!cancelModal.bookingId) return;

    setCancelModal(prev => ({ ...prev, isLoading: true }));
    setCancelError(null);

    try {
      const response = await apiClient.delete<CancelBookingResponse>(
        `/booking/flight-orders/${cancelModal.bookingId}`
      );
      
      setBookings(prev =>
        prev.map(booking =>
          booking.id === cancelModal.bookingId
            ? { ...booking, status: BOOKING_STATUS.CANCELLED }
            : booking
        )
      );
      
      closeCancelModal();
      
      // Show success message
      setSuccessMessage(response.message || 'Booking cancelled successfully');
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      console.error('Error cancelling booking:', err);
      if (isUnauthorizedError(err)) {
        await logout();
        router.push('/auth/login?redirect=/my');
        return;
      }
      setCancelError(err instanceof Error ? err.message : 'Failed to cancel booking');
      setCancelModal(prev => ({ ...prev, isLoading: false }));
    }
  };

  // Handle hydration
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    // Wait for hydration and check if user is authenticated
    if (!isHydrated) return;
    
    if (!isAuthenticated) {
      router.push('/auth/login?redirect=/my');
      return;
    }

    const fetchBookings = async () => {
      try {
        setLoading(true);
        const skip = (page - 1) * PAGE_SIZE;
        const data = await apiClient.get<PaginatedBookingsResponse>(`/bookings?skip=${skip}&limit=${PAGE_SIZE}`);
        setBookings(data.items);
        setTotalBookings(data.total);
      } catch (err) {
        console.error('Error fetching bookings:', err);
        if (isUnauthorizedError(err)) {
          await logout();
          router.push('/auth/login?redirect=/my');
          return;
        }
        setError(err instanceof Error ? err.message : 'Failed to load bookings');
      } finally {
        setLoading(false);
      }
    };

    fetchBookings();
  }, [isAuthenticated, isHydrated, router, logout, page]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case BOOKING_STATUS.CONFIRMED:
        return "bg-green-100 text-green-800";
      case BOOKING_STATUS.PAID:
        return "bg-green-100 text-green-800";
      case BOOKING_STATUS.PENDING:
        return "bg-yellow-100 text-yellow-800";
      case BOOKING_STATUS.CANCELLED:
        return "bg-red-100 text-red-800";
      case BOOKING_STATUS.FAILED:
        return "bg-red-100 text-red-800";
      case BOOKING_STATUS.REVERSED:
        return "bg-orange-100 text-orange-800";
      case BOOKING_STATUS.REFUNDED:
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-500 text-gray-800";
    }
  };

  // Filter bookings by search (client-side filter on current page)
  const filtered = useMemo(() => {
    if (!search.trim()) return bookings;
    const s = search.toLowerCase();
    return bookings.filter(b =>
      b.id.toLowerCase().includes(s) ||
      (b.pnr && b.pnr.toLowerCase().includes(s))
    );
  }, [search, bookings]);

  const totalPages = Math.ceil(totalBookings / PAGE_SIZE);
  const paginated = filtered;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 py-10 px-4">
      {/* Success Toast */}
      {successMessage && (
        <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-top-2 fade-in duration-300">
          <div className="bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-3">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="font-medium">{successMessage}</span>
            <button
              onClick={() => setSuccessMessage(null)}
              className="ml-2 hover:bg-green-700 rounded p-1"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">My Bookings & Tickets</h1>
          <p className="text-gray-600">View and manage all your flight bookings in one place</p>
        </div>

        {loading ? (
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading your bookings...</p>
          </div>
        ) : error ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="text-red-600 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-700 mb-2">Error Loading Bookings</h2>
            <p className="text-gray-500 mb-4">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Try Again
            </button>
          </div>
        ) : (
          <>
            {/* Search and Stats Bar */}
            <div className="mb-6 bg-white rounded-lg shadow-sm border p-4">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div className="relative flex-1 max-w-md">
                  <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    type="text"
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    placeholder="Search by Booking ID or PNR..."
                    className="w-full border border-gray-300 rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                  />
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-lg">
                    <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <span className="text-sm font-semibold text-blue-900">{totalBookings} Total</span>
                  </div>
                  <Link
                    href="/"
                    className="hidden md:inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    New Booking
                  </Link>
                </div>
              </div>
            </div>

            {filtered.length === 0 ? (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-gray-700 mb-2">
                  {search ? "No bookings match your search" : "No bookings yet"}
                </h2>
                <p className="text-gray-500 mb-6">
                  {search ? "Try a different search term" : "Start your journey by booking a flight"}
                </p>
                <Link href="/" className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  Book a Flight
                </Link>
              </div>
            ) : (
              <>
                {/* Desktop Table View */}
                <div className="hidden lg:block overflow-x-auto bg-white rounded-lg shadow-sm border">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
                      <tr>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Booking Info</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Created</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Ticket</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {paginated.map((booking: Booking) => (
                        <tr key={booking.id} className="hover:bg-blue-50 transition-colors">
                          <td className="px-6 py-4">
                            <div>
                              <p className="text-sm font-medium text-gray-900 mb-1">ID: {booking.id.slice(0, 8)}...</p>
                              <p className="text-sm text-gray-600">PNR: {booking.pnr || 'N/A'}</p>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(booking.status)}`}>
                              {booking.status.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-700">
                            {new Date(booking.created_at).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                            })}
                          </td>
                          <td className="px-6 py-4">
                            {booking.ticket_url ? (
                              <div className="flex gap-2">
                                <button onClick={() => handleViewTicket(booking.ticket_url!)} className="inline-flex items-center gap-1 px-3 py-1.5 bg-green-100 text-green-700 rounded-md hover:bg-green-200 text-xs font-medium transition-colors">
                                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                                  View
                                </button>
                                <button onClick={() => handleDownloadTicket(booking.ticket_url!, booking.id)} className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-xs font-medium transition-colors">
                                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                                  Download
                                </button>
                              </div>
                            ) : (booking.status === BOOKING_STATUS.PAID) ? (
                              <span className="inline-flex items-center gap-1.5 text-amber-600 text-xs font-medium" title="Your ticket is being generated">
                                <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                Processing...
                              </span>
                            ) : (
                              <span className="text-gray-400 text-xs">Not available</span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <Link href={`/booking/success/${booking.id}`} className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 text-sm font-medium">
                                View Details
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                              </Link>
                              {canCancelBooking(booking.status) && (
                                <button
                                  onClick={() => openCancelModal(booking.id, booking.pnr)}
                                  className="inline-flex items-center gap-1 text-red-600 hover:text-red-700 text-sm font-medium ml-2"
                                >
                                  Cancel
                                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Mobile Card View */}
                <div className="lg:hidden space-y-4">
                  {paginated.map((booking: Booking) => (
                    <div key={booking.id} className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-gray-900 mb-1 break-all">ID: {booking.id}</p>
                          <p className="text-xs text-gray-600">PNR: {booking.pnr || 'N/A'}</p>
                        </div>
                        <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold ${getStatusColor(booking.status)}`}>
                          {booking.status.toUpperCase()}
                        </span>
                      </div>
                      
                      <div className="text-xs text-gray-500 mb-3">
                        {new Date(booking.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Link href={`/booking/success/${booking.id}`} className="flex-1 text-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-xs font-medium transition-colors">
                          View Details
                        </Link>
                        {canCancelBooking(booking.status) && (
                          <button
                            onClick={() => openCancelModal(booking.id, booking.pnr)}
                            className="flex-1 px-3 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 text-xs font-medium transition-colors"
                          >
                            Cancel
                          </button>
                        )}
                        {booking.ticket_url && (
                          <>
                            <button onClick={() => handleViewTicket(booking.ticket_url!)} className="flex-1 px-3 py-2 bg-green-100 text-green-700 rounded-md hover:bg-green-200 text-xs font-medium transition-colors">
                              View Ticket
                            </button>
                            <button onClick={() => handleDownloadTicket(booking.ticket_url!, booking.id)} className="flex-1 px-3 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-xs font-medium transition-colors">
                              Download
                            </button>
                          </>
                        )}
                        {!booking.ticket_url && booking.status === BOOKING_STATUS.PAID && (
                          <span className="flex-1 text-center px-3 py-2 bg-amber-50 text-amber-600 rounded-md text-xs font-medium">
                            Processing...
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination Controls */}
                {totalPages > 1 && (
                  <div className="mt-6 flex items-center justify-between px-4 py-4 bg-white rounded-lg shadow-sm border">
                    <div className="text-sm text-gray-600 font-medium">
                      Page {page} of {totalPages}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="px-4 py-2 rounded-lg bg-gray-100 text-gray-700 font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="px-4 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>

      {/* Cancel Confirmation Modal */}
      {cancelModal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={!cancelModal.isLoading ? closeCancelModal : undefined}
          />
          
          {/* Modal */}
          <div className="relative bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 p-6">
            <div className="text-center">
              {/* Warning Icon */}
              <div className="mx-auto w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              
              <h3 className="text-xl font-bold text-gray-900 mb-2">Cancel Booking?</h3>
              <p className="text-gray-600 mb-2">
                Are you sure you want to cancel this booking?
              </p>
              {cancelModal.pnr && (
                <p className="text-sm text-gray-500 mb-4">
                  PNR: <span className="font-semibold">{cancelModal.pnr}</span>
                </p>
              )}
              <p className="text-sm text-red-600 mb-6">
                This action cannot be undone. Refund eligibility depends on the airline&apos;s policy.
              </p>

              {cancelError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-700">{cancelError}</p>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={closeCancelModal}
                  disabled={cancelModal.isLoading}
                  className="flex-1 px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors disabled:opacity-50"
                >
                  Keep Booking
                </button>
                <button
                  onClick={handleCancelBooking}
                  disabled={cancelModal.isLoading}
                  className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {cancelModal.isLoading ? (
                    <>
                      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Cancelling...
                    </>
                  ) : (
                    'Yes, Cancel Booking'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}