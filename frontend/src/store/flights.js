import { create } from 'zustand'

const useFlights = create((set) => ({
  flights: [],
  updateFlights: (newFlights) => set({ flights: newFlights }),
}))

export default useFlights;