"use client";
import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import useAuth from "@/store/auth";
import { Booking, TicketUploadResponse } from "@/types/admin";
import { apiClient, isUnauthorizedError, ApiClientError } from "@/lib/api";

export default function BookingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { logout, isAuthenticated } = useAuth();
  const bookingId = params.bookingId as string;

  const [booking, setBooking] = useState<Booking | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isViewingTicket, setIsViewingTicket] = useState(false);

  const handleDownloadTicket = async () => {
    if (!booking?.ticket_url) return;

    setIsDownloading(true);
    try {
      const response = await fetch(booking.ticket_url);
      const blob = await response.blob();

      // Detect file extension from content type or URL
      let extension = 'pdf';
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('image/jpeg') || contentType?.includes('image/jpg')) {
        extension = 'jpg';
      } else if (contentType?.includes('image/png')) {
        extension = 'png';
      } else if (booking.ticket_url.match(/\.(jpg|jpeg|png|pdf)$/i)) {
        extension = booking.ticket_url.match(/\.(jpg|jpeg|png|pdf)$/i)![1].toLowerCase();
      }

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ticket-${booking.id}.${extension}`;
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
    if (!booking?.ticket_url) return;
    setIsViewingTicket(true);
    window.open(booking.ticket_url, '_blank');
    setTimeout(() => setIsViewingTicket(false), 1000);
  };

  useEffect(() => {
    const fetchBooking = async () => {
      try {
        setIsLoading(true);
        const bookingData = await apiClient.get<Booking>(`/admin/bookings/${bookingId}`);
        setBooking(bookingData);
      } catch (err) {
        if (isUnauthorizedError(err)) {
          await logout();
          router.push(`/auth/login?redirect=/admin/bookings/${bookingId}`);
          return;
        }
        if (err instanceof ApiClientError && err.status === 404) {
          setError("Booking not found");
        } else {
          setError(err instanceof Error ? err.message : "Failed to load booking");
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchBooking();
  }, [bookingId, logout, router]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type (PDF or images)
      const validTypes = ["application/pdf", "image/jpeg", "image/jpg", "image/png"];
      if (!validTypes.includes(file.type)) {
        setUploadError("Please select a PDF or image file (JPG, PNG)");
        setSelectedFile(null);
        return;
      }
      // Validate file size (max 2MB)
      if (file.size > 2 * 1024 * 1024) {
        setUploadError("File size must be less than 2MB");
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setUploadError(null);
      setUploadSuccess(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile || !isAuthenticated) {
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(false);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const result = await apiClient.upload<TicketUploadResponse>(`/tickets/upload/${bookingId}`, formData);

      // Update booking with new ticket URL
      setBooking((prev) =>
        prev ? { ...prev, ticket_url: result.ticket_url } : null
      );
      setUploadSuccess(true);
      setSelectedFile(null);

      // Reset file input
      const fileInput = document.getElementById("ticket-file") as HTMLInputElement;
      if (fileInput) {
        fileInput.value = "";
      }
    } catch (err) {
      if (isUnauthorizedError(err)) {
        await logout();
        router.push(`/auth/login?redirect=/admin/bookings/${bookingId}`);
        return;
      }
      if (err instanceof ApiClientError) {
        setUploadError(err.detail || "Upload failed");
      } else {
        setUploadError(err instanceof Error ? err.message : "Upload failed");
      }
    } finally {
      setIsUploading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600 font-medium">Loading booking details...</p>
        </div>
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex items-center justify-center py-8 px-4">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
          <div className="text-center">
            <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-red-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
            <p className="text-gray-600 mb-6">{error || "Booking not found"}</p>
            <button
              onClick={() => router.push("/admin")}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  const pnr =
    booking.amadeus_order_response?.associatedRecords?.[0]?.reference || "N/A";
  const travelers =
    booking.amadeus_order_response?.travelers?.map((t) => ({
      name: `${t.name?.firstName || ""} ${t.name?.lastName || ""}`.trim(),
      type: t.travelerType,
    })) || [];

  // Extract flight itinerary details
  const flightOffers = booking.amadeus_order_response?.flightOffers || [];
  const itineraries = flightOffers[0]?.itineraries || [];

  const formatTime = (dateTimeString?: string) => {
    if (!dateTimeString) return 'N/A';
    return new Date(dateTimeString).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  };

  const formatDate = (dateTimeString?: string) => {
    if (!dateTimeString) return 'N/A';
    return new Date(dateTimeString).toLocaleDateString("en-US", {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => router.push("/admin")}
            className="text-blue-600 hover:text-blue-800 flex items-center gap-2 mb-4"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Booking Details</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Booking Info Card */}
            <div className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-gray-900">
                  Booking Information
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Booking ID</p>
                  <p className="font-medium text-gray-900 break-all">{booking.id}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Order ID</p>
                  <p className="font-medium text-gray-900 break-all">
                    {booking.flight_order_id}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">PNR</p>
                  <p className="font-medium text-gray-900">{pnr}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${booking.status === "confirmed" || booking.status === "paid"
                      ? "bg-green-100 text-green-800"
                      : booking.status === "pending"
                        ? "bg-yellow-100 text-yellow-800"
                        : "bg-red-100 text-red-800"
                      }`}
                  >
                    {booking.status.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Customer Email</p>
                  <p className="font-medium text-gray-900 break-all">{booking.user.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Created At</p>
                  <p className="font-medium text-gray-900">
                    {new Date(booking.created_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Price</p>
                  <p className="font-medium text-gray-900">
                    {flightOffers[0]?.price?.grandTotal || flightOffers[0]?.price?.total
                      ? `${flightOffers[0]?.price?.currency || 'USD'} ${flightOffers[0]?.price?.grandTotal || flightOffers[0]?.price?.total}`
                      : booking.total_amount
                        ? `$${booking.total_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                        : 'N/A'}
                  </p>
                </div>
              </div>

              {travelers.length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm text-gray-500 mb-2">Travelers</p>
                  <ul className="space-y-1">
                    {travelers.map((traveler, idx: number) => (
                      <li key={idx} className="text-sm text-gray-900">
                        {traveler.name} ({traveler.type})
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Ticket Status Card */}
            <div className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-gray-900">
                  Ticket Status
                </h2>
              </div>
              {booking.ticket_url ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-green-600">
                    <svg
                      className="w-6 h-6"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <span className="font-medium">Ticket Uploaded</span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleViewTicket}
                      disabled={isViewingTicket}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-60 transition-colors"
                    >
                      {isViewingTicket ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Opening...
                        </>
                      ) : (
                        <>
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                            />
                          </svg>
                          View Ticket
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleDownloadTicket}
                      disabled={isDownloading}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-60 transition-colors"
                    >
                      {isDownloading ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Downloading...
                        </>
                      ) : (
                        <>
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                            />
                          </svg>
                          Download Ticket
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-amber-600">
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span className="font-medium">No ticket uploaded</span>
                </div>
              )}
            </div>

            {/* Flight Itinerary Card */}
            {itineraries.length > 0 && (
              <div className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </div>
                  <h2 className="text-xl font-bold text-gray-900">
                    Flight Itinerary
                  </h2>
                </div>

                <div className="space-y-6">
                  {itineraries.map((itinerary, itinIndex: number) => (
                    <div key={itinIndex}>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-800 rounded-full text-sm font-semibold">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                          </svg>
                          {itinIndex === 0 ? "Outbound" : "Return"}
                        </span>
                        <span className="text-sm font-medium text-gray-600">
                          Duration: {itinerary.duration?.replace("PT", "").replace("H", "h ").replace("M", "m")}
                        </span>
                      </div>

                      <div className="space-y-4">
                        {itinerary.segments?.map((segment, segIndex: number) => (
                          <div key={segIndex} className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-4">
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex-1">
                                <div className="text-lg font-bold text-gray-900">
                                  {formatTime(segment.departure.at)}
                                </div>
                                <div className="text-sm font-medium text-gray-700">
                                  {segment.departure.iataCode}
                                </div>
                                <div className="text-xs text-gray-600">
                                  {formatDate(segment.departure.at)}
                                </div>
                              </div>

                              <div className="flex-1 mx-4 flex flex-col items-center">
                                <div className="flex items-center w-full">
                                  <div className="flex-1 h-px bg-blue-300"></div>
                                  <svg className="w-5 h-5 text-blue-600 mx-2" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                                  </svg>
                                  <div className="flex-1 h-px bg-blue-300"></div>
                                </div>
                                <div className="text-xs text-gray-600 mt-1">
                                  {segment.duration?.replace("PT", "").replace("H", "h ").replace("M", "m")}
                                </div>
                              </div>

                              <div className="flex-1 text-right">
                                <div className="text-lg font-bold text-gray-900">
                                  {formatTime(segment.arrival.at)}
                                </div>
                                <div className="text-sm font-medium text-gray-700">
                                  {segment.arrival.iataCode}
                                </div>
                                <div className="text-xs text-gray-600">
                                  {formatDate(segment.arrival.at)}
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center justify-between pt-3 border-t border-blue-200">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-gray-700">
                                  {segment.carrierCode} {segment.number}
                                </span>
                                <span className="text-xs text-gray-500">•</span>
                                <span className="text-sm text-gray-600">
                                  {segment.aircraft?.code || "N/A"}
                                </span>
                              </div>
                              <div className="text-sm text-gray-600">
                                {segment.numberOfStops === 0 ? "Direct" : `${segment.numberOfStops} stop(s)`}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {itinIndex < itineraries.length - 1 && (
                        <div className="my-4 border-t border-gray-300"></div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Upload Ticket Card */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg shadow-md border border-blue-100 overflow-hidden">
            <div className="bg-white border-b border-blue-100 px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <svg
                    className="w-6 h-6 text-blue-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    Upload Ticket
                  </h2>
                  <p className="text-sm text-gray-600">
                    Upload the flight ticket for this booking
                  </p>
                </div>
              </div>
            </div>

            <div className="p-6">
              {booking.ticket_url && !uploadSuccess && (
                <div className="mb-4 p-4 bg-blue-50 border-l-4 border-blue-500 rounded-r-md shadow-sm">
                  <div className="flex items-start gap-3">
                    <svg
                      className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <div>
                      <p className="font-semibold text-blue-800">Ticket Already Uploaded</p>
                      <p className="text-sm text-blue-700">
                        A ticket has already been uploaded for this booking. You can replace it by uploading a new file.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {uploadSuccess && (
                <div className="mb-4 p-4 bg-green-50 border-l-4 border-green-500 rounded-r-md shadow-sm">
                  <div className="flex items-start gap-3">
                    <svg
                      className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <div>
                      <p className="font-semibold text-green-800">Success!</p>
                      <p className="text-sm text-green-700">
                        Ticket uploaded successfully and is now available for download.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {uploadError && (
                <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-500 rounded-r-md shadow-sm">
                  <div className="flex items-start gap-3">
                    <svg
                      className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <div>
                      <p className="font-semibold text-red-800">Upload Failed</p>
                      <p className="text-sm text-red-700">{uploadError}</p>
                    </div>
                  </div>
                </div>
              )}

              <form onSubmit={handleUpload} className="space-y-5">
                <div>
                  <label
                    htmlFor="ticket-file"
                    className="block text-sm font-semibold text-gray-700 mb-3"
                  >
                    Choose File
                  </label>

                  {/* Custom File Upload Area */}
                  <div className="relative">
                    <input
                      type="file"
                      id="ticket-file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={handleFileChange}
                      disabled={isUploading}
                      className="hidden"
                    />
                    <label
                      htmlFor="ticket-file"
                      className={`flex flex-col items-center justify-center w-full h-40 border-2 border-dashed rounded-lg cursor-pointer transition-all ${isUploading
                        ? "border-gray-300 bg-gray-50 cursor-not-allowed"
                        : selectedFile
                          ? "border-green-400 bg-green-50 hover:bg-green-100"
                          : "border-blue-300 bg-white hover:bg-blue-50 hover:border-blue-400"
                        }`}
                    >
                      {selectedFile ? (
                        <div className="flex flex-col items-center text-center p-4">
                          <svg
                            className="w-12 h-12 text-green-500 mb-3"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          <p className="text-sm font-semibold text-gray-700 mb-1">
                            {selectedFile.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {(selectedFile.size / 1024).toFixed(2)} KB
                          </p>
                          <p className="text-xs text-blue-600 mt-2">
                            Click to change file
                          </p>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center text-center p-4">
                          <svg
                            className="w-12 h-12 text-blue-400 mb-3"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                            />
                          </svg>
                          <p className="text-sm font-semibold text-gray-700 mb-1">
                            Click to upload or drag and drop
                          </p>
                          <p className="text-xs text-gray-500">
                            PDF, JPG, or PNG (max 2MB)
                          </p>
                        </div>
                      )}
                    </label>
                  </div>

                  <div className="mt-3 flex items-start gap-2 text-xs text-gray-600 bg-blue-50 p-3 rounded-md">
                    <svg
                      className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <div>
                      <p className="font-medium text-blue-900 mb-1">File Requirements:</p>
                      <ul className="list-disc list-inside space-y-0.5 text-blue-800">
                        <li>Accepted formats: PDF, JPG, JPEG, PNG</li>
                        <li>Maximum file size: 2MB</li>
                        <li>Ensure the ticket is clear and readable</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={!selectedFile || isUploading}
                  className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-md hover:shadow-lg disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed disabled:shadow-none flex items-center justify-center gap-2"
                >
                  {isUploading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                      <span>Uploading...</span>
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                        />
                      </svg>
                      <span>Upload Ticket</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
