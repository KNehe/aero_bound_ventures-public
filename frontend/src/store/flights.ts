import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { FlightOffer } from '@/types/flight_offer';

interface FlightsState {
    selectedFlight: FlightOffer | null;
    searchParams: Record<string, any> | null;

    selectFlight: (flight: FlightOffer) => void;
    setSearchParams: (params: Record<string, any>) => void;
    clearSearch: () => void;
}

const useFlights = create<FlightsState>()(
    persist(
        (set) => ({
            selectedFlight: null,
            searchParams: null,

            selectFlight: (flight) => set({ selectedFlight: flight }),
            setSearchParams: (params) => set({ searchParams: params }),
            clearSearch: () => set({ searchParams: null }),
        }),
        {
            name: 'flights-storage',
            partialize: (state) => ({
                selectedFlight: state.selectedFlight,
                searchParams: state.searchParams,
            }),
        },
    ),
);

export default useFlights;
