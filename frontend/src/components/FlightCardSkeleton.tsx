import React from 'react';

export default function FlightCardSkeleton() {
    return (
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden mb-6 animate-pulse border border-gray-100">
            {/* Card Content */}
            <div className="p-6">
                {/* Outbound Itinerary */}
                <div className="flex items-center gap-6 py-4">
                    {/* Airline Logo */}
                    <div className="flex flex-col items-center w-16 flex-shrink-0">
                        <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
                        <div className="w-10 h-3 bg-gray-200 rounded mt-1"></div>
                    </div>

                    {/* Departure */}
                    <div className="flex flex-col items-center flex-shrink-0">
                        <div className="w-14 h-7 bg-gray-200 rounded mb-1"></div>
                        <div className="w-10 h-4 bg-gray-200 rounded mb-1"></div>
                        <div className="w-12 h-3 bg-gray-200 rounded"></div>
                    </div>

                    {/* Timeline */}
                    <div className="flex-1 flex flex-col items-center px-4">
                        <div className="w-16 h-3 bg-gray-200 rounded mb-2"></div>
                        <div className="w-full flex items-center">
                            <div className="w-2 h-2 rounded-full bg-gray-200"></div>
                            <div className="flex-1 h-0.5 bg-gray-200 mx-2"></div>
                            <div className="w-2 h-2 rounded-full bg-gray-200"></div>
                        </div>
                        <div className="w-20 h-3 bg-gray-200 rounded mt-2"></div>
                    </div>

                    {/* Arrival */}
                    <div className="flex flex-col items-center flex-shrink-0">
                        <div className="w-14 h-7 bg-gray-200 rounded mb-1"></div>
                        <div className="w-10 h-4 bg-gray-200 rounded mb-1"></div>
                        <div className="w-12 h-3 bg-gray-200 rounded"></div>
                    </div>
                </div>

                {/* Divider */}
                <div className="border-t border-gray-200 my-2"></div>

                {/* Return Itinerary */}
                <div className="flex items-center gap-6 py-4">
                    {/* Airline Logo */}
                    <div className="flex flex-col items-center w-16 flex-shrink-0">
                        <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
                        <div className="w-10 h-3 bg-gray-200 rounded mt-1"></div>
                    </div>

                    {/* Departure */}
                    <div className="flex flex-col items-center flex-shrink-0">
                        <div className="w-14 h-7 bg-gray-200 rounded mb-1"></div>
                        <div className="w-10 h-4 bg-gray-200 rounded mb-1"></div>
                        <div className="w-12 h-3 bg-gray-200 rounded"></div>
                    </div>

                    {/* Timeline */}
                    <div className="flex-1 flex flex-col items-center px-4">
                        <div className="w-16 h-3 bg-gray-200 rounded mb-2"></div>
                        <div className="w-full flex items-center">
                            <div className="w-2 h-2 rounded-full bg-gray-200"></div>
                            <div className="flex-1 h-0.5 bg-gray-200 mx-2"></div>
                            <div className="w-2 h-2 rounded-full bg-gray-200"></div>
                        </div>
                        <div className="w-20 h-3 bg-gray-200 rounded mt-2"></div>
                    </div>

                    {/* Arrival */}
                    <div className="flex flex-col items-center flex-shrink-0">
                        <div className="w-14 h-7 bg-gray-200 rounded mb-1"></div>
                        <div className="w-10 h-4 bg-gray-200 rounded mb-1"></div>
                        <div className="w-12 h-3 bg-gray-200 rounded"></div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t border-gray-100">
                <div>
                    <div className="w-16 h-3 bg-gray-200 rounded mb-2"></div>
                    <div className="w-24 h-8 bg-gray-200 rounded"></div>
                    <div className="w-20 h-3 bg-gray-200 rounded mt-1"></div>
                </div>
                <div className="w-32 h-12 bg-gray-300 rounded-xl"></div>
            </div>
        </div>
    );
}
