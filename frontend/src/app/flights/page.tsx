"use client";

import FlightOfferCard from '@/components/FlightOfferCard';
import useFlights from '@/store/flights';

export default function FlightsPage() {
  const flights = useFlights((state) => state.flights)

  console.log("Flights in store:", flights);


  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Flight Search Results</h1>
      {flights && flights.length > 0 ? (
        <div>
          {flights.map((flight: unknown) => (
            <FlightOfferCard flight={flight} />
          ))}
        </div>
      ) : (
         <p>No flights found.</p>
      )}
    </div>
  );
}