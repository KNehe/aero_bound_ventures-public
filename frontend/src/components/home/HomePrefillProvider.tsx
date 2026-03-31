"use client";

import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

interface HomePrefillContextValue {
  prefillDestination: string;
  setPrefillDestination: (destination: string) => void;
}

const HomePrefillContext = createContext<HomePrefillContextValue | null>(null);

export function HomePrefillProvider({ children }: { children: ReactNode }) {
  const [prefillDestination, setPrefillDestination] = useState("");

  const value = useMemo(
    () => ({
      prefillDestination,
      setPrefillDestination,
    }),
    [prefillDestination]
  );

  return (
    <HomePrefillContext.Provider value={value}>
      {children}
    </HomePrefillContext.Provider>
  );
}

export function useHomePrefill() {
  const context = useContext(HomePrefillContext);

  if (!context) {
    throw new Error("useHomePrefill must be used within HomePrefillProvider");
  }

  return context;
}
