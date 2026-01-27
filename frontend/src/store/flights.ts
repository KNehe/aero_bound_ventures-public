import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { FlightOffer } from '@/types/flight-booking';

interface FlightsState {
    flights: FlightOffer[];
    selectedFlight: FlightOffer | null;
    isLoading: boolean;
    error: string | null;
    searchParams: Record<string, any> | null;

    selectFlight: (flight: FlightOffer) => void;
    updateFlights: (newFlights: FlightOffer[]) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    setSearchParams: (params: Record<string, any>) => void;
    clearSearch: () => void;
}

const useFlights = create<FlightsState>()(
    persist(
        (set) => ({
            flights: [],
            selectedFlight: null,
            isLoading: false,
            error: null,
            searchParams: null,

            selectFlight: (flight) => set({ selectedFlight: flight }),
            updateFlights: (newFlights) => set({ flights: newFlights, isLoading: false, error: null }),
            setLoading: (isLoading) => set({ isLoading, error: null }),
            setError: (error) => set({ error, isLoading: false, flights: [] }),
            setSearchParams: (params) => set({ searchParams: params }),
            clearSearch: () => set({ flights: [], searchParams: null, error: null, isLoading: false }),
        }),
        {
            name: 'flights-storage',
            // Only persist selectedFlight if needed, but maybe better not to persist search state too aggressively
            // to avoid stale "loading" states if the user closes the tab.
            // However, for this UX request, we might want to keep the search params.
            partialize: (state) => ({
                flights: state.flights,
                selectedFlight: state.selectedFlight,
                searchParams: state.searchParams,
            }),
        },
    ),
);

export default useFlights;
