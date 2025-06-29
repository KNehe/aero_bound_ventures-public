"use client";
import React from "react";
import TicketProcessingStatus from "../../../../components/TicketProcessingStatus";

export default function TicketProcessingPage({ params }: { params: Promise<{ bookingId: string }> }) {
  const resolvedParams = React.use(params);

  const handleTicketReady = (ticketUrl: string) => {
    // In a real app, you might want to:
    // - Send a notification to the user
    // - Update the booking status in the database
    // - Send an email with the ticket link
    console.log("Ticket ready:", ticketUrl);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center gap-2">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h1 className="text-xl font-semibold text-gray-900">Aero Bound Ventures</h1>
            </div>
            <div className="text-sm text-gray-500">
              Booking ID: {resolvedParams.bookingId}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <TicketProcessingStatus 
        bookingId={resolvedParams.bookingId}
        onTicketReady={handleTicketReady}
      />
    </div>
  );
} 