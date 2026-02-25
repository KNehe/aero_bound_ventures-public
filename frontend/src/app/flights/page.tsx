"use client";
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { FaPlane, FaCalendarAlt, FaUsers, FaArrowLeft } from 'react-icons/fa';
import FlightOfferCard from '@/components/FlightOfferCard';
import FlightCardSkeleton from '@/components/FlightCardSkeleton';
import useFlights from '@/store/flights';
import type { FlightOffer } from '@/types/flight_offer';

export default function FlightsPage() {
  const { searchParams } = useFlights();
  const BASE_API_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

  const fetchFlights = async (params: any) => {
    const queryParams = new URLSearchParams(params);
    const url = `${BASE_API_URL}/shopping/flight-offers?${queryParams.toString()}`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error('Failed to fetch flights');
    }
    return response.json();
  };

  const { data: flights, error, isLoading } = useQuery<FlightOffer[]>({
    queryKey: ['flights', searchParams],
    queryFn: () => fetchFlights(searchParams),
    enabled: !!searchParams,
  });

  const formatDisplayDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString([], {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-8 px-6 shadow-lg">
        <div className="max-w-6xl mx-auto">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-blue-100 hover:text-white transition-colors mb-4 text-sm"
          >
            <FaArrowLeft className="w-3 h-3" />
            Back to Search
          </Link>

          {searchParams && (
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h1 className="text-2xl md:text-3xl font-extrabold flex items-center gap-3">
                  <span>{searchParams.originLocationCode}</span>
                  <FaPlane className="w-5 h-5 rotate-90 opacity-70" />
                  <span>{searchParams.destinationLocationCode}</span>
                </h1>
                <div className="flex flex-wrap items-center gap-4 mt-2 text-blue-100 text-sm">
                  <span className="flex items-center gap-1">
                    <FaCalendarAlt className="w-4 h-4" />
                    {formatDisplayDate(searchParams.departureDate)}
                    {searchParams.returnDate && ` — ${formatDisplayDate(searchParams.returnDate)}`}
                  </span>
                  <span className="flex items-center gap-1">
                    <FaUsers className="w-4 h-4" />
                    {searchParams.adults} Adult{parseInt(searchParams.adults) > 1 ? 's' : ''}
                    {searchParams.children && parseInt(searchParams.children) > 0 &&
                      `, ${searchParams.children} Child${parseInt(searchParams.children) > 1 ? 'ren' : ''}`
                    }
                  </span>
                </div>
              </div>

              {!isLoading && flights && flights.length > 0 && (
                <div className="bg-white/20 backdrop-blur-sm rounded-xl px-4 py-2">
                  <span className="text-lg font-bold">{flights.length}</span>
                  <span className="ml-1 text-blue-100">flight{flights.length > 1 ? 's' : ''} found</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {isLoading ? (
          <div className="space-y-4">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-gray-600">Searching for the best flights...</span>
            </div>
            <FlightCardSkeleton />
            <FlightCardSkeleton />
            <FlightCardSkeleton />
          </div>
        ) : error ? (
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h2>
            <p className="text-gray-600 mb-6">{error.message}</p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-xl transition-colors"
            >
              <FaArrowLeft className="w-4 h-4" />
              Try a new search
            </Link>
          </div>
        ) : flights && flights.length > 0 ? (
          <div>
            {flights.map((flight: FlightOffer, index: number) => (
              <FlightOfferCard key={flight.id || index} flight={flight} />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FaPlane className="w-8 h-8 text-blue-500" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">No flights found</h2>
            <p className="text-gray-600 mb-6">
              We couldn't find any flights matching your search criteria.<br />
              Try adjusting your dates or destinations.
            </p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-xl transition-colors"
            >
              <FaArrowLeft className="w-4 h-4" />
              Back to Search
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
