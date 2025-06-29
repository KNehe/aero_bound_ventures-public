"use client";
import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface BookingSuccessData {
  orderId: string;
  pnr: string;
  bookingDate: string;
  status: "CONFIRMED" | "PENDING" | "CANCELLED";
  flightDetails: {
    outbound: {
      date: string;
      segments: Array<{
        departure: { airport: string; time: string; terminal?: string };
        arrival: { airport: string; time: string; terminal?: string };
        flight: string;
        duration: string;
      }>;
    };
    return: {
      date: string;
      segments: Array<{
        departure: { airport: string; time: string; terminal?: string };
        arrival: { airport: string; time: string; terminal?: string };
        flight: string;
        duration: string;
      }>;
    };
  };
  passengers: Array<{
    id: string;
    type: string;
    name: string;
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
  contact: {
    name: string;
    email: string;
    phone: string;
  };
}

// Mock data for demonstration
const mockBookingData: BookingSuccessData = {
  orderId: "MOCK_BOOKING_ID_1703123456789",
  pnr: "ABC123",
  bookingDate: "2023-12-21T10:30:00Z",
  status: "CONFIRMED",
  flightDetails: {
    outbound: {
      date: "2024-02-01",
      segments: [
        {
          departure: { airport: "SYD", time: "19:15", terminal: "1" },
          arrival: { airport: "SIN", time: "00:30", terminal: "1" },
          flight: "TR13",
          duration: "8h 15m",
        },
        {
          departure: { airport: "SIN", time: "22:05", terminal: "1" },
          arrival: { airport: "DMK", time: "23:30", terminal: "1" },
          flight: "TR868",
          duration: "2h 25m",
        },
      ],
    },
    return: {
      date: "2024-02-05",
      segments: [
        {
          departure: { airport: "DMK", time: "23:15", terminal: "1" },
          arrival: { airport: "SIN", time: "02:50", terminal: "1" },
          flight: "TR867",
          duration: "2h 35m",
        },
        {
          departure: { airport: "SIN", time: "06:55", terminal: "1" },
          arrival: { airport: "SYD", time: "18:15", terminal: "1" },
          flight: "TR12",
          duration: "8h 20m",
        },
      ],
    },
  },
  passengers: [
    { id: "1", type: "Adult", name: "John Smith" },
    { id: "2", type: "Child", name: "Jane Smith" },
  ],
  pricing: {
    total: "546.70",
    currency: "EUR",
    breakdown: [
      { item: "Base Fare", amount: "334.00" },
      { item: "Taxes & Fees", amount: "212.70" },
    ],
  },
  contact: {
    name: "John Smith",
    email: "john.smith@email.com",
    phone: "+1 555-123-4567",
  },
};

export default function BookingSuccessPage({ params }: { params: Promise<{ orderId: string }> }) {
  const router = useRouter();
  const resolvedParams = React.use(params);
  const bookingData = mockBookingData; // In real app, fetch by orderId

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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-green-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold">Booking Confirmed!</h1>
                <p className="text-green-100">Your flight has been successfully booked</p>
              </div>
            </div>
            <Link href="/" className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg transition-colors">
              Book Another Flight
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Booking Summary */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">Booking Summary</h2>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(bookingData.status)}`}>
                  {bookingData.status}
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Booking Reference</h3>
                  <p className="text-lg font-mono font-semibold text-gray-900">{bookingData.orderId}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">PNR (Airline Reference)</h3>
                  <p className="text-lg font-mono font-semibold text-gray-900">{bookingData.pnr}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Booking Date</h3>
                  <p className="text-gray-900">{formatDate(bookingData.bookingDate)}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Total Amount</h3>
                  <p className="text-2xl font-bold text-gray-900">{bookingData.pricing.currency} {bookingData.pricing.total}</p>
                </div>
              </div>
            </div>

            {/* Flight Itinerary */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Flight Itinerary</h2>
              
              {/* Outbound Flight */}
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                  Outbound • {formatDate(bookingData.flightDetails.outbound.date)}
                </h3>
                <div className="space-y-4">
                  {bookingData.flightDetails.outbound.segments.map((segment, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
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
                          <div className="text-sm text-gray-600">
                            Flight {segment.flight}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Return Flight */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                  Return • {formatDate(bookingData.flightDetails.return.date)}
                </h3>
                <div className="space-y-4">
                  {bookingData.flightDetails.return.segments.map((segment, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
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
                          <div className="text-sm text-gray-600">
                            Flight {segment.flight}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Passenger Information */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Passenger Information</h2>
              <div className="space-y-4">
                {bookingData.passengers.map((passenger) => (
                  <div key={passenger.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div>
                      <p className="font-semibold text-gray-900">{passenger.name}</p>
                      <p className="text-sm text-gray-600 capitalize">{passenger.type}</p>
                    </div>
                    {passenger.seat && (
                      <div className="text-right">
                        <p className="text-sm text-gray-500">Seat</p>
                        <p className="font-semibold text-gray-900">{passenger.seat}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Pricing Breakdown */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Pricing Breakdown</h2>
              <div className="space-y-3">
                {bookingData.pricing.breakdown.map((item, index) => (
                  <div key={index} className="flex justify-between">
                    <span className="text-gray-600">{item.item}</span>
                    <span className="text-gray-900">{bookingData.pricing.currency} {item.amount}</span>
                  </div>
                ))}
                <div className="border-t border-gray-200 pt-3">
                  <div className="flex justify-between text-lg font-bold">
                    <span>Total</span>
                    <span>{bookingData.pricing.currency} {bookingData.pricing.total}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Contact Information */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Contact Information</h2>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Primary Contact</p>
                  <p className="font-semibold text-gray-900">{bookingData.contact.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="text-gray-900">{bookingData.contact.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Phone</p>
                  <p className="text-gray-900">{bookingData.contact.phone}</p>
                </div>
              </div>
            </div>

            {/* Important Information */}
            <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-4">Important Information</h3>
              <div className="space-y-3 text-sm text-blue-800">
                <div className="flex items-start gap-2">
                  <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p>Check-in opens 24 hours before departure</p>
                </div>
                <div className="flex items-start gap-2">
                  <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p>Bring valid travel documents and ID</p>
                </div>
                <div className="flex items-start gap-2">
                  <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p>Arrive at airport 2-3 hours before departure</p>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Actions</h3>
              <div className="space-y-3">
                <Link
                  href={`/tickets/processing/${bookingData.orderId}`}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors text-center block"
                >
                  View Ticket Status
                </Link>
                <button
                  onClick={() => window.print()}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                  Print Confirmation
                </button>
                <button
                  onClick={() => {
                    // In real app, this would download a PDF
                    alert('Downloading booking confirmation...');
                  }}
                  className="w-full bg-gray-600 hover:bg-gray-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                  Download PDF
                </button>
                <Link
                  href="/support"
                  className="block w-full bg-gray-100 hover:bg-gray-200 text-gray-800 font-semibold py-2 px-4 rounded-lg transition-colors text-center"
                >
                  Contact Support
                </Link>
              </div>
            </div>

            {/* Ticket Processing Status */}
            <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-yellow-600 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-yellow-900">Tickets Being Processed</h3>
              </div>
              <p className="text-sm text-yellow-800 mb-4">
                Your tickets are currently being processed by our system. This usually takes 5-10 minutes.
              </p>
              <Link
                href={`/tickets/processing/${bookingData.orderId}`}
                className="inline-flex items-center gap-2 text-yellow-800 hover:text-yellow-900 font-medium"
              >
                <span>Track Processing Status</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 