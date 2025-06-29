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
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [bookingData, setBookingData] = useState<Booking>(booking);

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

  const validateFile = (file: File): string | null => {
    // Check file type
    if (file.type !== 'application/pdf') {
      return 'Please select a PDF file';
    }
    
    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      return 'File size must be less than 10MB';
    }
    
    // Check file name
    if (!file.name.toLowerCase().includes('ticket') && !file.name.toLowerCase().includes('booking')) {
      return 'Please select a ticket or booking document';
    }
    
    return null;
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    setUploadError(null);
    
    if (file) {
      const error = validateFile(file);
      if (error) {
        setUploadError(error);
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleUploadTicket = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadProgress(0);
    setUploadError(null);

    try {
      // Simulate file upload with progress
      const uploadSteps = [
        { progress: 20, message: 'Validating file...' },
        { progress: 40, message: 'Processing ticket data...' },
        { progress: 60, message: 'Generating ticket URL...' },
        { progress: 80, message: 'Updating booking status...' },
        { progress: 100, message: 'Upload complete!' }
      ];

      for (const step of uploadSteps) {
        await new Promise(resolve => setTimeout(resolve, 800));
        setUploadProgress(step.progress);
      }

      // Simulate successful upload
      const ticketUrl = `/tickets/${bookingData.bookingId}.pdf`;
      
      // Update booking data
      setBookingData(prev => ({
        ...prev,
        ticketStatus: 'ready' as const,
        ticketUrl: ticketUrl,
        adminNotes: adminNotes + '\n\n[Ticket uploaded successfully - ' + new Date().toLocaleString() + ']'
      }));

      // Update admin notes
      setAdminNotes(prev => prev + '\n\n[Ticket uploaded successfully - ' + new Date().toLocaleString() + ']');

      // Close modal after success
      setTimeout(() => {
        setShowUploadModal(false);
        setSelectedFile(null);
        setIsUploading(false);
        setUploadProgress(0);
      }, 1000);

    } catch (error) {
      setUploadError('Upload failed. Please try again.');
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleSaveNotes = () => {
    // In real app, this would save to database
    alert("Admin notes saved successfully");
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      const error = validateFile(file);
      if (error) {
        setUploadError(error);
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setUploadError(null);
    }
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
                <p className="text-sm text-gray-500">{bookingData.bookingId}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-500">Status:</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(bookingData.status)}`}>
                  {bookingData.status}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-500">Ticket:</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTicketStatusColor(bookingData.ticketStatus)}`}>
                  {bookingData.ticketStatus}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-500">Payment:</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPaymentStatusColor(bookingData.paymentStatus)}`}>
                  {bookingData.paymentStatus}
                </span>
              </div>
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
                  <p className="font-mono font-semibold text-gray-900">{bookingData.bookingId}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">PNR</p>
                  <p className="font-mono font-semibold text-gray-900">{bookingData.pnr}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Booking Date</p>
                  <p className="text-gray-900">{formatDate(bookingData.bookingDate)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Amount</p>
                  <p className="text-lg font-bold text-gray-900">{bookingData.pricing.currency} {bookingData.pricing.total}</p>
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
                      {bookingData.flightDetails.origin} → {bookingData.flightDetails.destination}
                    </h3>
                    <p className="text-gray-600">
                      {bookingData.flightDetails.airline} {bookingData.flightDetails.flightNumber}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">Departure</p>
                    <p className="font-semibold text-gray-900">{formatDate(bookingData.flightDetails.departureDate)}</p>
                  </div>
                </div>

                {bookingData.flightDetails.segments.map((segment, index) => (
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
                {bookingData.passengers.map((passenger) => (
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
            {/* Customer Information */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Customer Information</h2>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Name</p>
                  <p className="font-semibold text-gray-900">
                    {bookingData.user.firstName} {bookingData.user.lastName}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="text-gray-900">{bookingData.user.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Phone</p>
                  <p className="text-gray-900">{bookingData.user.phone}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Address</p>
                  <p className="text-gray-900">
                    {bookingData.user.address.street}<br />
                    {bookingData.user.address.city}, {bookingData.user.address.postalCode}<br />
                    {bookingData.user.address.country}
                  </p>
                </div>
              </div>
            </div>

            {/* Payment Status */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Payment Status</h2>
              <div className="flex items-center justify-between">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPaymentStatusColor(bookingData.paymentStatus)}`}>
                  {bookingData.paymentStatus}
                </span>
                <p className="text-lg font-bold text-gray-900">
                  {bookingData.pricing.currency} {bookingData.pricing.total}
                </p>
              </div>
            </div>

            {/* Ticket Information */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Ticket Information</h2>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500">Ticket Status:</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTicketStatusColor(bookingData.ticketStatus)}`}>
                    {bookingData.ticketStatus}
                  </span>
                </div>
                {bookingData.ticketUrl && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-500">Ticket URL:</span>
                    <a
                      href={bookingData.ticketUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 text-sm underline"
                    >
                      View Ticket
                    </a>
                  </div>
                )}
                {!bookingData.ticketUrl && bookingData.ticketStatus === 'ready' && (
                  <div className="text-sm text-gray-500">
                    Ticket is ready but URL not available
                  </div>
                )}
                {bookingData.ticketStatus === 'processing' && (
                  <div className="text-sm text-blue-600">
                    Ticket is being processed...
                  </div>
                )}
                {bookingData.ticketStatus === 'failed' && (
                  <div className="text-sm text-red-600">
                    Ticket processing failed
                  </div>
                )}
              </div>
            </div>

            {/* Admin Actions */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Admin Actions</h2>
              
              <div className="space-y-3">
                {bookingData.ticketStatus === "processing" && (
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                  >
                    Upload Ticket
                  </button>
                )}
                
                {bookingData.ticketStatus === "ready" && bookingData.ticketUrl && (
                  <a
                    href={bookingData.ticketUrl}
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
                placeholder="Add admin notes here..."
                className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-700"
              />
              <div className="flex gap-3 mt-4">
                <button
                  onClick={handleSaveNotes}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Save Notes
                </button>
                <button
                  onClick={() => setAdminNotes(bookingData.adminNotes || "")}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 transition-colors"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Ticket Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Upload Ticket
                </h3>
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                  disabled={isUploading}
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                {/* File Upload Area */}
                <div
                  className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                    selectedFile
                      ? 'border-green-300 bg-green-50'
                      : 'border-gray-300 hover:border-blue-400'
                  }`}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                >
                  {selectedFile ? (
                    <div className="space-y-2">
                      <div className="flex items-center justify-center">
                        <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                      <p className="text-xs text-gray-500">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="text-sm text-red-600 hover:text-red-800"
                        disabled={isUploading}
                      >
                        Remove file
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <div className="text-sm text-gray-600">
                        <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                          <span>Upload a file</span>
                          <input
                            id="file-upload"
                            name="file-upload"
                            type="file"
                            className="sr-only"
                            accept=".pdf"
                            onChange={handleFileUpload}
                            disabled={isUploading}
                          />
                        </label>
                        <p className="pl-1">or drag and drop</p>
                      </div>
                      <p className="text-xs text-gray-500">PDF up to 10MB</p>
                    </div>
                  )}
                </div>

                {/* Error Message */}
                {uploadError && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-3">
                    <div className="flex">
                      <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                      <p className="ml-2 text-sm text-red-700">{uploadError}</p>
                    </div>
                  </div>
                )}

                {/* Upload Progress */}
                {isUploading && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>Uploading...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {/* Upload Button */}
                <button
                  onClick={handleUploadTicket}
                  disabled={!selectedFile || isUploading}
                  className={`w-full py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    !selectedFile || isUploading
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
                  }`}
                >
                  {isUploading ? (
                    <div className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Uploading...
                    </div>
                  ) : (
                    'Upload Ticket'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 