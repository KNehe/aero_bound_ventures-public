"use client";
import React, { useState, useMemo, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import useAuth from '@/store/auth';

interface Booking {
  id: string;
  pnr: string | null;
  status: string;
  created_at: string;
  ticket_url: string | null;
}

export default function MyBookingsAndTicketsPage() {
  const token = useAuth((state) => state.token);
  const logout = useAuth((state) => state.logout);
  const router = useRouter();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [isHydrated, setIsHydrated] = useState(false);
  
  const PAGE_SIZE = 10;

  const BOOKING_STATUS = {
    CONFIRMED: "confirmed",
    PAID: "paid",
    PENDING: "pending",
    CANCELLED: "cancelled",
    REVERSED: "reversed",
    FAILED: "failed",
    REFUNDED: "refunded",
  } as const;

  // Handle hydration
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    // Wait for hydration and check if user is authenticated
    if (!isHydrated) return;
    
    if (!token) {
      router.push('/auth/login?redirect=/my');
      return;
    }

    const fetchBookings = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/bookings`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.status === 401) {
          logout();
          router.push('/auth/login?redirect=/my');
          return;
        }

        if (!response.ok) {
          throw new Error(`Failed to fetch bookings: ${response.status}`);
        }

        const data = await response.json();
        setBookings(data);
      } catch (err) {
        console.error('Error fetching bookings:', err);
        setError(err instanceof Error ? err.message : 'Failed to load bookings');
      } finally {
        setLoading(false);
      }
    };

    fetchBookings();
  }, [token, isHydrated, router, logout]);

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

  // Filter bookings by search
  const filtered = useMemo(() => {
    if (!search.trim()) return bookings;
    const s = search.toLowerCase();
    return bookings.filter(b =>
      b.id.toLowerCase().includes(s) ||
      (b.pnr && b.pnr.toLowerCase().includes(s))
    );
  }, [search, bookings]);

  // Pagination
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Reset to page 1 on new search
  useEffect(() => { setPage(1); }, [search]);

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">My Bookings & Tickets</h1>

        {loading ? (
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading your bookings...</p>
          </div>
        ) : error ? (
          <div className="text-center py-20">
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
            <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search by Booking ID or PNR..."
                className="w-full md:w-96 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder-gray-700"
              />
              <div className="flex items-center gap-2 text-sm text-gray-600">
                Showing {paginated.length} of {filtered.length} bookings
              </div>
            </div>
            {filtered.length === 0 ? (
              <div className="text-center py-20">
                <h2 className="text-xl font-semibold text-gray-700 mb-2">No bookings found</h2>
                <p className="text-gray-500">Try a different search or book a new flight.</p>
                <Link href="/" className="mt-6 inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium">Book a Flight</Link>
              </div>
            ) : (
              <div className="overflow-x-auto bg-white rounded-lg shadow-sm border">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Booking ID</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">PNR</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Created Date</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {paginated.map((booking: Booking) => (
                      <tr key={booking.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 font-mono text-sm text-gray-900">{booking.id}</td>
                        <td className="px-4 py-3 font-mono text-sm text-gray-900">{booking.pnr || 'N/A'}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(booking.status)}`}>
                            {booking.status.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {new Date(booking.created_at).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-col gap-2 min-w-[120px]">
                            <Link href={`/booking/success/${booking.id}`} className="text-blue-600 hover:underline text-xs font-medium">View Details</Link>
                            {booking.ticket_url ? (
                              <a href={booking.ticket_url} target="_blank" rel="noopener noreferrer" className="text-green-600 hover:underline text-xs font-medium flex items-center gap-1">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                                Download Ticket
                              </a>
                            ) : (booking.status === BOOKING_STATUS.PAID) ? (
                              <span className="text-amber-600 text-xs font-medium flex items-center gap-1" title="Your ticket is being generated">
                                <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                Processing Ticket...
                              </span>
                            ) : (
                              <span className="text-gray-400 text-xs">Pay to get ticket</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {/* Pagination Controls */}
                <div className="flex items-center justify-between px-4 py-4 bg-gray-50 border-t">
                  <div className="text-sm text-gray-600">
                    Page {page} of {totalPages}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-3 py-1 rounded bg-gray-200 text-gray-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="px-3 py-1 rounded bg-gray-200 text-gray-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}