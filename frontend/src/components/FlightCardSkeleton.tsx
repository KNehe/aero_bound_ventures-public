import React from 'react';

export default function FlightCardSkeleton() {
    return (
        <div className="bg-white rounded-lg shadow-md mb-4 p-6 animate-pulse">
            {/* Header: Airline info and basic details */}
            <div className="flex justify-between items-start mb-6">
                <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-gray-200 rounded-md"></div>
                    <div>
                        <div className="h-4 w-32 bg-gray-200 rounded mb-2"></div>
                        <div className="h-3 w-24 bg-gray-200 rounded"></div>
                    </div>
                </div>
                <div className="h-6 w-24 bg-gray-200 rounded"></div>
            </div>

            {/* Itineraries */}
            <div className="space-y-6">
                {[1, 2].map((i) => (
                    <div key={i} className="flex flex-col md:flex-row items-center gap-6 relative">
                        {/* Left: Checkboxes/Radio placeholder */}
                        <div className="hidden md:block w-4 h-4 rounded-full bg-gray-200"></div>

                        {/* Flight Details */}
                        <div className="flex-1 w-full grid grid-cols-3 gap-4 text-center items-center">
                            {/* Departure */}
                            <div className="flex flex-col items-center">
                                <div className="h-8 w-16 bg-gray-200 rounded mb-1"></div>
                                <div className="h-4 w-12 bg-gray-200 rounded text-sm mb-1"></div>
                                <div className="h-3 w-20 bg-gray-200 rounded text-xs"></div>
                            </div>

                            {/* Duration & Stops */}
                            <div className="flex flex-col items-center w-full px-2">
                                <div className="h-3 w-16 bg-gray-200 rounded text-xs mb-1"></div>
                                <div className="w-full flex items-center gap-1">
                                    <div className="h-[2px] w-full bg-gray-200"></div>
                                </div>
                                <div className="h-3 w-24 bg-gray-200 rounded text-xs mt-1"></div>
                            </div>

                            {/* Arrival */}
                            <div className="flex flex-col items-center">
                                <div className="h-8 w-16 bg-gray-200 rounded mb-1"></div>
                                <div className="h-4 w-12 bg-gray-200 rounded text-sm mb-1"></div>
                                <div className="h-3 w-20 bg-gray-200 rounded text-xs"></div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Footer: Price and Button */}
            <div className="mt-6 pt-4 border-t border-gray-100 flex justify-between items-center">
                <div className="flex flex-col">
                    <div className="h-4 w-24 bg-gray-200 rounded mb-1"></div>
                    <div className="h-8 w-32 bg-gray-200 rounded"></div>
                </div>
                <div className="h-10 w-32 bg-gray-300 rounded-lg"></div>
            </div>
        </div>
    );
}
