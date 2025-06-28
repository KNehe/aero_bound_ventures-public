"use client";
import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";

// Mock data structure based on the API response
interface FlightOffer {
  id: string;
  itineraries: Array<{
    duration: string;
    segments: Array<{
      departure: {
        iataCode: string;
        terminal?: string;
        at: string;
      };
      arrival: {
        iataCode: string;
        terminal?: string;
        at: string;
      };
      carrierCode: string;
      number: string;
      duration: string;
      numberOfStops: number;
    }>;
  }>;
  price: {
    currency: string;
    total: string;
  };
  numberOfBookableSeats: number;
  validatingAirlineCodes: string[];
}

// Mock data for demonstration
const mockFlightData = {
  meta: { count: 2 },
  data: [
    {
      id: "1",
      itineraries: [
        {
          duration: "PT14H15M",
          segments: [
            {
              departure: { iataCode: "SYD", terminal: "1", at: "2021-11-01T11:35:00" },
              arrival: { iataCode: "MNL", terminal: "2", at: "2021-11-01T16:50:00" },
              carrierCode: "PR",
              number: "212",
              duration: "PT8H15M",
              numberOfStops: 0,
            },
            {
              departure: { iataCode: "MNL", terminal: "1", at: "2021-11-01T19:20:00" },
              arrival: { iataCode: "BKK", at: "2021-11-01T21:50:00" },
              carrierCode: "PR",
              number: "732",
              duration: "PT3H30M",
              numberOfStops: 0,
            },
          ],
        },
      ],
      price: { currency: "EUR", total: "355.34" },
      numberOfBookableSeats: 9,
      validatingAirlineCodes: ["PR"],
    },
    {
      id: "2",
      itineraries: [
        {
          duration: "PT16H35M",
          segments: [
            {
              departure: { iataCode: "SYD", terminal: "1", at: "2021-11-01T11:35:00" },
              arrival: { iataCode: "MNL", terminal: "2", at: "2021-11-01T16:50:00" },
              carrierCode: "PR",
              number: "212",
              duration: "PT8H15M",
              numberOfStops: 0,
            },
            {
              departure: { iataCode: "MNL", terminal: "1", at: "2021-11-01T21:40:00" },
              arrival: { iataCode: "BKK", at: "2021-11-02T00:10:00" },
              carrierCode: "PR",
              number: "740",
              duration: "PT3H30M",
              numberOfStops: 0,
            },
          ],
        },
      ],
      price: { currency: "EUR", total: "355.34" },
      numberOfBookableSeats: 9,
      validatingAirlineCodes: ["PR"],
    },
  ],
  dictionaries: {
    carriers: { PR: "PHILIPPINE AIRLINES" },
    aircraft: { "320": "AIRBUS A320", "321": "AIRBUS A321", "333": "AIRBUS A330-300" },
  },
};

export default function FlightsPage() {
  const [selectedFlight, setSelectedFlight] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"price" | "duration" | "departure">("price");

  const formatDuration = (duration: string) => {
    const match = duration.match(/PT(\d+)H(\d+)M/);
    if (match) {
      const hours = parseInt(match[1]);
      const minutes = parseInt(match[2]);
      return `${hours}h ${minutes}m`;
    }
    return duration;
  };

  const formatTime = (dateTime: string) => {
    return new Date(dateTime).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  };

  const formatDate = (dateTime: string) => {
    return new Date(dateTime).toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  };

  const sortedFlights = [...mockFlightData.data].sort((a, b) => {
    switch (sortBy) {
      case "price":
        return parseFloat(a.price.total) - parseFloat(b.price.total);
      case "duration":
        return a.itineraries[0].duration.localeCompare(b.itineraries[0].duration);
      case "departure":
        return a.itineraries[0].segments[0].departure.at.localeCompare(
          b.itineraries[0].segments[0].departure.at
        );
      default:
        return 0;
    }
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span className="font-semibold">Back to Search</span>
            </Link>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3 bg-white/10 rounded-lg px-4 py-2">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-lg">SYD</span>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                  <span className="font-bold text-lg">BKK</span>
                </div>
                <div className="w-px h-6 bg-white/30"></div>
                <div className="text-sm opacity-90">
                  Nov 1, 2021
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Results Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Flight Results
          </h1>
          <p className="text-gray-600">
            Found {mockFlightData.meta.count} flights from Sydney to Bangkok
          </p>
        </div>

        {/* Filters and Sort */}
        <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-gray-700">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 font-medium"
              >
                <option value="price">Price</option>
                <option value="duration">Duration</option>
                <option value="departure">Departure Time</option>
              </select>
            </div>
            <div className="text-sm text-gray-600">
              Showing {sortedFlights.length} of {mockFlightData.meta.count} flights
            </div>
          </div>
        </div>

        {/* Flight Results */}
        <div className="space-y-4">
          {sortedFlights.map((flight) => (
            <div
              key={flight.id}
              className={`bg-white rounded-lg shadow-sm border-2 transition-all duration-200 cursor-pointer hover:shadow-md ${
                selectedFlight === flight.id
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
              onClick={() => setSelectedFlight(flight.id)}
            >
              <div className="p-6">
                {/* Flight Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-semibold text-sm">
                        {flight.validatingAirlineCodes[0]}
                      </span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {mockFlightData.dictionaries.carriers[flight.validatingAirlineCodes[0] as keyof typeof mockFlightData.dictionaries.carriers]}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {flight.numberOfBookableSeats} seats available
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-gray-900">
                      {flight.price.currency} {flight.price.total}
                    </div>
                    <div className="text-sm text-gray-600">per passenger</div>
                  </div>
                </div>

                {/* Flight Route */}
                <div className="border-t border-gray-100 pt-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <div className="text-lg font-semibold text-gray-900">
                            {formatTime(flight.itineraries[0].segments[0].departure.at)}
                          </div>
                          <div className="text-sm text-gray-600">
                            {flight.itineraries[0].segments[0].departure.iataCode}
                            {flight.itineraries[0].segments[0].departure.terminal && 
                              ` Terminal ${flight.itineraries[0].segments[0].departure.terminal}`
                            }
                          </div>
                          <div className="text-xs text-gray-500">
                            {formatDate(flight.itineraries[0].segments[0].departure.at)}
                          </div>
                        </div>
                        <div className="flex-1 mx-4">
                          <div className="flex items-center">
                            <div className="flex-1 h-px bg-gray-300"></div>
                            <div className="mx-2 text-xs text-gray-500">
                              {formatDuration(flight.itineraries[0].duration)}
                            </div>
                            <div className="flex-1 h-px bg-gray-300"></div>
                          </div>
                          <div className="text-center text-xs text-gray-500 mt-1">
                            {flight.itineraries[0].segments.length === 1 ? "Direct" : `${flight.itineraries[0].segments.length - 1} stop`}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-semibold text-gray-900">
                            {formatTime(flight.itineraries[0].segments[flight.itineraries[0].segments.length - 1].arrival.at)}
                          </div>
                          <div className="text-sm text-gray-600">
                            {flight.itineraries[0].segments[flight.itineraries[0].segments.length - 1].arrival.iataCode}
                            {flight.itineraries[0].segments[flight.itineraries[0].segments.length - 1].arrival.terminal && 
                              ` Terminal ${flight.itineraries[0].segments[flight.itineraries[0].segments.length - 1].arrival.terminal}`
                            }
                          </div>
                          <div className="text-xs text-gray-500">
                            {formatDate(flight.itineraries[0].segments[flight.itineraries[0].segments.length - 1].arrival.at)}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Flight Segments */}
                  <div className="mt-4 space-y-3">
                    {flight.itineraries[0].segments.map((segment, index) => (
                      <div key={index} className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{segment.carrierCode}{segment.number}</span>
                            <span className="text-gray-500">•</span>
                            <span className="text-gray-600">{formatDuration(segment.duration)}</span>
                          </div>
                          <div className="text-gray-500">
                            {segment.numberOfStops === 0 ? "Non-stop" : `${segment.numberOfStops} stop`}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Action Button */}
                <div className="mt-6 pt-4 border-t border-gray-100">
                  <button
                    className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors ${
                      selectedFlight === flight.id
                        ? "bg-blue-600 text-white hover:bg-blue-700"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                    onClick={(e) => {
                      e.stopPropagation();
                      // Handle booking logic here
                      alert(`Booking flight ${flight.id} for ${flight.price.currency} ${flight.price.total}`);
                    }}
                  >
                    {selectedFlight === flight.id ? "Select Flight" : "Select This Flight"}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Back to Search */}
        <div className="mt-8 text-center">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Search
          </Link>
        </div>
      </div>
    </div>
  );
} 