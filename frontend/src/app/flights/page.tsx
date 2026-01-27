"use client";
import React, { useEffect } from 'react';
import FlightOfferCard from '@/components/FlightOfferCard';
import FlightCardSkeleton from '@/components/FlightCardSkeleton';
import useFlights from '@/store/flights';
import type { FlightOffer } from '@/types/flight-booking';

export default function FlightsPage() {
  const {
    flights,
    isLoading,
    error,
    searchParams,
    updateFlights,
    setError
  } = useFlights();

  useEffect(() => {
    const fetchFlights = async () => {
      if (!searchParams || !isLoading) return;

      const BASE_API_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

      try {
        const queryParams = new URLSearchParams(searchParams);
        const url = `${BASE_API_URL}/shopping/flight-offers?${queryParams.toString()}`;

        const response = await fetch(url);

        if (!response.ok) {
          throw new Error('Failed to fetch flights');
        }

        const data = await response.json();
        updateFlights(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred while fetching flights');
      }
    };

    fetchFlights();
  }, [searchParams, isLoading, updateFlights, setError]);

  return (
    <div className="container mx-auto p-4 min-h-screen">
      <h1 className="text-2xl font-bold mb-6">Flight Search Results</h1>

      {isLoading ? (
        <div>
          <FlightCardSkeleton />
          <FlightCardSkeleton />
          <FlightCardSkeleton />
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      ) : flights && flights.length > 0 ? (
        <div>
          {flights.map((flight: FlightOffer, index: number) => (
            <FlightOfferCard key={flight.id || index} flight={flight} />
          ))}
        </div>
      ) : (
        <div className="text-center py-10">
          <p className="text-gray-500 text-lg">No flights found for your search criteria.</p>
          <p className="text-gray-400">Try adjusting your dates or destinations.</p>
        </div>
      )}
    </div>
  );
}

