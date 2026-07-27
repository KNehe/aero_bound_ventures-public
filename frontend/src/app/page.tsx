import type { Metadata } from "next";
import HybridLandingPage from "@/components/hybrid/HybridLandingPage";

export const metadata: Metadata = {
  title: "Aero Bound Ventures | Air Travel + Software Development",
  description:
    "Aero Bound Ventures combines dependable air travel support with custom software development for people and growing businesses.",
};

export default function Home() {
  return <HybridLandingPage />;
}
