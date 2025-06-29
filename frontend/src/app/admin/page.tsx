"use client";
import React, { useState } from "react";
import Link from "next/link";

interface Booking {
  id: string;
  bookingId: string;
  pnr: string;
  status: "CONFIRMED" | "PENDING" | "CANCELLED";
  ticketStatus: "processing" | "ready" | "failed" | "cancelled";
  user: {
    id: string;
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
  };
  flightDetails: {
    origin: string;
    destination: string;
    departureDate: string;
    returnDate?: string;
    airline: string;
    flightNumber: string;
  };
  passengers: Array<{
    id: string;
    type: string;
    name: string;
  }>;
  pricing: {
    total: string;
    currency: string;
  };
  bookingDate: string;
  ticketUrl?: string;
  adminNotes?: string;
}

// Mock data for demonstration
const mockBookings: Booking[] = [
  {
    id: "1",
    bookingId: "MOCK_BOOKING_ID_1703123456789",
    pnr: "ABC123",
    status: "CONFIRMED",
    ticketStatus: "ready",
    user: {
      id: "1",
      firstName: "John",
      lastName: "Smith",
      email: "john.smith@email.com",
      phone: "+1 555-123-4567",
    },
    flightDetails: {
      origin: "SYD",
      destination: "SIN",
      departureDate: "2024-03-15",
      returnDate: "2024-03-22",
      airline: "Singapore Airlines",
      flightNumber: "SQ221",
    },
    passengers: [
      { id: "1", type: "Adult", name: "John Smith" },
      { id: "2", type: "Child", name: "Jane Smith" },
    ],
    pricing: {
      total: "546.70",
      currency: "EUR",
    },
    bookingDate: "2023-12-21T10:30:00Z",
    ticketUrl: "/tickets/MOCK_BOOKING_ID_1703123456789.pdf",
    adminNotes: "Tickets uploaded successfully",
  },
  {
    id: "2",
    bookingId: "MOCK_BOOKING_ID_1703123456790",
    pnr: "DEF456",
    status: "CONFIRMED",
    ticketStatus: "processing",
    user: {
      id: "2",
      firstName: "Sarah",
      lastName: "Johnson",
      email: "sarah.johnson@email.com",
      phone: "+1 555-987-6543",
    },
    flightDetails: {
      origin: "LAX",
      destination: "JFK",
      departureDate: "2024-04-10",
      airline: "American Airlines",
      flightNumber: "AA123",
    },
    passengers: [
      { id: "1", type: "Adult", name: "Sarah Johnson" },
    ],
    pricing: {
      total: "299.99",
      currency: "USD",
    },
    bookingDate: "2023-12-21T14:20:00Z",
    adminNotes: "Awaiting ticket from airline",
  },
  {
    id: "3",
    bookingId: "MOCK_BOOKING_ID_1703123456791",
    pnr: "GHI789",
    status: "CONFIRMED",
    ticketStatus: "failed",
    user: {
      id: "3",
      firstName: "Michael",
      lastName: "Brown",
      email: "michael.brown@email.com",
      phone: "+1 555-456-7890",
    },
    flightDetails: {
      origin: "LHR",
      destination: "CDG",
      departureDate: "2024-05-01",
      returnDate: "2024-05-08",
      airline: "British Airways",
      flightNumber: "BA456",
    },
    passengers: [
      { id: "1", type: "Adult", name: "Michael Brown" },
      { id: "2", type: "Adult", name: "Emma Brown" },
      { id: "3", type: "Child", name: "Tom Brown" },
    ],
    pricing: {
      total: "789.50",
      currency: "GBP",
    },
    bookingDate: "2023-12-21T16:45:00Z",
    adminNotes: "Payment issue - need to contact customer",
  },
];

export default function AdminDashboard() {
  const [bookings, setBookings] = useState<Booking[]>(mockBookings);
  const [filter, setFilter] = useState<"all" | "processing" | "ready" | "failed">("all");
  const [searchTerm, setSearchTerm] = useState("");

  const filteredBookings = bookings.filter(booking => {
    const matchesFilter = filter === "all" ? true : booking.ticketStatus === filter;
    const matchesSearch = 
      booking.bookingId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.user.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.user.lastName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.pnr.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesFilter && matchesSearch;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "CONFIRMED":
        return "bg-green-100 text-green-800";
      case "PENDING":
        return "bg-yellow-100 text-yellow-800";
      case "CANCELLED":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getTicketStatusColor = (status: string) => {
    switch (status) {
      case "processing":
        return "bg-blue-100 text-blue-800";
      case "ready":
        return "bg-green-100 text-green-800";
      case "failed":
        return "bg-red-100 text-red-800";
      case "cancelled":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
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

  const handleUploadTicket = (bookingId: string) => {
    // In real app, this would open a file upload modal
    alert(`Upload ticket for booking ${bookingId}`);
  };

  const handleViewDetails = (bookingId: string) => {
    // Navigate to detailed booking view
    window.location.href = `/admin/bookings/${bookingId}`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center gap-2">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">Admin User</span>
              <button className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors">
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Bookings</p>
                <p className="text-2xl font-bold text-gray-900">{bookings.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg className="w-4 h-4 text-blue-600 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Processing</p>
                <p className="text-2xl font-bold text-gray-900">
                  {bookings.filter(b => b.ticketStatus === "processing").length}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Ready</p>
                <p className="text-2xl font-bold text-gray-900">
                  {bookings.filter(b => b.ticketStatus === "ready").length}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Failed</p>
                <p className="text-2xl font-bold text-gray-900">
                  {bookings.filter(b => b.ticketStatus === "failed").length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
                Search Bookings
              </label>
              <input
                type="text"
                id="search"
                placeholder="Search by booking ID, name, email, or PNR..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label htmlFor="filter" className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Status
              </label>
              <select
                id="filter"
                value={filter}
                onChange={(e) => setFilter(e.target.value as any)}
                className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">All Bookings</h2>
          </div>
          
          {filteredBookings.length === 0 ? (
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
                  {filteredBookings.map((booking) => (
                    <tr key={booking.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{booking.bookingId}</p>
                          <p className="text-sm text-gray-500">PNR: {booking.pnr}</p>
                          <p className="text-xs text-gray-400">{formatDate(booking.bookingDate)}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {booking.user.firstName} {booking.user.lastName}
                          </p>
                          <p className="text-sm text-gray-500">{booking.user.email}</p>
                          <p className="text-sm text-gray-500">{booking.user.phone}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {booking.flightDetails.origin} → {booking.flightDetails.destination}
                          </p>
                          <p className="text-sm text-gray-500">
                            {booking.flightDetails.airline} {booking.flightDetails.flightNumber}
                          </p>
                          <p className="text-sm text-gray-500">
                            {formatDate(booking.flightDetails.departureDate)}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(booking.status)}`}>
                          {booking.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getTicketStatusColor(booking.ticketStatus)}`}>
                          {booking.ticketStatus}
                        </span>
                        {booking.adminNotes && (
                          <p className="text-xs text-gray-500 mt-1">{booking.adminNotes}</p>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleViewDetails(booking.bookingId)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            View Details
                          </button>
                          {booking.ticketStatus === "processing" && (
                            <button
                              onClick={() => handleUploadTicket(booking.bookingId)}
                              className="text-green-600 hover:text-green-900"
                            >
                              Upload Ticket
                            </button>
                          )}
                          {booking.ticketStatus === "ready" && booking.ticketUrl && (
                            <a
                              href={booking.ticketUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-purple-600 hover:text-purple-900"
                            >
                              View Ticket
                            </a>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 