"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";

export default function BookingForm() {
  const router = useRouter();
  const [form, setForm] = useState({
    from: "",
    to: "",
    depart: "",
    return: "",
    tripType: "roundtrip", // "oneway" or "roundtrip"
    adults: 1,
    children: 0,
    infants: 0,
    travelClass: "ECONOMY",
    currency: "USD",
    nonStop: false,
  });

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, value, type } = e.target;
    const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : undefined;
    
    setForm((prev) => ({ 
      ...prev, 
      [name]: type === 'checkbox' ? checked : value 
    }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const totalPassengers = Number(form.adults) + Number(form.children) + Number(form.infants);
    
    // Navigate to flights results page
    router.push('/flights');
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
        <div>
          <label htmlFor="from" className="block text-white font-semibold mb-1 text-base">From</label>
          <input
            id="from"
            name="from"
            type="text"
            required
            placeholder="City or Airport (e.g., NYC, LAX)"
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 placeholder-gray-700 text-base bg-white/90"
            value={form.from}
            onChange={handleChange}
          />
        </div>
        <div>
          <label htmlFor="to" className="block text-white font-semibold mb-1 text-base">To</label>
          <input
            id="to"
            name="to"
            type="text"
            required
            placeholder="City or Airport (e.g., LON, CDG)"
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 placeholder-gray-700 text-base bg-white/90"
            value={form.to}
            onChange={handleChange}
          />
        </div>
        <div>
          <label htmlFor="depart" className="block text-white font-semibold mb-1 text-base">Departure</label>
          <input
            id="depart"
            name="depart"
            type="date"
            required
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base bg-white/90"
            value={form.depart}
            onChange={handleChange}
          />
        </div>
      </div>

      {/* Column 2: Return Date, Travel Class, Currency */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label htmlFor="return" className="block text-white font-semibold mb-1 text-base">Return</label>
          <input
            id="return"
            name="return"
            type="date"
            required={form.tripType === "roundtrip"}
            disabled={form.tripType === "oneway"}
            className="w-full border border-white/30 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base bg-white/90 disabled:bg-gray-300 disabled:text-gray-500"
            value={form.return}
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
        <div>
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
        </div>
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
            {[1,2,3,4,5,6,7,8,9].map(num => (
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
            {[0,1,2,3,4,5,6,7,8].map(num => (
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
            {[0,1,2,3,4].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Bottom Row: Non-stop Option, Total, and Submit */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="nonStop"
            name="nonStop"
            checked={form.nonStop}
            onChange={handleChange}
            className="mr-2"
          />
          <label htmlFor="nonStop" className="text-white font-semibold text-base">Non-stop flights only</label>
        </div>
        <div className="text-sm text-white">
          <span className="font-bold">Total:</span> {totalPassengers} {totalPassengers > 9 && <span className="text-red-300">(Max 9)</span>}
        </div>
        <button
          type="submit"
          disabled={totalPassengers > 9 || infants > adults}
          className="w-full md:w-auto bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500 text-white font-bold py-2 px-8 rounded-lg text-lg shadow transition-colors"
        >
          Search Flights
        </button>
      </div>
    </form>
  );
} 