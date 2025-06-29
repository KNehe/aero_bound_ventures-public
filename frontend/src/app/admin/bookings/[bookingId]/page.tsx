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
    address: {
      street: string;
      city: string;
      postalCode: string;
      country: string;
    };
  };
  flightDetails: {
    origin: string;
    destination: string;
    departureDate: string;
    returnDate?: string;
    airline: string;
    flightNumber: string;
    segments: Array<{
      departure: { airport: string; time: string; terminal?: string };
      arrival: { airport: string; time: string; terminal?: string };
      flight: string;
      duration: string;
    }>;
  };
  passengers: Array<{
    id: string;
    type: string;
    name: string;
    dateOfBirth: string;
    gender: string;
    passportNumber?: string;
    seat?: string;
  }>;
  pricing: {
    total: string;
    currency: string;
    breakdown: Array<{
      item: string;
      amount: string;
    }>;
  };
  bookingDate: string;
  ticketUrl?: string;
  adminNotes?: string;
  paymentStatus: "PAID" | "PENDING" | "FAILED";
}

// Mock data for demonstration
const mockBooking: Booking = {
  id: "1",
  bookingId: "MOCK_BOOKING_ID_1703123456789",
  pnr: "ABC123",
  status: "CONFIRMED",
  ticketStatus: "processing",
  user: {
    id: "1",
    firstName: "John",
    lastName: "Smith",
    email: "john.smith@email.com",
    phone: "+1 555-123-4567",
    address: {
      street: "123 Main Street",
      city: "New York",
      postalCode: "10001",
      country: "United States",
    },
  },
  flightDetails: {
    origin: "SYD",
    destination: "SIN",
    departureDate: "2024-03-15",
    returnDate: "2024-03-22",
    airline: "Singapore Airlines",
    flightNumber: "SQ221",
    segments: [
      {
        departure: { airport: "SYD", time: "19:15", terminal: "1" },
        arrival: { airport: "SIN", time: "00:30", terminal: "1" },
        flight: "SQ221",
        duration: "8h 15m",
      },
    ],
  },
  passengers: [
    {
      id: "1",
      type: "Adult",
      name: "John Smith",
      dateOfBirth: "1985-06-15",
      gender: "Male",
      passportNumber: "US123456789",
    },
    {
      id: "2",
      type: "Child",
      name: "Jane Smith",
      dateOfBirth: "2015-03-22",
      gender: "Female",
      passportNumber: "US987654321",
    },
  ],
  pricing: {
    total: "546.70",
    currency: "EUR",
    breakdown: [
      { item: "Base Fare", amount: "334.00" },
      { item: "Taxes & Fees", amount: "212.70" },
    ],
  },
  bookingDate: "2023-12-21T10:30:00Z",
  adminNotes: "Awaiting ticket from airline consolidator",
  paymentStatus: "PAID",
};

export default function AdminBookingDetailPage({ params }: { params: Promise<{ bookingId: string }> }) {
  const resolvedParams = React.use(params);
  const [booking] = useState<Booking>(mockBooking);
  const [adminNotes, setAdminNotes] = useState(booking.adminNotes || "");
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const formatTime = (timeString: string) => {
    return timeString;
  };

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

  const getPaymentStatusColor = (status: string) => {
    switch (status) {
      case "PAID":
        return "bg-green-100 text-green-800";
      case "PENDING":
        return "bg-yellow-100 text-yellow-800";
      case "FAILED":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUploadTicket = () => {
    if (selectedFile) {
      // In real app, this would upload to server and update booking
      alert(`Uploading ${selectedFile.name} for booking ${booking.bookingId}`);
      setShowUploadModal(false);
      setSelectedFile(null);
    }
  };

  const handleSaveNotes = () => {
    // In real app, this would save to database
    alert("Admin notes saved successfully");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center gap-4">
              <Link
                href="/admin"
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                <span>Back to Dashboard</span>
              </Link>
              <div className="h-6 w-px bg-gray-300"></div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Booking Details</h1>
                <p className="text-sm text-gray-500">{booking.bookingId}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(booking.status)}`}>
                {booking.status}
              </span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getTicketStatusColor(booking.ticketStatus)}`}>
                {booking.ticketStatus}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Booking Summary */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Booking Summary</h2>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Booking ID</p>
                  <p className="font-mono font-semibold text-gray-900">{booking.bookingId}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">PNR</p>
                  <p className="font-mono font-semibold text-gray-900">{booking.pnr}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Booking Date</p>
                  <p className="text-gray-900">{formatDate(booking.bookingDate)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Amount</p>
                  <p className="text-lg font-bold text-gray-900">{booking.pricing.currency} {booking.pricing.total}</p>
                </div>
              </div>
            </div>

            {/* Flight Details */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Flight Details</h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">
                      {booking.flightDetails.origin} → {booking.flightDetails.destination}
                    </h3>
                    <p className="text-gray-600">
                      {booking.flightDetails.airline} {booking.flightDetails.flightNumber}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">Departure</p>
                    <p className="font-semibold text-gray-900">{formatDate(booking.flightDetails.departureDate)}</p>
                  </div>
                </div>

                {booking.flightDetails.segments.map((segment, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-lg font-semibold text-gray-900">
                          {formatTime(segment.departure.time)}
                        </div>
                        <div className="text-sm text-gray-600">
                          {segment.departure.airport}
                          {segment.departure.terminal && ` Terminal ${segment.departure.terminal}`}
                        </div>
                      </div>
                      <div className="flex-1 mx-4">
                        <div className="flex items-center">
                          <div className="flex-1 h-px bg-gray-300"></div>
                          <div className="mx-2 text-xs text-gray-500">
                            {segment.duration}
                          </div>
                          <div className="flex-1 h-px bg-gray-300"></div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-semibold text-gray-900">
                          {formatTime(segment.arrival.time)}
                        </div>
                        <div className="text-sm text-gray-600">
                          {segment.arrival.airport}
                          {segment.arrival.terminal && ` Terminal ${segment.arrival.terminal}`}
                        </div>
                      </div>
                    </div>
                    <div className="text-sm text-gray-600 mt-2">
                      Flight {segment.flight}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Passenger Information */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Passenger Information</h2>
              
              <div className="space-y-4">
                {booking.passengers.map((passenger) => (
                  <div key={passenger.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-semibold text-gray-800">{passenger.name}</h3>
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full capitalize">
                        {passenger.type}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Date of Birth</p>
                        <p className="font-medium text-gray-900">{formatDate(passenger.dateOfBirth)}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Gender</p>
                        <p className="font-medium text-gray-900">{passenger.gender}</p>
                      </div>
                      {passenger.passportNumber && (
                        <div>
                          <p className="text-gray-500">Passport</p>
                          <p className="font-mono text-gray-900">{passenger.passportNumber}</p>
                        </div>
                      )}
                      {passenger.seat && (
                        <div>
                          <p className="text-gray-500">Seat</p>
                          <p className="font-medium text-gray-900">{passenger.seat}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Pricing Breakdown */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Pricing Breakdown</h2>
              
              <div className="space-y-3">
                {booking.pricing.breakdown.map((item, index) => (
                  <div key={index} className="flex justify-between">
                    <span className="text-gray-600">{item.item}</span>
                    <span className="text-gray-900">{booking.pricing.currency} {item.amount}</span>
                  </div>
                ))}
                <div className="border-t border-gray-200 pt-3">
                  <div className="flex justify-between text-lg font-bold">
                    <span>Total</span>
                    <span>{booking.pricing.currency} {booking.pricing.total}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Customer Information */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Customer Information</h2>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Name</p>
                  <p className="font-semibold text-gray-900">
                    {booking.user.firstName} {booking.user.lastName}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="text-gray-900">{booking.user.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Phone</p>
                  <p className="text-gray-900">{booking.user.phone}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Address</p>
                  <p className="text-gray-900">
                    {booking.user.address.street}<br />
                    {booking.user.address.city}, {booking.user.address.postalCode}<br />
                    {booking.user.address.country}
                  </p>
                </div>
              </div>
            </div>

            {/* Payment Status */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Payment Status</h2>
              <div className="flex items-center justify-between">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPaymentStatusColor(booking.paymentStatus)}`}>
                  {booking.paymentStatus}
                </span>
                <p className="text-lg font-bold text-gray-900">
                  {booking.pricing.currency} {booking.pricing.total}
                </p>
              </div>
            </div>

            {/* Admin Actions */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Admin Actions</h2>
              
              <div className="space-y-3">
                {booking.ticketStatus === "processing" && (
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                  >
                    Upload Ticket
                  </button>
                )}
                
                {booking.ticketStatus === "ready" && booking.ticketUrl && (
                  <a
                    href={booking.ticketUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors text-center"
                  >
                    View Ticket
                  </a>
                )}
                
                <button
                  onClick={() => window.print()}
                  className="w-full bg-gray-600 hover:bg-gray-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                  Print Details
                </button>
                
                <button className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors">
                  Cancel Booking
                </button>
              </div>
            </div>

            {/* Admin Notes */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Admin Notes</h2>
              <textarea
                value={adminNotes}
                onChange={(e) => setAdminNotes(e.target.value)}
                placeholder="Add notes about this booking..."
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 h-32 resize-none"
              />
              <button
                onClick={handleSaveNotes}
                className="mt-3 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
              >
                Save Notes
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Ticket Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Ticket</h3>
              <p className="text-gray-600 mb-4">
                Upload the ticket PDF for booking {booking.bookingId}
              </p>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="ticket-upload"
                />
                <label htmlFor="ticket-upload" className="cursor-pointer">
                  <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-gray-600">
                    {selectedFile ? selectedFile.name : "Click to select PDF file"}
                  </p>
                </label>
              </div>
              
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUploadTicket}
                  disabled={!selectedFile}
                  className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Upload
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 