"use client";
import React, { useState, useEffect } from "react";

interface TicketStatus {
  id: string;
  bookingId: string;
  status: "processing" | "ready" | "failed" | "cancelled";
  progress: number;
  estimatedTime: string;
  lastUpdated: string;
  flightDetails: {
    origin: string;
    destination: string;
    departureDate: string;
    returnDate?: string;
    airline: string;
    flightNumber: string;
  };
  passengers: Array<{
    name: string;
    ticketNumber?: string;
  }>;
  ticketUrl?: string;
  errorMessage?: string;
}

interface TicketProcessingStatusProps {
  bookingId: string;
  onTicketReady?: (ticketUrl: string) => void;
}

export default function TicketProcessingStatus({ bookingId, onTicketReady }: TicketProcessingStatusProps) {
  const [ticketStatus, setTicketStatus] = useState<TicketStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Simulate ticket processing status updates
  useEffect(() => {
    const mockTicketStatus: TicketStatus = {
      id: "1",
      bookingId: bookingId,
      status: "processing",
      progress: 45,
      estimatedTime: "5-10 minutes",
      lastUpdated: new Date().toISOString(),
      flightDetails: {
        origin: "SYD",
        destination: "SIN",
        departureDate: "2024-03-15",
        returnDate: "2024-03-22",
        airline: "Singapore Airlines",
        flightNumber: "SQ221",
      },
      passengers: [
        { name: "John Smith" },
        { name: "Jane Smith" },
      ],
    };

    setTicketStatus(mockTicketStatus);
    setIsLoading(false);

    // Simulate progress updates
    const progressInterval = setInterval(() => {
      setTicketStatus(prev => {
        if (!prev) return prev;
        
        const newProgress = Math.min(prev.progress + Math.random() * 15, 100);
        const newStatus = newProgress >= 100 ? "ready" : prev.status;
        
        if (newStatus === "ready") {
          clearInterval(progressInterval);
          // Simulate ticket URL generation
          setTimeout(() => {
            setTicketStatus(prev => prev ? {
              ...prev,
              ticketUrl: `/tickets/${bookingId}.pdf`,
              status: "ready",
              progress: 100
            } : null);
            onTicketReady?.(`/tickets/${bookingId}.pdf`);
          }, 2000);
        }
        
        return {
          ...prev,
          progress: newProgress,
          status: newStatus,
          lastUpdated: new Date().toISOString(),
        };
      });
    }, 3000);

    return () => clearInterval(progressInterval);
  }, [bookingId, onTicketReady]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!ticketStatus) {
    return (
      <div className="text-center p-8">
        <p className="text-gray-600">Unable to load ticket status</p>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "processing":
        return "text-blue-600";
      case "ready":
        return "text-green-600";
      case "failed":
        return "text-red-600";
      case "cancelled":
        return "text-gray-600";
      default:
        return "text-gray-600";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "processing":
        return (
          <svg className="w-6 h-6 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      case "ready":
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case "failed":
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Ticket Processing</h1>
        <p className="text-gray-600">We're preparing your tickets for {ticketStatus.flightDetails.airline}</p>
      </div>

      {/* Status Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`${getStatusColor(ticketStatus.status)}`}>
              {getStatusIcon(ticketStatus.status)}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 capitalize">
                {ticketStatus.status === "processing" ? "Processing Tickets" : 
                 ticketStatus.status === "ready" ? "Tickets Ready" :
                 ticketStatus.status === "failed" ? "Processing Failed" : "Cancelled"}
              </h2>
              <p className="text-sm text-gray-500">
                Booking ID: {ticketStatus.bookingId}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Last updated</p>
            <p className="text-sm font-medium text-gray-900">
              {new Date(ticketStatus.lastUpdated).toLocaleTimeString()}
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        {ticketStatus.status === "processing" && (
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Processing progress</span>
              <span>{Math.round(ticketStatus.progress)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${ticketStatus.progress}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Estimated time remaining: {ticketStatus.estimatedTime}
            </p>
          </div>
        )}

        {/* Flight Details */}
        <div className="border-t border-gray-100 pt-4">
          <h3 className="font-medium text-gray-900 mb-3">Flight Details</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Route</p>
              <p className="font-medium">{ticketStatus.flightDetails.origin} → {ticketStatus.flightDetails.destination}</p>
            </div>
            <div>
              <p className="text-gray-500">Flight</p>
              <p className="font-medium">{ticketStatus.flightDetails.airline} {ticketStatus.flightDetails.flightNumber}</p>
            </div>
            <div>
              <p className="text-gray-500">Departure</p>
              <p className="font-medium">{new Date(ticketStatus.flightDetails.departureDate).toLocaleDateString()}</p>
            </div>
            {ticketStatus.flightDetails.returnDate && (
              <div>
                <p className="text-gray-500">Return</p>
                <p className="font-medium">{new Date(ticketStatus.flightDetails.returnDate).toLocaleDateString()}</p>
              </div>
            )}
          </div>
        </div>

        {/* Passengers */}
        <div className="border-t border-gray-100 pt-4 mt-4">
          <h3 className="font-medium text-gray-900 mb-3">Passengers</h3>
          <div className="space-y-2">
            {ticketStatus.passengers.map((passenger, index) => (
              <div key={index} className="flex justify-between items-center">
                <span className="text-sm text-gray-600">{passenger.name}</span>
                {passenger.ticketNumber && (
                  <span className="text-sm font-medium text-green-600">✓ Ready</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      {ticketStatus.status === "ready" && ticketStatus.ticketUrl && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-green-900 mb-2">Tickets Ready!</h3>
          <p className="text-green-700 mb-4">Your tickets have been processed and are ready for download.</p>
          <div className="flex gap-3 justify-center">
            <a
              href={ticketStatus.ticketUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 font-medium"
            >
              Download Tickets
            </a>
            <button
              onClick={() => window.print()}
              className="bg-white text-green-600 border border-green-600 px-6 py-2 rounded-lg hover:bg-green-50 font-medium"
            >
              Print Tickets
            </button>
          </div>
        </div>
      )}

      {ticketStatus.status === "failed" && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-red-900 mb-2">Processing Failed</h3>
          <p className="text-red-700 mb-4">
            {ticketStatus.errorMessage || "There was an issue processing your tickets. Please contact support."}
          </p>
          <button className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 font-medium">
            Contact Support
          </button>
        </div>
      )}

      {/* Processing Steps */}
      {ticketStatus.status === "processing" && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-medium text-blue-900 mb-4">What's happening now?</h3>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                ticketStatus.progress >= 25 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-400'
              }`}>
                {ticketStatus.progress >= 25 ? '✓' : '1'}
              </div>
              <span className="text-sm text-blue-800">Validating booking information</span>
            </div>
            <div className="flex items-center gap-3">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                ticketStatus.progress >= 50 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-400'
              }`}>
                {ticketStatus.progress >= 50 ? '✓' : '2'}
              </div>
              <span className="text-sm text-blue-800">Generating ticket documents</span>
            </div>
            <div className="flex items-center gap-3">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                ticketStatus.progress >= 75 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-400'
              }`}>
                {ticketStatus.progress >= 75 ? '✓' : '3'}
              </div>
              <span className="text-sm text-blue-800">Applying security features</span>
            </div>
            <div className="flex items-center gap-3">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                ticketStatus.progress >= 100 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-400'
              }`}>
                {ticketStatus.progress >= 100 ? '✓' : '4'}
              </div>
              <span className="text-sm text-blue-800">Preparing for download</span>
            </div>
          </div>
        </div>
      )}

      {/* Support Info */}
      <div className="text-center mt-6">
        <p className="text-sm text-gray-500">
          Need help? Contact our support team at{" "}
          <a href="mailto:support@aeroboundventures.com" className="text-blue-600 hover:underline">
            support@aeroboundventures.com
          </a>
        </p>
      </div>
    </div>
  );
} 