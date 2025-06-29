"use client";
import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";

// Mock data structure based on the API response
interface FlightPricingData {
  data: {
    type: string;
    flightOffers: Array<{
      id: string;
      itineraries: Array<{
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
          aircraft?: {
            code: string;
          };
        }>;
      }>;
      price: {
        currency: string;
        total: string;
        base: string;
        grandTotal: string;
        billingCurrency?: string;
        fees: Array<{
          amount: string;
          type: string;
        }>;
      };
      validatingAirlineCodes: string[];
      travelerPricings: Array<{
        travelerId: string;
        travelerType: string;
        price: {
          currency: string;
          total: string;
          base: string;
          taxes?: Array<{
            amount: string;
            code: string;
          }>;
        };
        fareDetailsBySegment: Array<{
          segmentId: string;
          cabin: string;
          fareBasis: string;
          class: string;
          includedCheckedBags: {
            weight?: number;
            weightUnit?: string;
            quantity?: number;
          };
        }>;
      }>;
    }>;
  };
  dictionaries?: {
    locations?: Record<string, { cityCode: string; countryCode: string }>;
  };
}

// Mock data for demonstration
const mockPricingData: FlightPricingData = {
  data: {
    type: "flight-offers-pricing",
    flightOffers: [
      {
        id: "1",
        itineraries: [
          {
            segments: [
              {
                departure: { iataCode: "SYD", terminal: "1", at: "2021-02-01T19:15:00" },
                arrival: { iataCode: "SIN", terminal: "1", at: "2021-02-02T00:30:00" },
                carrierCode: "TR",
                number: "13",
                duration: "PT8H15M",
                numberOfStops: 0,
                aircraft: { code: "789" },
              },
              {
                departure: { iataCode: "SIN", terminal: "1", at: "2021-02-02T22:05:00" },
                arrival: { iataCode: "DMK", terminal: "1", at: "2021-02-02T23:30:00" },
                carrierCode: "TR",
                number: "868",
                duration: "PT2H25M",
                numberOfStops: 0,
                aircraft: { code: "788" },
              },
            ],
          },
          {
            segments: [
              {
                departure: { iataCode: "DMK", terminal: "1", at: "2021-02-05T23:15:00" },
                arrival: { iataCode: "SIN", terminal: "1", at: "2021-02-06T02:50:00" },
                carrierCode: "TR",
                number: "867",
                duration: "PT2H35M",
                numberOfStops: 0,
                aircraft: { code: "788" },
              },
              {
                departure: { iataCode: "SIN", terminal: "1", at: "2021-02-06T06:55:00" },
                arrival: { iataCode: "SYD", terminal: "1", at: "2021-02-06T18:15:00" },
                carrierCode: "TR",
                number: "12",
                duration: "PT8H20M",
                numberOfStops: 0,
                aircraft: { code: "789" },
              },
            ],
          },
        ],
        price: {
          currency: "EUR",
          total: "546.70",
          base: "334.00",
          grandTotal: "546.70",
          fees: [
            { amount: "0.00", type: "SUPPLIER" },
            { amount: "0.00", type: "TICKETING" },
          ],
        },
        validatingAirlineCodes: ["HR"],
        travelerPricings: [
          {
            travelerId: "1",
            travelerType: "ADULT",
            price: {
              currency: "EUR",
              total: "546.70",
              base: "334.00",
            },
            fareDetailsBySegment: [
              {
                segmentId: "1",
                cabin: "ECONOMY",
                fareBasis: "O2TR24",
                class: "O",
                includedCheckedBags: { weight: 20, weightUnit: "KG" },
              },
              {
                segmentId: "2",
                cabin: "ECONOMY",
                fareBasis: "O2TR24",
                class: "O",
                includedCheckedBags: { weight: 20, weightUnit: "KG" },
              },
              {
                segmentId: "5",
                cabin: "ECONOMY",
                fareBasis: "X2TR24",
                class: "X",
                includedCheckedBags: { weight: 20, weightUnit: "KG" },
              },
              {
                segmentId: "6",
                cabin: "ECONOMY",
                fareBasis: "H2TR24",
                class: "H",
                includedCheckedBags: { weight: 20, weightUnit: "KG" },
              },
            ],
          },
        ],
      },
    ],
  },
  dictionaries: {
    locations: {
      SYD: { cityCode: "SYD", countryCode: "AU" },
      SIN: { cityCode: "SIN", countryCode: "SG" },
      DMK: { cityCode: "BKK", countryCode: "TH" },
    },
  },
};

export default function FlightPricingPage({ params }: { params: { id: string } }) {
  const [selectedTravelers, setSelectedTravelers] = useState<Record<string, boolean>>({});
  const flightOffer = mockPricingData.data.flightOffers[0];

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
    const date = new Date(dateTime);
    const hours = date.getUTCHours().toString().padStart(2, '0');
    const minutes = date.getUTCMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
  };

  const formatDate = (dateTime: string) => {
    const date = new Date(dateTime);
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  };

  const totalPrice = flightOffer.travelerPricings.reduce(
    (sum, traveler) => sum + parseFloat(traveler.price.total),
    0
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <Link href="/flights" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span className="font-semibold">Back to Results</span>
            </Link>
            <div className="text-right">
              <div className="text-2xl font-bold">{flightOffer.price.currency} {totalPrice.toFixed(2)}</div>
              <div className="text-sm opacity-90">Total for all passengers</div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Flight Details */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Flight Details</h2>
              
              {/* Outbound Flight */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Outbound • {formatDate(flightOffer.itineraries[0].segments[0].departure.at)}</h3>
                <div className="space-y-4">
                  {flightOffer.itineraries[0].segments.map((segment, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <div>
                              <div className="text-lg font-semibold text-gray-900">
                                {formatTime(segment.departure.at)}
                              </div>
                              <div className="text-sm text-gray-600">
                                {segment.departure.iataCode}
                                {segment.departure.terminal && ` Terminal ${segment.departure.terminal}`}
                              </div>
                            </div>
                            <div className="flex-1 mx-4">
                              <div className="flex items-center">
                                <div className="flex-1 h-px bg-gray-300"></div>
                                <div className="mx-2 text-xs text-gray-500">
                                  {formatDuration(segment.duration)}
                                </div>
                                <div className="flex-1 h-px bg-gray-300"></div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-semibold text-gray-900">
                                {formatTime(segment.arrival.at)}
                              </div>
                              <div className="text-sm text-gray-600">
                                {segment.arrival.iataCode}
                                {segment.arrival.terminal && ` Terminal ${segment.arrival.terminal}`}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-sm text-gray-600">
                            <span>{segment.carrierCode}{segment.number}</span>
                            <span>{segment.aircraft?.code && `Aircraft: ${segment.aircraft.code}`}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Return Flight */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Return • {formatDate(flightOffer.itineraries[1].segments[0].departure.at)}</h3>
                <div className="space-y-4">
                  {flightOffer.itineraries[1].segments.map((segment, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <div>
                              <div className="text-lg font-semibold text-gray-900">
                                {formatTime(segment.departure.at)}
                              </div>
                              <div className="text-sm text-gray-600">
                                {segment.departure.iataCode}
                                {segment.departure.terminal && ` Terminal ${segment.departure.terminal}`}
                              </div>
                            </div>
                            <div className="flex-1 mx-4">
                              <div className="flex items-center">
                                <div className="flex-1 h-px bg-gray-300"></div>
                                <div className="mx-2 text-xs text-gray-500">
                                  {formatDuration(segment.duration)}
                                </div>
                                <div className="flex-1 h-px bg-gray-300"></div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-semibold text-gray-900">
                                {formatTime(segment.arrival.at)}
                              </div>
                              <div className="text-sm text-gray-600">
                                {segment.arrival.iataCode}
                                {segment.arrival.terminal && ` Terminal ${segment.arrival.terminal}`}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-sm text-gray-600">
                            <span>{segment.carrierCode}{segment.number}</span>
                            <span>{segment.aircraft?.code && `Aircraft: ${segment.aircraft.code}`}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Pricing Breakdown */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Pricing Breakdown</h2>
              
              <div className="space-y-4">
                {flightOffer.travelerPricings.map((traveler) => (
                  <div key={traveler.travelerId} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-gray-800 capitalize">
                        {traveler.travelerType} {traveler.travelerId}
                      </h3>
                      <div className="text-right">
                        <div className="text-lg font-bold text-gray-900">
                          {traveler.price.currency} {traveler.price.total}
                        </div>
                        <div className="text-sm text-gray-600">
                          Base: {traveler.price.currency} {traveler.price.base}
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-sm text-gray-600">
                      <div className="grid grid-cols-2 gap-2">
                        <span>Fare Class: {traveler.fareDetailsBySegment[0].class}</span>
                        <span>Cabin: {traveler.fareDetailsBySegment[0].cabin}</span>
                        <span>Checked Bags: {traveler.fareDetailsBySegment[0].includedCheckedBags.weight || traveler.fareDetailsBySegment[0].includedCheckedBags.quantity} {traveler.fareDetailsBySegment[0].includedCheckedBags.weightUnit || 'pieces'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Fees */}
              {flightOffer.price.fees.length > 0 && (
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <h4 className="font-semibold text-gray-800 mb-2">Fees</h4>
                  <div className="space-y-2">
                    {flightOffer.price.fees.map((fee, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span className="text-gray-600 capitalize">{fee.type.replace('_', ' ').toLowerCase()}</span>
                        <span className="text-gray-900">{fee.currency} {fee.amount}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar - Booking Summary */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border p-6 sticky top-24">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Booking Summary</h2>
              
              <div className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Base Fare</span>
                  <span className="text-gray-900">{flightOffer.price.currency} {flightOffer.price.base}</span>
                </div>
                
                {flightOffer.price.fees.map((fee, index) => (
                  <div key={index} className="flex justify-between text-sm">
                    <span className="text-gray-600 capitalize">{fee.type.replace('_', ' ').toLowerCase()}</span>
                    <span className="text-gray-900">{flightOffer.price.currency} {fee.amount}</span>
                  </div>
                ))}
                
                <div className="border-t border-gray-200 pt-4">
                  <div className="flex justify-between text-lg font-bold">
                    <span>Total</span>
                    <span>{flightOffer.price.currency} {flightOffer.price.grandTotal}</span>
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {flightOffer.price.billingCurrency && flightOffer.price.billingCurrency !== flightOffer.price.currency && 
                      `Billed in ${flightOffer.price.billingCurrency}`
                    }
                  </div>
                </div>
              </div>

              <button
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg mt-6 transition-colors"
                onClick={() => alert('Proceeding to booking...')}
              >
                Continue to Booking
              </button>

              <div className="mt-4 text-xs text-gray-500 text-center">
                By continuing, you agree to our terms and conditions
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 