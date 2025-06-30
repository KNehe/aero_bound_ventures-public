"use client";
import React, { useState, useMemo } from "react";
import Link from "next/link";

// Expanded mock user bookings data (15+ rows)
const mockBookings = [
  {
    id: "1",
    bookingId: "BOOK123456",
    pnr: "PNR123",
    status: "CONFIRMED",
    ticketStatus: "ready",
    origin: "SYD",
    destination: "SIN",
    departureDate: "2024-07-01",
    returnDate: "2024-07-10",
    airline: "Singapore Airlines",
    flightNumber: "SQ221",
    passengers: 2,
    total: "1200.00",
    currency: "USD",
    ticketUrl: "/tickets/BOOK123456.pdf",
    issuedAt: "2024-06-01",
    passengerNames: ["John Smith", "Jane Smith"],
  },
  {
    id: "2",
    bookingId: "BOOK654321",
    pnr: "PNR654",
    status: "PENDING",
    ticketStatus: "processing",
    origin: "LAX",
    destination: "JFK",
    departureDate: "2024-08-15",
    returnDate: null,
    airline: "Delta",
    flightNumber: "DL123",
    passengers: 1,
    total: "450.00",
    currency: "USD",
    ticketUrl: null,
    issuedAt: null,
    passengerNames: ["Sarah Johnson"],
  },
  // Add more mock bookings for demonstration
  ...Array.from({ length: 14 }).map((_, i) => ({
    id: String(i + 3),
    bookingId: `BOOK${100000 + i}`,
    pnr: `PNR${200 + i}`,
    status: i % 3 === 0 ? "CONFIRMED" : i % 3 === 1 ? "PENDING" : "CANCELLED",
    ticketStatus: i % 4 === 0 ? "ready" : i % 4 === 1 ? "processing" : i % 4 === 2 ? "failed" : "cancelled",
    origin: ["SYD", "LAX", "JFK", "LHR", "CDG"][i % 5],
    destination: ["SIN", "JFK", "LHR", "CDG", "SYD"][i % 5],
    departureDate: `2024-07-${(i % 28) + 1}`,
    returnDate: i % 2 === 0 ? `2024-07-${(i % 28) + 5}` : null,
    airline: ["Singapore Airlines", "Delta", "Qantas", "British Airways"][i % 4],
    flightNumber: `FL${100 + i}`,
    passengers: (i % 4) + 1,
    total: (400 + i * 25).toFixed(2),
    currency: "USD",
    ticketUrl: i % 4 === 0 ? `/tickets/BOOK${100000 + i}.pdf` : null,
    issuedAt: i % 4 === 0 ? `2024-06-${(i % 28) + 1}` : null,
    passengerNames: Array.from({ length: (i % 4) + 1 }).map((_, j) => `Passenger ${j + 1}`),
  })),
];

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

const PAGE_SIZE = 10;

export default function MyBookingsAndTicketsPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  // Filter bookings by search
  const filtered = useMemo(() => {
    if (!search.trim()) return mockBookings;
    const s = search.toLowerCase();
    return mockBookings.filter(b =>
      b.bookingId.toLowerCase().includes(s) ||
      b.pnr.toLowerCase().includes(s) ||
      b.origin.toLowerCase().includes(s) ||
      b.destination.toLowerCase().includes(s) ||
      b.passengerNames.some(name => name.toLowerCase().includes(s))
    );
  }, [search]);

  // Pagination
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Reset to page 1 on new search
  React.useEffect(() => { setPage(1); }, [search]);

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">My Bookings & Tickets</h1>
        <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by Booking ID, PNR, passenger, or route..."
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
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Route</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Dates</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Passengers</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Total</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Booking Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Ticket Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginated.map((booking) => (
                  <tr key={booking.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-sm text-gray-900">{booking.bookingId}</td>
                    <td className="px-4 py-3 font-mono text-sm text-gray-900">{booking.pnr}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {booking.origin} → {booking.destination}
                      <div className="text-xs text-gray-500">{booking.airline} {booking.flightNumber}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {booking.departureDate}
                      {booking.returnDate && (
                        <>
                          <br />Return: {booking.returnDate}
                        </>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {booking.passengerNames.join(", ")}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 font-semibold">
                      {booking.currency} {booking.total}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(booking.status)}`}>{booking.status}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTicketStatusColor(booking.ticketStatus)}`}>{booking.ticketStatus}</span>
                      {booking.issuedAt && (
                        <div className="text-xs text-gray-500 mt-1">Issued: {booking.issuedAt}</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-2 min-w-[120px]">
                        <Link href={`/booking/${booking.bookingId}`} className="text-blue-600 hover:underline text-xs font-medium">View Details</Link>
                        {booking.ticketStatus === "ready" && booking.ticketUrl && (
                          <a href={booking.ticketUrl} target="_blank" rel="noopener noreferrer" className="text-green-600 hover:underline text-xs font-medium">Download Ticket</a>
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
      </div>
    </div>
  );
} 