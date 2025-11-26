"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import useAuth from "@/store/auth";

// Pesapal uses server-side integration
// No global window object needed for iframe approach

interface PesapalPaymentRequest {
  booking_id: string;
  amount: number;
  currency: string;
  description: string;
  callback_url: string;
  notification_id?: string;
  billing_address: {
    email_address: string;
    phone_number: string;
    country_code: string;
    first_name: string;
    last_name: string;
  };
}

interface PesapalPaymentResponse {
  order_tracking_id: string;
  merchant_reference: string;
  redirect_url: string;
  error?: {
    error_type: string;
    code: string;
    message: string;
    details: string;
  };
}


interface BookingSuccessData {
  orderId: string;
  pnr: string;
  bookingDate: string;
  status: "confirmed" | "pending" | "cancelled" | "paid" | "reversed" | "failed" | "refunded";
  ticket_url?: string;
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
    return?: {
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

export default function BookingSuccessPage() {
// Status constants to avoid hardcoded strings (matching backend BookingStatus class)
const BOOKING_STATUS = {
  CONFIRMED: "confirmed",
  PAID: "paid",
  PENDING: "pending",
  CANCELLED: "cancelled",
  REVERSED: "reversed",
  FAILED: "failed",
  REFUNDED: "refunded",
} as const;
  const router = useRouter();
  const [bookingData, setBookingData] = useState<BookingSuccessData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);
  const [showPaymentIframe, setShowPaymentIframe] = useState(false);
  const [paymentUrl, setPaymentUrl] = useState<string | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);
  const { token, logout } = useAuth();
  const params =  useParams();
  const {orderId} = params;

  // Handle hydration
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Handle Pesapal payment
  const handlePayment = async () => {
    if (!bookingData) return;

    try {
      setIsProcessingPayment(true);

      // Use first passenger's information (primary traveler) for Pesapal billing
      const firstPassenger = bookingData.passengers[0];
      const nameParts = firstPassenger?.name.split(' ') || bookingData.contact.name.split(' ');
      const firstName = nameParts[0] || '';
      const lastName = nameParts.slice(1).join(' ') || firstName;

      // Extract country calling code from phone number (format: +256 712345678)
      const phoneMatch = bookingData.contact.phone.match(/^\+?(\d{1,3})\s?(.+)$/);
      const countryCode = phoneMatch ? phoneMatch[1] : '256'; // Default to Uganda
      const phoneNumber = phoneMatch ? phoneMatch[2].replace(/\s/g, '') : bookingData.contact.phone;

      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
      
      // Create payment request on backend
      const response = await fetch(`${baseUrl}/payments/pesapal/initiate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          booking_id: bookingData.orderId,
          amount: parseFloat(bookingData.pricing.total),
          currency: 'USD', 
          description: `Flight booking ${bookingData.pnr}`,
          callback_url: `${window.location.origin}/booking/payment/callback`,
          billing_address: {
            email_address: bookingData.contact.email,
            phone_number: phoneNumber,
            country_code: countryCode,
            first_name: firstName,
            last_name: lastName,
          },
        }),
      });
      console.log("response:", response);

      if(response.status === 401) {
        logout();
        router.push(`/auth/login?redirect=${encodeURIComponent(window.location.pathname)}`);
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Backend error:', errorData);
        throw new Error(errorData.detail || `Failed to initiate payment (${response.status})`);
      }

      const data: PesapalPaymentResponse = await response.json();
      console.log('Payment response:', data);

      if (data.error) {
        throw new Error(data.error.message || 'Payment initiation failed');
      }

      // Show payment iframe instead of redirecting
      setPaymentUrl(data.redirect_url);
      setShowPaymentIframe(true);
    } catch (error) {
      console.error('Payment error:', error);
      alert(error instanceof Error ? error.message : 'Failed to initiate payment. Please try again.');
      setIsProcessingPayment(false);
    }
  };

  useEffect(() => {
    if (!orderId || !isHydrated) return;


    const fetchBookingData = async () => {
      try {
        setLoading(true);
        setError(null);

        const currentPath = `/booking/success/${orderId}`;

        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

        const response = await fetch(
          `${baseUrl}/booking/flight-orders/${orderId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          }
        );

        if (response.status === 401) {
          logout();
          router.push(`/auth/login?redirect=${encodeURIComponent(currentPath)}`);
          return;
        }

        if (!response.ok) {
          throw new Error("Failed to fetch booking details");
        }

        const data = await response.json();
        setBookingData(data);
        console.log("Fetched booking data:", data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchBookingData();
  }, [isHydrated, orderId, token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
          <p className="mt-4 text-gray-600">Loading booking details...</p>
        </div>
      </div>
    );
  }

  if (error || !bookingData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Unable to Load Booking</h2>
          <p className="text-gray-600 mb-4">{error || "Booking not found"}</p>
          <Link href="/" className="inline-block bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg transition-colors">
            Return Home
          </Link>
        </div>
      </div>
    );
  }

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

  // Helper to check if booking is paid (for payment button)
  const isPaid = bookingData.status === BOOKING_STATUS.CONFIRMED || bookingData.status === BOOKING_STATUS.PAID;
  // Helper to check if ticket is available
  const hasTicket = Boolean((bookingData as any).ticket_url);
  // Show processing message only if status is PAID and ticket is not present
  const showProcessingMessage = bookingData.status === BOOKING_STATUS.PAID && !hasTicket;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Payment Iframe Modal */}
      {showPaymentIframe && paymentUrl && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}>
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold text-gray-900">Complete Payment</h3>
              <button
                onClick={() => {
                  setShowPaymentIframe(false);
                  setPaymentUrl(null);
                  setIsProcessingPayment(false);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <iframe
                src={paymentUrl}
                className="w-full h-full border-0"
                title="Pesapal Payment"
                sandbox="allow-same-origin allow-scripts allow-forms allow-top-navigation allow-popups"
              />
            </div>
          </div>
        </div>
      )}

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
                    {bookingData.status.toUpperCase()}
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
              {bookingData.flightDetails.return && (
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
              )}
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
                <div className="border-t border-gray-00 pt-3">
                  <div className="flex justify-between text-lg font-bold text-gray-700">
                    <span>Total</span>
                    <span>{bookingData.pricing.currency} {bookingData.pricing.total}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
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
                {/* Show payment button only if not paid */}
                {!(bookingData.status === BOOKING_STATUS.PAID || bookingData.status === BOOKING_STATUS.CONFIRMED) && (
                  <button
                    onClick={handlePayment}
                    disabled={isProcessingPayment}
                    className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold py-2 px-4 rounded-lg transition-colors text-center"
                  >
                    {isProcessingPayment ? 'Processing...' : 'Pay to Receive Ticket'}
                  </button>
                )}
                {/* Show download button if ticket is available */}
                {isPaid && hasTicket && (
                  <a
                    href={(bookingData as any).ticket_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg text-center transition-colors"
                  >
                    Download Ticket
                  </a>
                )}
                {/* Show processing message only if status is PAID and ticket is not present */}
                {showProcessingMessage && (
                  <button
                    disabled
                    className="w-full bg-yellow-400 text-yellow-900 font-semibold py-2 px-4 rounded-lg text-center cursor-not-allowed"
                  >
                    Ticket is being processed. Please be patient (max 24 hours)
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}