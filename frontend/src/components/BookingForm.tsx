"use client";
import React, { useState, useEffect, useRef } from "react";
import { useRouter } from 'next/navigation'
import useFlights from "@/store/flights";

interface BookingFormProps {
  prefillDestination: string;
}

export default function BookingForm({ prefillDestination }: BookingFormProps) {
  const originRef = useRef<HTMLDivElement>(null);
  const destinationRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      // Check if click was outside both dropdowns
      if (originRef.current && !originRef.current.contains(event.target as Node) &&
        destinationRef.current && !destinationRef.current.contains(event.target as Node)) {
        setShowDropdown({ origin: false, destination: false });
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (prefillDestination) {
      setForm(prev => ({
        ...prev,
        destinationLocationCode: prefillDestination
      }));
      setDisplayValues(prev => ({
        ...prev,
        destination: prefillDestination
      }));
    }
  }, [prefillDestination]);
  const [form, setForm] = useState({
    originLocationCode: "",
    destinationLocationCode: "",
    departureDate: "",
    returnDate: "",
    tripType: "roundtrip", // "oneway" or "roundtrip"
    adults: 1,
    children: 0,
    infants: 0,
    travelClass: "ECONOMY",
    currency: "USD",
    nonStop: false,
  });
  const [displayValues, setDisplayValues] = useState({
    origin: "",
    destination: ""
  });
  const [isSearching, setIsSearching] = useState(false);
  const { setSearchParams, setLoading } = useFlights();
  const [locationSearchResults, setLocationSearchResults] = useState<{ origin: any[]; destination: any[] }>({
    origin: [],
    destination: []
  });
  const [searchLoading, setSearchLoading] = useState<{ origin: boolean; destination: boolean }>({
    origin: false,
    destination: false
  });
  const [showDropdown, setShowDropdown] = useState<{ origin: boolean; destination: boolean }>({
    origin: false,
    destination: false
  });
  const router = useRouter();


  const BASE_API_URL = process.env.NEXT_PUBLIC_API_BASE_URL;


  const debounce = (callback: any, delay: number) => {
    let timer: any;

    return (...args: any[]) => {
      window.clearTimeout(timer);

      timer = window.setTimeout(() => {
        callback(...args);
      }, delay);
    };
  }

  const debouncedSearchOrigin = useRef(
    debounce((value: string) => searchLocations("origin", value), 300)
  )
  const debouncedSearchDestination = useRef(
    debounce((value: string) => searchLocations("destination", value), 300)
  )

  const searchLocations = async (searchType: 'origin' | 'destination', query: string) => {
    if (!query.trim()) return;

    setSearchLoading(prev => ({ ...prev, [searchType]: true }));
    try {
      const response = await fetch(`${BASE_API_URL}/reference-data/locations?keyword=${query}`);
      const data = await response.json();

      const locations = Array.isArray(data) ? data : [];

      setLocationSearchResults(prev => ({ ...prev, [searchType]: locations }));
      setShowDropdown(prev => ({ ...prev, [searchType]: true }));
    } catch (error) {
      setLocationSearchResults(prev => ({ ...prev, [searchType]: [] }));
    } finally {
      setSearchLoading(prev => ({ ...prev, [searchType]: false }));
    }
  };

  const handleLocationSelect = (searchType: 'origin' | 'destination', location: any) => {
    setForm(prev => ({
      ...prev,
      [`${searchType}LocationCode`]: location.iataCode
    }));
    setDisplayValues(prev => ({
      ...prev,
      [searchType]: location.subType === 'CITY' ? location.name : `${location.name}, ${location.address.cityName}`
    }));
    setShowDropdown(prev => ({ ...prev, [searchType]: false }));
  };

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, value, type } = e.target;
    const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : undefined;

    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const params: Record<string, any> = {
      originLocationCode: form.originLocationCode,
      destinationLocationCode: form.destinationLocationCode,
      departureDate: form.departureDate,
      adults: form.adults.toString(),
      max: "5",
      currencyCode: form.currency,
    };

    if (form.returnDate && form.tripType === "roundtrip") {
      params.returnDate = form.returnDate;
    }

    if (form.children > 0) {
      params.children = form.children.toString();
    }

    if (form.infants > 0) {
      params.infants = form.infants.toString();
    }
    if (form.travelClass) {
      params.travelClass = form.travelClass;
    }

    if (form.nonStop) {
      params.nonStop = form.nonStop.toString();
    }

    // Store params and set loading state
    setSearchParams(params);
    setLoading(true);
    setIsSearching(true);

    // Immediate navigation
    router.push(`/flights`);
  }

  // Convert string values to numbers for calculations
  const adults = Number(form.adults);
  const children = Number(form.children);
  const infants = Number(form.infants);
  const totalPassengers = adults + children + infants;

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-6xl mx-auto bg-white/20 backdrop-blur-sm rounded-2xl border border-white/30 p-6 flex flex-col gap-4 -mt-6 relative z-20"
      aria-label="Flight Booking Form"
    >
      {/* Trip Type Toggle */}
      <div className="flex gap-4 mb-2">
        <label className="flex items-center text-white font-bold">
          <input
            type="radio"
            name="tripType"
            value="roundtrip"
            checked={form.tripType === "roundtrip"}
            onChange={handleChange}
            className="mr-2"
          />
          Round-trip
        </label>
        <label className="flex items-center text-white font-bold">
          <input
            type="radio"
            name="tripType"
            value="oneway"
            checked={form.tripType === "oneway"}
            onChange={handleChange}
            className="mr-2"
          />
          One-way
        </label>
      </div>

      {/* Column 1: From/To */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="relative" ref={originRef}>
          <label htmlFor="originLocationCode" className="block text-white font-semibold mb-1 text-base">From</label>
          <input
            id="originLocationCode"
            name="originLocationCode"
            type="text"
            required
            placeholder="City or Airport (e.g., NYC, LAX)"
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 placeholder-gray-700 text-base bg-white/90"
            value={form.originLocationCode}
            onChange={(e) => {
              const value = e.target.value;
              setDisplayValues(prev => ({ ...prev, origin: value }));
              setForm(prev => ({ ...prev, originLocationCode: value }));
              debouncedSearchOrigin.current(value)
            }}
            onFocus={(e) => {
              if (e.target.value) setShowDropdown(prev => ({ ...prev, origin: true }))
            }}
            onBlur={(e) => {
              // Only hide if the related target is not in the dropdown
              if (!originRef.current?.contains(e.relatedTarget)) {
                setTimeout(() => {
                  setShowDropdown(prev => ({ ...prev, origin: false }));
                }, 200);
              }
            }}
          />
          {showDropdown.origin && (
            <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
              {searchLoading.origin ? (
                <div className="p-3 text-gray-500">Loading...</div>
              ) : locationSearchResults.origin.length > 0 ? (
                locationSearchResults.origin.map((location: any) => (
                  <div
                    key={location.id}
                    className="p-3 hover:bg-gray-100 cursor-pointer"
                    onClick={() => handleLocationSelect('origin', location)}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900">{location.iataCode}</span>
                      <span className="text-xs px-2 py-0.5 bg-gray-200 rounded-full text-gray-700">
                        {location.subType === 'CITY' ? 'City' : 'Airport'}
                      </span>
                    </div>
                    <div className="text-sm text-gray-800">
                      {location.subType === 'CITY' ? location.name : (
                        <>
                          {location.name}
                          <span className="text-gray-600"> · {location.address.cityName}</span>
                        </>
                      )}
                    </div>
                    <div className="text-xs text-gray-600">
                      {location.address.countryName}
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-3 text-gray-500">No results found</div>
              )}
            </div>
          )}
        </div>
        <div className="relative" ref={destinationRef}>
          <label htmlFor="destinationLocationCode" className="block text-white font-semibold mb-1 text-base">To</label>
          <input
            id="destinationLocationCode"
            name="destinationLocationCode"
            type="text"
            required
            placeholder="City or Airport (e.g., LON, CDG)"
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 placeholder-gray-700 text-base bg-white/90"
            value={form.destinationLocationCode}
            onChange={(e) => {
              const value = e.target.value;
              setDisplayValues(prev => ({ ...prev, destination: value }));
              setForm(prev => ({ ...prev, destinationLocationCode: value }));
              debouncedSearchDestination.current(value)
            }}
            onFocus={(e) => {
              if (e.target.value) setShowDropdown(prev => ({ ...prev, destination: true }))
            }}
            onBlur={(e) => {
              // Only hide if the related target is not in the dropdown
              if (!destinationRef.current?.contains(e.relatedTarget)) {
                setTimeout(() => {
                  setShowDropdown(prev => ({ ...prev, destination: false }));
                }, 200);
              }
            }}
          />
          {showDropdown.destination && (
            <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
              {searchLoading.destination ? (
                <div className="p-3 text-gray-500">Loading...</div>
              ) : locationSearchResults.destination.length > 0 ? (
                locationSearchResults.destination.map((location: any) => (
                  <div
                    key={location.id}
                    className="p-3 hover:bg-gray-100 cursor-pointer"
                    onClick={() => handleLocationSelect('destination', location)}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900">{location.iataCode}</span>
                      <span className="text-xs px-2 py-0.5 bg-gray-200 rounded-full text-gray-700">
                        {location.subType === 'CITY' ? 'City' : 'Airport'}
                      </span>
                    </div>
                    <div className="text-sm text-gray-800">
                      {location.subType === 'CITY' ? location.name : (
                        <>
                          {location.name}
                          <span className="text-gray-600"> · {location.address.cityName}</span>
                        </>
                      )}
                    </div>
                    <div className="text-xs text-gray-600">
                      {location.address.countryName}
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-3 text-gray-500">No results found</div>
              )}
            </div>
          )}
        </div>
        <div>
          <label htmlFor="departureDate" className="block text-white font-semibold mb-1 text-base">Departure</label>
          <input
            id="departureDate"
            name="departureDate"
            type="date"
            required
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base bg-white/90"
            value={form.departureDate}
            onChange={handleChange}
          />
        </div>
      </div>

      {/* Column 2: Return Date, Travel Class, Currency */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label htmlFor="returnDate" className="block text-white font-semibold mb-1 text-base">Return</label>
          <input
            id="returnDate"
            name="returnDate"
            type="date"
            required={form.tripType === "roundtrip"}
            disabled={form.tripType === "oneway"}
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base bg-white/90 disabled:bg-gray-300 disabled:text-gray-500"
            value={form.returnDate}
            onChange={handleChange}
          />
        </div>
        <div>
          <label htmlFor="travelClass" className="block text-white font-semibold mb-1 text-base">Travel Class</label>
          <select
            id="travelClass"
            name="travelClass"
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base bg-white/90"
            value={form.travelClass}
            onChange={handleChange}
          >
            <option value="ECONOMY">Economy</option>
            <option value="PREMIUM_ECONOMY">Premium Economy</option>
            <option value="BUSINESS">Business</option>
            <option value="FIRST">First Class</option>
          </select>
        </div>
        {/* <div>
          <label htmlFor="currency" className="block text-white font-semibold mb-1 text-base">Currency</label>
          <select
            id="currency"
            name="currency"
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base bg-white/90"
            value={form.currency}
            onChange={handleChange}
          >
            <option value="USD">USD ($)</option>
            <option value="EUR">EUR (€)</option>
            <option value="GBP">GBP (£)</option>
            <option value="CAD">CAD (C$)</option>
          </select>
        </div> */}
      </div>

      {/* Column 3: Passengers and Options */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label htmlFor="adults" className="block text-white font-semibold mb-1 text-base">Adults (12+)</label>
          <select
            id="adults"
            name="adults"
            required
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base bg-white/90"
            value={form.adults}
            onChange={handleChange}
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="children" className="block text-white font-semibold mb-1 text-base">Children (2-11)</label>
          <select
            id="children"
            name="children"
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base bg-white/90"
            value={form.children}
            onChange={handleChange}
          >
            {[0, 1, 2, 3, 4, 5, 6, 7, 8].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="infants" className="block text-white font-semibold mb-1 text-base">Infants (0-2)</label>
          <select
            id="infants"
            name="infants"
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base bg-white/90"
            value={form.infants}
            onChange={handleChange}
          >
            {[0, 1, 2, 3, 4].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Bottom Row: Non-stop Option, Total, and Submit */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        {/* <div className="flex items-center">
          <input
            type="checkbox"
            id="nonStop"
            name="nonStop"
            checked={form.nonStop === "False" ? false : true}
            onChange={handleChange}
            className="mr-2"
          />
          <label htmlFor="nonStop" className="text-white font-semibold text-base">Non-stop flights only</label>
        </div> */}
        <div className="text-sm text-white">
          <span className="font-bold">Total:</span> {totalPassengers} {totalPassengers > 9 && <span className="text-red-300">(Max 9)</span>}
        </div>
        <button
          type="submit"
          disabled={totalPassengers > 9 || infants > adults || isSearching}
          className="w-full md:w-auto bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500 text-white font-bold py-2 px-8 rounded-lg text-lg shadow transition-colors"
        >
          {isSearching ? (
            <div className="flex items-center justify-center gap-2">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Searching...
            </div>
          ) : (
            "Search Flights"
          )}
        </button>
      </div>
    </form>
  );
} 