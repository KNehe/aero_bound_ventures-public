import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useFlights = create()(
  persist(
    (set) => ({
      flights: [],
      selectedFlight: null,
      selectFlight: (flight) => set({ selectedFlight: flight }),
      updateFlights: (newFlights) => set({ flights: newFlights }),
    }),
    {
      name: 'flights-storage',
    },
  ),
)

export default useFlights;
