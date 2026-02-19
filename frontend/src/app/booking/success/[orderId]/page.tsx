"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import useAuth from "@/store/auth";
import { apiClient, isUnauthorizedError, ApiClientError } from "@/lib/api";
import SeatMap from "@/components/SeatMap";

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
  const [showSeatMap, setShowSeatMap] = useState(false);
  const [seatMapData, setSeatMapData] = useState<any>(null);
  const [isSeatMapLoading, setIsSeatMapLoading] = useState(false);
  const [selectedSeats, setSelectedSeats] = useState<Record<string, string>>({});
  const { logout, isAuthenticated } = useAuth();
  const params = useParams();
  const { orderId } = params;
  const [isDownloading, setIsDownloading] = useState(false);
  const [isViewingTicket, setIsViewingTicket] = useState(false);

  const handleDownloadTicket = async () => {
    const ticketUrl = (bookingData as any)?.ticket_url;
    if (!ticketUrl) return;

    setIsDownloading(true);
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
      link.download = `ticket-${orderId}.${extension}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading ticket:', error);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleViewTicket = () => {
    const ticketUrl = (bookingData as any)?.ticket_url;
    if (!ticketUrl) return;
    setIsViewingTicket(true);
    window.open(ticketUrl, '_blank');
    setTimeout(() => setIsViewingTicket(false), 1000);
  };

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

      // Create payment request on backend using apiClient
      const data = await apiClient.post<PesapalPaymentResponse>('/payments/pesapal/initiate', {
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
      });

      console.log('Payment response:', data);

      if (data.error) {
        throw new Error(data.error.message || 'Payment initiation failed');
      }

      // Show payment iframe instead of redirecting
      setPaymentUrl(data.redirect_url);
      setShowPaymentIframe(true);
    } catch (error) {
      console.error('Payment error:', error);
      if (isUnauthorizedError(error)) {
        await logout();
        router.push(`/auth/login?redirect=${encodeURIComponent(window.location.pathname)}`);
        return;
      }
      if (error instanceof ApiClientError) {
        alert(error.detail || 'Failed to initiate payment');
      } else {
        alert(error instanceof Error ? error.message : 'Failed to initiate payment. Please try again.');
      }
      setIsProcessingPayment(false);
    }
  };

  const fetchSeatMap = async () => {
    setIsSeatMapLoading(true);
    try {
      // For success page, we might need the original flight offer or use orderId
      // The backend view_seat_map_get uses flightOrderId
      const response = await apiClient.get<any>(`/shopping/seatmaps?flightorderId=${orderId}`);
      console.log("Success Page Seat Map Raw Response:", response);

      // Handle various potential response structures gracefully
      let data = null;
      if (Array.isArray(response)) {
        data = response[0];
      } else if (response && response.data) {
        data = Array.isArray(response.data) ? response.data[0] : response.data;
      } else {
        data = response;
      }

      setSeatMapData(data);
    } catch (error) {
      console.error("Error fetching seat map:", error);
    } finally {
      setIsSeatMapLoading(false);
    }
  };

  const handleOpenSeatMap = () => {
    setShowSeatMap(true);
    if (!seatMapData) {
      fetchSeatMap();
    }
  };

  const handleSelectSeat = (_travelerId: string, _seatNumber: string, _price?: any) => {
    // Read-only: seat selection is disabled on the success page
  };


  useEffect(() => {
    if (!orderId || !isHydrated) return;


    const fetchBookingData = async () => {
      try {
        setLoading(true);
        setError(null);

        const currentPath = `/booking/success/${orderId}`;

        const data = await apiClient.get<BookingSuccessData>(`/booking/flight-orders/${orderId}`);
        setBookingData(data);

        // Initialize selected seats from passenger data
        const initialSeats: Record<string, string> = {};
        data.passengers.forEach(p => {
          if (p.seat) initialSeats[p.id] = p.seat;
        });
        setSelectedSeats(initialSeats);

        console.log("Fetched booking data:", data);

      } catch (err) {
        if (isUnauthorizedError(err)) {
          await logout();
          router.push(`/auth/login?redirect=${encodeURIComponent(`/booking/success/${orderId}`)}`);
          return;
        }
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchBookingData();
  }, [isHydrated, orderId, logout, router]);

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
  const isPaid = bookingData.status === BOOKING_STATUS.PAID;
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
      <div className="bg-gradient-to-br from-green-600 via-green-700 to-emerald-800 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDEzNGgtMnYtMmgydjJ6bTAgMTBoLTJ2LTJoMnYyem0wIDEwaC0ydi0yaDJ2MnptMCAxMGgtMnYtMmgydjJ6bTAtNTBoLTJ2LTJoMnYyem0wLTEwaC0ydi0yaDJ2MnptMC0xMGgtMnYtMmgydjJ6bS0xMCAwaDJ2Mmgtdi0yem0tMTAgMGgydjJoLTJ2LTJ6bS0xMCAwaDJ2Mmgtdi0yem0tMTAgMGgydjJoLTJ2LTJ6bS0xMCAwaDJ2Mmgtdi0yem0tMTAgMGgydjJoLTJ2LTJ6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-30"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between py-8 gap-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center shadow-lg">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl md:text-4xl font-bold mb-1">Booking Confirmed!</h1>
                <p className="text-green-100 text-sm md:text-base">Your flight has been successfully booked</p>
              </div>
            </div>
            <Link href="/" className="inline-flex items-center gap-2 bg-white text-green-700 hover:bg-green-50 px-5 py-2.5 rounded-lg transition-all shadow-md hover:shadow-lg font-semibold">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              Book Another Flight
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Booking Summary */}
            <div className="bg-gradient-to-br from-white to-gray-50 rounded-xl shadow-lg border border-gray-200 p-6 md:p-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">Booking Summary</h2>
                </div>
                <span className={`px-4 py-1.5 rounded-full text-sm font-semibold shadow-sm ${getStatusColor(bookingData.status)}`}>
                  {bookingData.status.toUpperCase()}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Booking Reference</h3>
                  <p className="text-base font-mono font-bold text-gray-900 break-all">{bookingData.orderId}</p>
                </div>
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">PNR (Airline Reference)</h3>
                  <p className="text-base font-mono font-bold text-gray-900">{bookingData.pnr}</p>
                </div>
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Booking Date</h3>
                  <p className="text-base font-semibold text-gray-900">{formatDate(bookingData.bookingDate)}</p>
                </div>
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-lg border-2 border-green-200">
                  <h3 className="text-xs font-semibold text-green-700 uppercase tracking-wider mb-2">Total Amount</h3>
                  <p className="text-2xl font-bold text-green-700">{bookingData.pricing.currency} {bookingData.pricing.total}</p>
                </div>
              </div>
            </div>

            {/* Flight Itinerary */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 md:p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-indigo-100 rounded-lg">
                  <svg className="w-6 h-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-900">Flight Itinerary</h2>
              </div>

              {/* Outbound Flight */}
              <div className="mb-8">
                <div className="flex items-center gap-2 mb-4">
                  <span className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                    Outbound
                  </span>
                  <span className="text-base font-semibold text-gray-700">{formatDate(bookingData.flightDetails.outbound.date)}</span>
                </div>
                <div className="space-y-4">
                  {bookingData.flightDetails.outbound.segments.map((segment, index) => (
                    <div key={index} className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl p-5 hover:shadow-md transition-shadow">
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
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 md:p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <svg className="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-900">Passengers</h2>
              </div>
              <div className="space-y-3">
                {bookingData.passengers.map((passenger) => (
                  <div key={passenger.id} className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
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
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 md:p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-green-100 rounded-lg">
                  <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-900">Pricing Breakdown</h2>
              </div>
              <div className="space-y-3">
                {bookingData.pricing.breakdown.map((item, index) => (
                  <div key={index} className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-gray-600 font-medium">{item.item}</span>
                    <span className="text-gray-900 font-semibold">{bookingData.pricing.currency} {item.amount}</span>
                  </div>
                ))}
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4 mt-4">
                  <div className="flex justify-between text-xl font-bold text-green-700">
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
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border-2 border-blue-200 p-6 shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <div className="p-1.5 bg-blue-100 rounded-lg">
                  <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-blue-900">Important Info</h3>
              </div>
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
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="p-1.5 bg-indigo-100 rounded-lg">
                  <svg className="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-gray-900">Quick Actions</h3>
              </div>
              <div className="space-y-3">
                {/* Show cancelled message if booking is cancelled */}
                {bookingData.status === BOOKING_STATUS.CANCELLED && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="font-semibold text-red-800">Booking Cancelled</span>
                    </div>
                    <p className="text-sm text-red-700">
                      This booking has been cancelled. If you paid for this booking, a refund will be processed within 5-7 business days.
                    </p>
                    <a
                      href="/"
                      className="mt-3 inline-block w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg text-center transition-colors"
                    >
                      Book a New Flight
                    </a>
                  </div>
                )}
                {/* Show payment button if booking is confirmed but not yet paid */}
                {bookingData.status === BOOKING_STATUS.CONFIRMED && (
                  <button
                    onClick={handlePayment}
                    disabled={isProcessingPayment}
                    className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold py-2 px-4 rounded-lg transition-colors text-center"
                  >
                    {isProcessingPayment ? 'Processing...' : 'Pay Now'}
                  </button>
                )}
                {/* Show download button if ticket is available */}
                {isPaid && hasTicket && (
                  <div className="w-full flex gap-2">
                    <button
                      onClick={handleViewTicket}
                      disabled={isViewingTicket}
                      className="flex-1 bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white font-semibold py-2 px-4 rounded-lg text-center transition-colors"
                    >
                      {isViewingTicket ? (
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Opening...
                        </div>
                      ) : (
                        "View Ticket"
                      )}
                    </button>
                    <button
                      onClick={handleDownloadTicket}
                      disabled={isDownloading}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold py-2 px-4 rounded-lg text-center transition-colors"
                    >
                      {isDownloading ? (
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Downloading...
                        </div>
                      ) : (
                        "Download Ticket"
                      )}
                    </button>
                  </div>
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
                <button
                  onClick={handleOpenSeatMap}
                  disabled={isSeatMapLoading}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-semibold py-2 px-4 rounded-lg transition-colors text-center"
                >
                  {isSeatMapLoading ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Loading Seat Map...
                    </div>
                  ) : (
                    "View Seat Map"
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Seat Map Modal */}
      {showSeatMap && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden">

            <div className="flex items-center justify-between p-6 border-b">
              <div>
                <h3 className="text-xl font-bold text-gray-900">Aircraft Seat Map</h3>
                <p className="text-sm text-gray-500">View your seat assignments • Visit airline website to make changes</p>
              </div>
              <button
                onClick={() => setShowSeatMap(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <svg className="w-6 h-6 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {isSeatMapLoading ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                  <p className="text-gray-500 font-medium">Loading cabin layout...</p>
                </div>
              ) : seatMapData ? (
                <div className="flex flex-col items-center">
                  <div className="w-full mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-3">
                    <svg className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm text-amber-800">
                      This is a <strong>view-only</strong> seat map showing your booked seat assignment. To change your seat, please visit the airline&apos;s website or contact them directly.
                    </p>
                  </div>
                  <SeatMap
                    seatMapData={seatMapData}
                    onSelectSeat={handleSelectSeat}
                    selectedSeats={selectedSeats}
                    travelerId={bookingData.passengers[0].id}
                    readOnly
                  />
                </div>

              ) : (
                <div className="bg-red-50 p-8 rounded-xl border border-red-100 text-center">
                  <p className="text-red-700 font-bold mb-2">Seat Map Unavailable</p>
                  <p className="text-sm text-red-600">The airline hasn't provided a seat map for this booking yet.</p>
                </div>
              )}
            </div>

            <div className="p-6 border-t bg-gray-50 flex justify-end">
              <button
                onClick={() => setShowSeatMap(false)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 px-8 rounded-xl transition-all shadow-md hover:shadow-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}