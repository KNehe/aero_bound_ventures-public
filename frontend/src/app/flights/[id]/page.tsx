"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import useFlights from "@/store/flights";
import { FlightOffer } from "@/types/flight_offer";


const BASE_API_URL = process.env.NEXT_PUBLIC_API_BASE_URL

export default function FlightPricingPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const selectedFlight = useFlights(state => state.selectedFlight) as FlightOffer
  const [flightOffer, setFlightOffer] = useState<FlightOffer>(selectedFlight);
  const selectFlight = useFlights(state => state.selectFlight);

  useEffect(() => {
    confirmPrice()
  }, [])

  const confirmPrice = async () => {
    const url = `${BASE_API_URL}/shopping/flight-offers/pricing`

    const res = await fetch(url, {
      method: "POST",
      body: JSON.stringify(selectedFlight),
      headers: {
        "Content-Type": "application/json",
      }
    });
    const data = await res.json()
    if (data?.data?.flightOffers?.[0]) {
      selectFlight(data.data.flightOffers[0])
    }
  }


  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-5xl mx-auto px-4">
        <div className="mb-6">
          <Link href="/flights" className="text-sm text-blue-600 hover:underline">&larr; Back to search</Link>
          <h1 className="mt-3 text-2xl font-bold text-black">Confirm flight offer</h1>
          <p className="text-sm text-gray-700 font-medium">Review and confirm the selected flight before continuing to payment.</p>
        </div>

        {flightOffer ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2">
              <div className="bg-white shadow-sm rounded-lg overflow-hidden">
                <div className="p-5 border-b">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-black">
                        {flightOffer.itineraries[0].segments[0].departure.iataCode}
                        <span className="text-gray-500">→</span> {flightOffer.itineraries[0].segments[flightOffer.itineraries[0].segments.length - 1].arrival.iataCode}
                      </h2>
                      <div className="text-sm text-gray-800 mt-1 font-medium">
                        Depart: {new Date(flightOffer.itineraries[0].segments[0].departure.at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                        {flightOffer.itineraries.length > 1 && (
                          <span className="ml-3">• Return: {new Date(flightOffer.itineraries[1].segments[0].departure.at).toLocaleDateString([], { month: 'short', day: 'numeric' })}</span>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-extrabold text-blue-600">${flightOffer.price.total}</div>
                      <div className="text-xs text-gray-600">Total price for all passengers</div>
                    </div>
                  </div>
                </div>

                <div className="p-5 space-y-6">
                  {flightOffer.itineraries.map((itinerary, itinIdx) => (
                    <div key={itinIdx}>
                      <h3 className="text-sm font-semibold text-gray-800 mb-3">{itinIdx === 0 ? 'Outbound' : 'Return'} • {itinerary.duration ?? ''}</h3>

                      <div className="space-y-3">
                        {itinerary.segments.map((segment, sIdx) => (
                          <div key={segment.id} className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                            <div className="flex items-center gap-4">
                              <div className="text-right w-20">
                                <div className="font-medium text-sm text-gray-800">{new Date(segment.departure.at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                                <div className="text-xs text-gray-600">{new Date(segment.departure.at).toLocaleDateString([], { month: 'short', day: 'numeric' })}</div>
                              </div>
                              <div>
                                <div className="font-semibold text-gray-800">{segment.departure.iataCode} → {segment.arrival.iataCode}</div>
                                <div className="text-xs text-gray-700">{segment.carrierCode ?? ''} {segment.number ?? ''} • {segment.aircraft?.code ?? ''}</div>
                              </div>
                            </div>

                            <div className="text-right w-24">
                              <div className="font-medium text-sm text-gray-800">{new Date(segment.arrival.at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                              <div className="text-xs text-gray-600">{new Date(segment.arrival.at).toLocaleDateString([], { month: 'short', day: 'numeric' })}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}

                  <div className="pt-2 border-t">
                    <h4 className="text-sm font-semibold text-gray-800 mb-2">Traveler pricing</h4>
                    <div className="space-y-2">
                      {flightOffer.travelerPricings?.map((tp, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <div className="text-sm text-gray-800 font-medium">{tp.travelerType ?? 'Passenger'} • {tp.fareOption ?? ''}</div>
                          <div className="text-sm font-medium text-black">{tp.price?.currency ?? flightOffer.price.currency} {tp.price?.total}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <aside>
              <div className="bg-white shadow-sm rounded-lg overflow-hidden p-5 space-y-4">
                <div>
                  <div className="text-sm text-gray-800 font-medium">Price summary</div>
                  <div className="mt-2 text-2xl font-extrabold text-blue-600">${flightOffer.price.total}</div>
                </div>

                <div className="text-sm text-gray-800">
                  <div className="flex justify-between"><span>Base fare</span><span>{flightOffer.price.currency ?? 'USD'} {flightOffer.price.base}</span></div>
                  {flightOffer.price.fees?.map((f, i) => (
                    <div key={i} className="flex justify-between text-xs text-gray-600"><span>{f.type}</span><span>{f.amount}</span></div>
                  ))}
                </div>

                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="text-sm font-medium text-gray-800">Grand total</div>
                      <div className="text-xs text-gray-600">Includes taxes & fees</div>
                    </div>

                    <div className="inline-flex items-center gap-3 bg-blue-50 px-4 py-2 rounded-lg">
                      <div className="text-sm text-gray-600">Payable</div>
                      <div className="text-2xl md:text-3xl font-extrabold text-blue-600">{flightOffer.price.currency ?? 'USD'} {flightOffer.price.grandTotal ?? flightOffer.price.total}</div>
                    </div>
                  </div>
                </div>

                <div>
                  <button
                    onClick={() => router.push(`/booking/${flightOffer.id}`)}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg"
                  >
                    Confirm and continue
                  </button>
                </div>

                <div className="text-xs text-gray-500">By confirming you agree to the fare rules and ticketing terms.</div>
              </div>
            </aside>
          </div>
        ) : (
          <div className="bg-white p-6 rounded-lg shadow-sm text-center text-gray-600">Loading flight offer...</div>
        )}
      </div>
    </div>
  );
} 