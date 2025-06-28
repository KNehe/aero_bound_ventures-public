"use client";
import React, { useState } from "react";

export default function BookingForm() {
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
    alert(`Searching ${form.tripType} flights from ${form.from} to ${form.to} for ${totalPassengers} passenger(s) (${form.adults} adults, ${form.children} children, ${form.infants} infants) in ${form.travelClass} class on ${form.depart}${form.return ? `, returning ${form.return}` : ""}`);
  }

  // Convert string values to numbers for calculations
  const adults = Number(form.adults);
  const children = Number(form.children);
  const infants = Number(form.infants);
  const totalPassengers = adults + children + infants;

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-2xl mx-auto bg-white rounded-2xl shadow-lg p-6 flex flex-col gap-4 -mt-6 relative z-20"
      aria-label="Flight Booking Form"
    >
      {/* Trip Type Toggle */}
      <div className="flex gap-4 mb-2">
        <label className="flex items-center text-gray-900">
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
        <label className="flex items-center text-gray-900">
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

      {/* From/To Fields */}
      <div className="flex flex-col md:flex-row gap-3">
        <div className="flex-1">
          <label htmlFor="from" className="block text-gray-700 font-semibold mb-1 text-base">From</label>
          <input
            id="from"
            name="from"
            type="text"
            required
            placeholder="City or Airport (e.g., NYC, LAX)"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base"
            value={form.from}
            onChange={handleChange}
          />
        </div>
        <div className="flex-1">
          <label htmlFor="to" className="block text-gray-700 font-semibold mb-1 text-base">To</label>
          <input
            id="to"
            name="to"
            type="text"
            required
            placeholder="City or Airport (e.g., LON, CDG)"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base"
            value={form.to}
            onChange={handleChange}
          />
        </div>
      </div>

      {/* Date Fields */}
      <div className="flex flex-col md:flex-row gap-3">
        <div className="flex-1">
          <label htmlFor="depart" className="block text-gray-700 font-semibold mb-1 text-base">Departure</label>
          <input
            id="depart"
            name="depart"
            type="date"
            required
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base"
            value={form.depart}
            onChange={handleChange}
          />
        </div>
        {form.tripType === "roundtrip" && (
          <div className="flex-1">
            <label htmlFor="return" className="block text-gray-700 font-semibold mb-1 text-base">Return</label>
            <input
              id="return"
              name="return"
              type="date"
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base"
              value={form.return}
              onChange={handleChange}
            />
          </div>
        )}
      </div>

      {/* Passenger Breakdown - Compact */}
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label htmlFor="adults" className="block text-gray-700 font-semibold mb-1 text-base">Adults (12+)</label>
          <select
            id="adults"
            name="adults"
            required
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base"
            value={form.adults}
            onChange={handleChange}
          >
            {[1,2,3,4,5,6,7,8,9].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="children" className="block text-gray-700 font-semibold mb-1 text-base">Children (2-11)</label>
          <select
            id="children"
            name="children"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base"
            value={form.children}
            onChange={handleChange}
          >
            {[0,1,2,3,4,5,6,7,8].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="infants" className="block text-gray-700 font-semibold mb-1 text-base">Infants (0-2)</label>
          <select
            id="infants"
            name="infants"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base"
            value={form.infants}
            onChange={handleChange}
          >
            {[0,1,2,3,4].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Travel Class and Options - Compact */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="travelClass" className="block text-gray-700 font-semibold mb-1 text-base">Travel Class</label>
          <select
            id="travelClass"
            name="travelClass"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base"
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
          <label htmlFor="currency" className="block text-gray-700 font-semibold mb-1 text-base">Currency</label>
          <select
            id="currency"
            name="currency"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 text-base"
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

      {/* Non-stop Option and Total - Compact */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="nonStop"
            name="nonStop"
            checked={form.nonStop}
            onChange={handleChange}
            className="mr-2"
          />
          <label htmlFor="nonStop" className="text-gray-700 font-semibold text-base">Non-stop flights only</label>
        </div>
        <div className="text-xs text-gray-600">
          Total: {totalPassengers} {totalPassengers > 9 && <span className="text-red-500">(Max 9)</span>}
        </div>
      </div>

      <button
        type="submit"
        disabled={totalPassengers > 9 || infants > adults}
        className="w-full bg-blue-700 hover:bg-blue-800 disabled:bg-gray-400 text-white font-bold py-2 rounded-lg text-lg shadow transition-colors"
      >
        Search Flights
      </button>
    </form>
  );
} 