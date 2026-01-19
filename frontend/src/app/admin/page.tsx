"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import useAuth from "@/store/auth";
import { Booking, BookingStats, CursorPaginatedBookingsResponse } from "@/types/admin";
import { apiClient, isUnauthorizedError, getApiBaseUrl } from "@/lib/api";

const BOOKING_STATUS = {
  CONFIRMED: "confirmed",
  PAID: "paid",
  PENDING: "pending",
  CANCELLED: "cancelled",
  REVERSED: "reversed",
  FAILED: "failed",
  REFUNDED: "refunded",
} as const;

export default function AdminDashboard() {
  const router = useRouter();
  const { logout, userInfo, isAuthenticated } = useAuth();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [filter, setFilter] = useState<"all" | "processing" | "ready" | "failed">("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [stats, setStats] = useState<BookingStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [isLoadingBookings, setIsLoadingBookings] = useState(true);
  const [bookingsError, setBookingsError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const PAGE_SIZE = 20;

  const filteredBookings = bookings.filter(booking => {
    const matchesFilter = filter === "all" ? true : booking.ticket_url ? "ready" : "processing";
    const pnr = booking.amadeus_order_response?.associatedRecords?.[0]?.reference || "";
    const matchesSearch = 
      booking.flight_order_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      pnr.toLowerCase().includes(searchTerm.toLowerCase());
    
    return (filter === "all" || matchesFilter === filter) && matchesSearch;
  });

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
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
        return "bg-gray-100 text-gray-800";
    }
  };

  const getTicketStatusColor = (hasTicket: boolean) => {
    return hasTicket ? "bg-green-100 text-green-800" : "bg-blue-100 text-blue-800";
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Helper to extract PNR from amadeus_order_response
  const extractPNR = (amadeusOrder: any): string => {
    try {
      return amadeusOrder?.associatedRecords?.[0]?.reference || 'N/A';
    } catch {
      return 'N/A';
    }
  };

  // Helper to extract flight details from amadeus_order_response
  const extractFlightDetails = (amadeusOrder: any) => {
    try {
      const flight = amadeusOrder?.flightOffers?.[0];
      const itinerary = flight?.itineraries?.[0];
      const segment = itinerary?.segments?.[0];
      
      return {
        origin: segment?.departure?.iataCode || 'N/A',
        destination: segment?.arrival?.iataCode || 'N/A',
        airline: segment?.carrierCode || 'N/A',
        flightNumber: segment?.number || 'N/A',
        departureDate: segment?.departure?.at || 'N/A',
      };
    } catch {
      return {
        origin: 'N/A',
        destination: 'N/A',
        airline: 'N/A',
        flightNumber: 'N/A',
        departureDate: 'N/A',
      };
    }
  };

  const handleViewDetails = (bookingId: string) => {
    // Navigate to detailed booking view
    window.location.href = `/admin/bookings/${bookingId}`;
  };

  // Fetch booking statistics from API
  useEffect(() => {
    const fetchStats = async () => {
      try {
        setIsLoadingStats(true);
        setStatsError(null);
        
        const data = await apiClient.get<BookingStats>('/admin/stats/bookings');
        setStats(data);
      } catch (error) {
        console.error("Error fetching booking stats:", error);
        if (isUnauthorizedError(error)) {
          await logout();
          router.push('/auth/login?redirect=/admin');
          return;
        }
        setStatsError(error instanceof Error ? error.message : "Failed to load statistics");
      } finally {
        setIsLoadingStats(false);
      }
    };
    
    fetchStats();
  }, [logout, router]);

  const fetchBookings = async (cursor?: string | null) => {
    try {
      setIsLoadingBookings(true);
      setBookingsError(null);
      const params = new URLSearchParams({ limit: String(PAGE_SIZE) });
      if (cursor) params.append('cursor', cursor);
      const data = await apiClient.get<CursorPaginatedBookingsResponse>(`/admin/bookings?${params.toString()}`);
      setBookings(prev => cursor ? [...prev, ...data.items] : data.items);
      setNextCursor(data.next_cursor);
      setHasMore(data.has_more);
    } catch (error) {
      console.error("Error fetching bookings:", error);
      if (isUnauthorizedError(error)) {
        await logout();
        router.push('/auth/login?redirect=/admin');
        return;
      }
      setBookingsError(error instanceof Error ? error.message : "Failed to load bookings");
    } finally {
      setIsLoadingBookings(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, [logout, router]);

  useEffect(() => {
    const url  = `${getApiBaseUrl()}/notifications/${userInfo?.id}`;
    const sse = new EventSource(url, { withCredentials: true });

    sse.onmessage = (event) => {
      console.log(event.data)
    }

    sse.onerror = (error) => {
      console.error("SSE connection error", error);
      sse.close();
    }

  }, [])
  // Use API stats only - no fallback to mock data
  const statsTotalBookings = stats?.total_bookings;
  const totalRevenue = stats?.total_revenue;
  const activeUsers = stats?.active_users;
  const bookingsToday = stats?.bookings_today;
  const bookingsThisWeek = stats?.bookings_this_week;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-gray-600">Admin User</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Alert */}
        {statsError && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-red-700">{statsError}</p>
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">{isLoadingStats ? (
            // Loading skeletons
            <>
              {[...Array(4)].map((_, i) => (
                <div key={i} className="bg-white rounded-lg shadow-sm border p-6">
                  <div className="animate-pulse">
                    <div className="flex items-center">
                      <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
                      <div className="ml-4 flex-1">
                        <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
                        <div className="h-6 bg-gray-200 rounded w-16"></div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </>
          ) : (
            <>
          {/* Total Bookings */}
          <div className="bg-gradient-to-br from-white to-blue-50 rounded-lg shadow-md border border-blue-100 p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-sm">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-gray-600">Total Bookings</p>
                <p className="text-3xl font-bold text-gray-900">
                  {statsTotalBookings !== undefined ? statsTotalBookings : (
                    <span className="text-red-500">N/A</span>
                  )}
                </p>
              </div>
            </div>
          </div>
          
          {/* Revenue */}
          <div className="bg-gradient-to-br from-white to-green-50 rounded-lg shadow-md border border-green-100 p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center shadow-sm">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-gray-600">Total Revenue</p>
                <p className="text-3xl font-bold text-gray-900">
                  {totalRevenue !== undefined ? (
                    `$${totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                  ) : (
                    <span className="text-red-500">N/A</span>
                  )}
                </p>
              </div>
            </div>
          </div>
          
          {/* Active Users */}
          <div className="bg-gradient-to-br from-white to-purple-50 rounded-lg shadow-md border border-purple-100 p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center shadow-sm">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-gray-600">Active Users</p>
                <p className="text-3xl font-bold text-gray-900">
                  {activeUsers !== undefined ? activeUsers : (
                    <span className="text-red-500">N/A</span>
                  )}
                </p>
              </div>
            </div>
          </div>
          
          {/* Bookings Today/Week */}
          <div className="bg-gradient-to-br from-white to-orange-50 rounded-lg shadow-md border border-orange-100 p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="w-14 h-14 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center shadow-sm">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-gray-600">Bookings (Today/Week)</p>
                <div className="flex items-baseline gap-1">
                  {bookingsToday !== undefined && bookingsThisWeek !== undefined ? (
                    <>
                      <p className="text-3xl font-bold text-gray-900">{bookingsToday}</p>
                      <span className="text-gray-400">/</span>
                      <p className="text-xl font-semibold text-gray-600">{bookingsThisWeek}</p>
                    </>
                  ) : (
                    <span className="text-3xl font-bold text-red-500">N/A</span>
                  )}
                </div>
              </div>
            </div>
          </div>
            </>
          )}
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-lg shadow-md border p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="flex-1">
              <label htmlFor="search" className="block text-sm font-semibold text-gray-700 mb-2">
                Search Bookings
              </label>
              <div className="relative">
                <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  id="search"
                  placeholder="Search by booking ID, email, or PNR..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                />
              </div>
            </div>
            <div>
              <label htmlFor="filter" className="block text-sm font-semibold text-gray-700 mb-2">
                Filter by Status
              </label>
              <select
                id="filter"
                value={filter}
                onChange={(e) => setFilter(e.target.value as any)}
                className="border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 min-w-[160px]"
              >
                <option value="all">All Statuses</option>
                <option value="processing">Processing</option>
                <option value="ready">Ready</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Bookings Table */}
        <div className="bg-white rounded-lg shadow-md border overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white">
            <h2 className="text-xl font-bold text-gray-900">All Bookings</h2>
          </div>
          
          {bookingsError && (
            <div className="p-6 bg-red-50 border-b border-red-200">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-red-700">{bookingsError}</p>
              </div>
            </div>
          )}
          
          {isLoadingBookings ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading bookings...</p>
            </div>
          ) : filteredBookings.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No bookings found</h3>
              <p className="text-gray-600">
                {searchTerm ? "Try adjusting your search criteria." : "No bookings match the current filter."}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Booking Details
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Customer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Flight
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ticket Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredBookings.map((booking) => {
                    const pnr = extractPNR(booking.amadeus_order_response);
                    const flightDetails = extractFlightDetails(booking.amadeus_order_response);
                    const ticketStatus = booking.ticket_url ? 'ready' : 'pending';
                    
                    return (
                      <tr key={booking.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <p className="text-base font-medium text-gray-900">{booking.flight_order_id}</p>
                            <p className="text-base text-gray-500">PNR: {pnr}</p>
                            <p className="text-sm text-gray-400">{formatDate(booking.created_at)}</p>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <p className="text-base font-medium text-gray-900">{booking.user.email}</p>
                            <p className="text-sm text-gray-500">ID: {booking.user.id}</p>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <p className="text-base font-medium text-gray-900">
                              {flightDetails.origin} → {flightDetails.destination}
                            </p>
                            <p className="text-base text-gray-500">
                              {flightDetails.airline} {flightDetails.flightNumber}
                            </p>
                            <p className="text-base text-gray-500">
                              {flightDetails.departureDate !== 'N/A' ? formatDate(flightDetails.departureDate) : 'N/A'}
                            </p>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-sm font-medium rounded-full ${getStatusColor(booking.status)}`}>
                            {booking.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-sm font-medium rounded-full ${getTicketStatusColor(!!booking.ticket_url)}`}>
                            {ticketStatus}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-base font-medium">
                          <button
                            onClick={() => handleViewDetails(booking.id)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Pagination Controls */}
          {hasMore && (
            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-center">
              <button
                onClick={() => fetchBookings(nextCursor)}
                disabled={isLoadingBookings}
                className="px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoadingBookings ? 'Loading...' : 'Load More'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 