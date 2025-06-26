"use client";
import React, { useState } from "react";

export default function BookingForm() {
  const [form, setForm] = useState({
    from: "",
    to: "",
    depart: "",
    return: "",
    passengers: 1,
  });

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // For now, just alert the form data
    alert(`Searching flights from ${form.from} to ${form.to} for ${form.passengers} passenger(s) on ${form.depart}${form.return ? `, returning ${form.return}` : ""}`);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-2xl mx-auto bg-white rounded-2xl shadow-lg p-8 flex flex-col gap-6 -mt-12 relative z-20"
      aria-label="Flight Booking Form"
    >
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <label htmlFor="from" className="block text-gray-700 font-semibold mb-1">From</label>
          <input
            id="from"
            name="from"
            type="text"
            required
            placeholder="City or Airport"
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900"
            value={form.from}
            onChange={handleChange}
          />
        </div>
        <div className="flex-1">
          <label htmlFor="to" className="block text-gray-700 font-semibold mb-1">To</label>
          <input
            id="to"
            name="to"
            type="text"
            required
            placeholder="City or Airport"
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900"
            value={form.to}
            onChange={handleChange}
          />
        </div>
      </div>
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <label htmlFor="depart" className="block text-gray-700 font-semibold mb-1">Departure</label>
          <input
            id="depart"
            name="depart"
            type="date"
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900"
            value={form.depart}
            onChange={handleChange}
          />
        </div>
        <div className="flex-1">
          <label htmlFor="return" className="block text-gray-700 font-semibold mb-1">Return (optional)</label>
          <input
            id="return"
            name="return"
            type="date"
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900"
            value={form.return}
            onChange={handleChange}
          />
        </div>
        <div className="flex-1">
          <label htmlFor="passengers" className="block text-gray-700 font-semibold mb-1">Passengers</label>
          <input
            id="passengers"
            name="passengers"
            type="number"
            min={1}
            max={9}
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900"
            value={form.passengers}
            onChange={handleChange}
          />
        </div>
      </div>
      <button
        type="submit"
        className="w-full bg-blue-700 hover:bg-blue-800 text-white font-bold py-3 rounded-lg text-lg shadow transition-colors"
      >
        Search Flights
      </button>
    </form>
  );
} 