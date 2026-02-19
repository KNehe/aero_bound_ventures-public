"use client";
import { useState } from 'react';
import { FaPlane, FaClock } from 'react-icons/fa';
import { FlightOffer, Segment } from "@/types/flight_offer";
import useFlights from '@/store/flights';
import { useRouter } from 'next/navigation';

export default function FlightOfferCard({ flight }: { flight: FlightOffer }) {
  const { itineraries, price } = flight;
  const outbound = itineraries[0];
  const returnFlight = itineraries.length > 1 ? itineraries[1] : null;
  const selectFlight = useFlights(state => state.selectFlight);
  const router = useRouter();
  const [isNavigating, setIsNavigating] = useState(false);

  const formatTime = (datetime: string) =>
    new Date(datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const formatDate = (datetime: string) =>
    new Date(datetime).toLocaleDateString([], { month: 'short', day: 'numeric' });

  const parseDuration = (duration: string) => {
    const match = duration.match(/PT(\d+H)?(\d+M)?/);
    const hours = match?.[1] ? parseInt(match[1]) : 0;
    const minutes = match?.[2] ? parseInt(match[2]) : 0;
    return `${hours}h ${minutes}m`;
  };

  const calculateTotalDuration = (segments: Segment[]) => {
    const start = new Date(segments[0].departure.at);
    const end = new Date(segments[segments.length - 1].arrival.at);
    const diffMs = end.getTime() - start.getTime();
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
  };

  const getStopsText = (segments: Segment[]) => {
    if (segments.length === 1) return 'Direct';
    const stopCount = segments.length - 1;
    const stopCodes = segments.slice(0, -1).map(s => s.arrival.iataCode);
    return `${stopCount} stop${stopCount > 1 ? 's' : ''} via ${stopCodes.join(', ')}`;
  };

  const onSelectFlight = () => {
    setIsNavigating(true);
    selectFlight(flight);
    router.push(`/flights/${flight.id}/`);
  };

  const renderItinerary = (segments: Segment[], label: string) => {
    const firstSegment = segments[0];
    const lastSegment = segments[segments.length - 1];
    const carrier = firstSegment.carrierCode;
    const totalDuration = calculateTotalDuration(segments);
    const stopsText = getStopsText(segments);

    return (
      <div className="flex items-center gap-6 py-4">
        {/* Airline */}
        <div className="flex flex-col items-center w-16 flex-shrink-0">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg flex items-center justify-center text-white font-bold text-sm shadow-md">
            {carrier}
          </div>
          <span className="text-xs text-gray-500 mt-1">{label}</span>
        </div>

        {/* Departure */}
        <div className="text-center flex-shrink-0">
          <div className="text-2xl font-bold text-gray-900">
            {formatTime(firstSegment.departure.at)}
          </div>
          <div className="text-sm font-semibold text-blue-600">
            {firstSegment.departure.iataCode}
          </div>
          <div className="text-xs text-gray-500">
            {formatDate(firstSegment.departure.at)}
          </div>
        </div>

        {/* Timeline */}
        <div className="flex-1 flex flex-col items-center px-4">
          <div className="text-xs text-gray-500 flex items-center gap-1 mb-1">
            <FaClock className="w-3 h-3" />
            {totalDuration}
          </div>
          <div className="w-full flex items-center">
            <div className="w-2 h-2 rounded-full bg-blue-500"></div>
            <div className="flex-1 border-t-2 border-dashed border-gray-300 relative">
              {segments.length > 1 && (
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                  <FaPlane className="text-blue-500 w-4 h-4 rotate-90" />
                </div>
              )}
            </div>
            <div className="w-2 h-2 rounded-full bg-blue-500"></div>
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {stopsText}
          </div>
        </div>

        {/* Arrival */}
        <div className="text-center flex-shrink-0">
          <div className="text-2xl font-bold text-gray-900">
            {formatTime(lastSegment.arrival.at)}
          </div>
          <div className="text-sm font-semibold text-blue-600">
            {lastSegment.arrival.iataCode}
          </div>
          <div className="text-xs text-gray-500">
            {formatDate(lastSegment.arrival.at)}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden mb-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl border border-gray-100">
      {/* Card Content */}
      <div className="p-6">
        {/* Outbound */}
        {renderItinerary(outbound.segments, 'Depart')}

        {/* Divider for round trip */}
        {returnFlight && (
          <>
            <div className="border-t border-gray-200 my-2"></div>
            {renderItinerary(returnFlight.segments, 'Return')}
          </>
        )}
      </div>

      {/* Footer with price and CTA */}
      <div className="bg-gradient-to-r from-gray-50 to-blue-50 px-6 py-4 flex items-center justify-between border-t border-gray-100">
        <div>
          <div className="text-sm text-gray-500">Total price</div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-blue-600">
              ${parseFloat(price.total).toLocaleString()}
            </span>
            <span className="text-sm text-gray-500">{price.currency}</span>
          </div>
          <div className="text-xs text-gray-500">for all passengers</div>
        </div>

        <button
          onClick={onSelectFlight}
          disabled={isNavigating}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-bold py-3 px-8 rounded-xl transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl flex items-center gap-2"
        >
          {isNavigating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Loading...
            </>
          ) : (
            <>
              Select Flight
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
