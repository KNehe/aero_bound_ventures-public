"use client";
import { useEffect, useState } from "react";
import { FaMapMarkerAlt } from "react-icons/fa";
import { fetchPopularDestinations } from "../utils/fetchPopularDestinations";

type Destination = {
  destination: string;
  analytics: {
    flights: { score: number };
    travelers: { score: number };
  };
};

const DEFAULT_DESTINATIONS: Destination[] = [
  {
    destination: "LON",
    analytics: {
      flights: { score: 71 },
      travelers: { score: 56 }
    }
  },
  {
    destination: "DXB",
    analytics: {
      flights: { score: 26 },
      travelers: { score: 7 }
    }
  },
  {
    destination: "PAR",
    analytics: {
      flights: { score: 74 },
      travelers: { score: 100 }
    }
  },
  {
    destination: "GRU",
    analytics: {
      flights: { score: 50 },
      travelers: { score: 30 }
    }
  }
];

const IATA_TO_CITY: Record<string, string> = {
  LON: "London, UK",
  DXB: "Dubai, UAE",
  PAR: "Paris, France",
  GRU: "Sao Paulo, Brazil",
  BCN: "Barcelona, Spain",
  NYC: "New York, USA",
  MAD: "Madrid, Spain",
  MNL: "Manila, Philippines",
  BKK: "Bangkok, Thailand",
  SIN: "Singapore, Singapore",
  CMB: "Colombo, Sri Lanka",
  SYD: "Sydney, Australia",
  KTM: "Kathmandu, Nepal",
  // Add more as needed
};


interface PopularDestinationsSectionProps {
  setPrefillDestination: (destination: string) => void;
}

export default function PopularDestinationsSection({ setPrefillDestination }: PopularDestinationsSectionProps) {
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const currentPeriod = `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`;

    fetchPopularDestinations("DXB", currentPeriod)
      .then((data) => {
        if (data && data.length > 0) {
          setDestinations(data);
        } else {
          setDestinations(DEFAULT_DESTINATIONS);
        }
        setLoading(false);
      })
      .catch((err) => {
        setLoading(false);
      });
  }, []);
  return (
    <section className="w-full bg-gray-100 py-20 px-4 md:px-0">
      <div className="max-w-5xl mx-auto text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-extrabold text-blue-900 mb-4">Popular Destinations</h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Discover our most sought-after destinations and start planning your next adventure
        </p>
      </div>
      {loading ? (
        <div className="text-center text-blue-700 py-10">Loading...</div>
      ) : error ? (
        <div className="text-center text-red-600 py-10">{error}</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {destinations.map((destination) => (
            <div key={destination.destination} className="bg-white rounded-2xl shadow-lg overflow-hidden transition-transform hover:-translate-y-2 hover:shadow-xl">
              <div className="relative h-48 overflow-hidden">
                <img
                  src="/aeroplane.jpg"
                  alt={IATA_TO_CITY[destination.destination] || destination.destination}
                  className="w-full h-full object-cover transition-transform hover:scale-110"
                />
                <div className="absolute bottom-3 left-3 bg-blue-600 text-white px-2 py-1 rounded-full text-sm font-semibold">
                  Flights: {destination.analytics.flights.score}
                </div>
              </div>
              <div className="p-6">
                <div className="flex items-center mb-2">
                  <FaMapMarkerAlt className="text-blue-600 mr-2" />
                  <h3 className="text-xl font-bold text-blue-900">{IATA_TO_CITY[destination.destination] || destination.destination}</h3>
                </div>
                <p className="text-gray-600 text-sm mb-4">Travelers Score: {destination.analytics.travelers.score}</p>
                <button 
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors duration-200"
                  onClick={() => {
                    setPrefillDestination(destination.destination);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                >
                  Book Now
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
