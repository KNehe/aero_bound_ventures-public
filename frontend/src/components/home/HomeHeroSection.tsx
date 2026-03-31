"use client";

import HeroSection from "@/components/HeroSection";
import { useHomePrefill } from "@/components/home/HomePrefillProvider";

export default function HomeHeroSection() {
  const { prefillDestination } = useHomePrefill();

  return <HeroSection prefillDestination={prefillDestination} />;
}
