"use client";
import React, { useState } from "react";
import Link from "next/link";

interface Ticket {
  id: string;
  bookingId: string;
  status: "processing" | "ready" | "failed" | "cancelled";
  progress: number;
  flightDetails: {
    origin: string;
    destination: string;
    departureDate: string;
    returnDate?: string;
    airline: string;
    flightNumber: string;
  };
  passengers: number;
  totalPrice: string;
  currency: string;
  bookingDate: string;
  ticketUrl?: string;
}

// Mock data for demonstration
const mockTickets: Ticket[] = [
  {
    id: "1",
    bookingId: "MOCK_BOOKING_ID_1703123456789",
    status: "ready",
    progress: 100,
    flightDetails: {
      origin: "SYD",
      destination: "SIN",
      departureDate: "2024-03-15",
      returnDate: "2024-03-22",
      airline: "Singapore Airlines",
      flightNumber: "SQ221",
    },
    passengers: 2,
    totalPrice: "546.70",
    currency: "EUR",
    bookingDate: "2023-12-21T10:30:00Z",
    ticketUrl: "/tickets/MOCK_BOOKING_ID_1703123456789.pdf",
  },
  {
    id: "2",
    bookingId: "MOCK_BOOKING_ID_1703123456790",
    status: "processing",
    progress: 65,
    flightDetails: {
      origin: "LAX",
      destination: "JFK",
      departureDate: "2024-04-10",
      airline: "American Airlines",
      flightNumber: "AA123",
    },
    passengers: 1,
    totalPrice: "299.99",
    currency: "USD",
    bookingDate: "2023-12-21T14:20:00Z",
  },
  {
    id: "3",
    bookingId: "MOCK_BOOKING_ID_1703123456791",
    status: "failed",
    progress: 0,
    flightDetails: {
      origin: "LHR",
      destination: "CDG",
      departureDate: "2024-05-01",
      returnDate: "2024-05-08",
      airline: "British Airways",
      flightNumber: "BA456",
    },
    passengers: 3,
    totalPrice: "789.50",
    currency: "GBP",
    bookingDate: "2023-12-21T16:45:00Z",
  },
];

export default function TicketsPage() {
  const [tickets] = useState<Ticket[]>(mockTickets);
  const [filter, setFilter] = useState<"all" | "processing" | "ready" | "failed">("all");

  const filteredTickets = tickets.filter(ticket => 
    filter === "all" ? true : ticket.status === filter
  );

  const getStatusColor = (status: string) => {
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "processing":
        return (
          <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      case "ready":
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case "failed":
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center gap-2">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h1 className="text-2xl font-bold text-gray-900">My Tickets</h1>
            </div>
            <Link
              href="/"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Book New Flight
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <div className="mb-6">
          <div className="flex gap-2">
            <button
              onClick={() => setFilter("all")}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filter === "all"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              All Tickets ({tickets.length})
            </button>
            <button
              onClick={() => setFilter("processing")}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filter === "processing"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              Processing ({tickets.filter(t => t.status === "processing").length})
            </button>
            <button
              onClick={() => setFilter("ready")}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filter === "ready"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              Ready ({tickets.filter(t => t.status === "ready").length})
            </button>
            <button
              onClick={() => setFilter("failed")}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filter === "failed"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              Failed ({tickets.filter(t => t.status === "failed").length})
            </button>
          </div>
        </div>

        {/* Tickets List */}
        {filteredTickets.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No tickets found</h3>
            <p className="text-gray-600 mb-4">
              {filter === "all" 
                ? "You haven't booked any flights yet." 
                : `No tickets with status "${filter}" found.`}
            </p>
            <Link
              href="/"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Book Your First Flight
            </Link>
          </div>
        ) : (
          <div className="grid gap-6">
            {filteredTickets.map((ticket) => (
              <div key={ticket.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${getStatusColor(ticket.status)}`}>
                      {getStatusIcon(ticket.status)}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {ticket.flightDetails.origin} → {ticket.flightDetails.destination}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {ticket.flightDetails.airline} {ticket.flightDetails.flightNumber}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-gray-900">
                      {ticket.currency} {ticket.totalPrice}
                    </p>
                    <p className="text-sm text-gray-500">
                      {ticket.passengers} passenger{ticket.passengers > 1 ? 's' : ''}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
                  <div>
                    <p className="text-gray-500">Departure</p>
                    <p className="font-medium">{formatDate(ticket.flightDetails.departureDate)}</p>
                  </div>
                  {ticket.flightDetails.returnDate && (
                    <div>
                      <p className="text-gray-500">Return</p>
                      <p className="font-medium">{formatDate(ticket.flightDetails.returnDate)}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-gray-500">Booking Date</p>
                    <p className="font-medium">{formatDate(ticket.bookingDate)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Booking ID</p>
                    <p className="font-mono text-xs">{ticket.bookingId}</p>
                  </div>
                </div>

                {/* Progress Bar for Processing Tickets */}
                {ticket.status === "processing" && (
                  <div className="mb-4">
                    <div className="flex justify-between text-sm text-gray-600 mb-2">
                      <span>Processing progress</span>
                      <span>{Math.round(ticket.progress)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${ticket.progress}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3">
                  {ticket.status === "ready" && ticket.ticketUrl && (
                    <>
                      <a
                        href={ticket.ticketUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium"
                      >
                        Download Ticket
                      </a>
                      <button
                        onClick={() => window.print()}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium"
                      >
                        Print Ticket
                      </button>
                    </>
                  )}
                  
                  {ticket.status === "processing" && (
                    <Link
                      href={`/tickets/processing/${ticket.bookingId}`}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium"
                    >
                      Track Processing
                    </Link>
                  )}
                  
                  {ticket.status === "failed" && (
                    <button className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 font-medium">
                      Contact Support
                    </button>
                  )}
                  
                  <Link
                    href={`/booking/success/${ticket.bookingId}`}
                    className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 font-medium"
                  >
                    View Details
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 