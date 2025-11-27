"use client";
import HeroSection from '@/components/HeroSection';
import HowItWorksSection from '@/components/HowItWorksSection';
import PopularDestinationsSection from '@/components/PopularDestinationsSection';
import TestimonialsSection from '@/components/TestimonialsSection';
import ContactUsSection from '@/components/ContactUsSection';
import { useState } from 'react';

export default function Home() {
  const [prefillDestination, setPrefillDestination] = useState<string>('');

  return (
    <main>
      <HeroSection prefillDestination={prefillDestination} />
      <div id="how-it-works">
      <HowItWorksSection />
      </div>
      <div id="destinations">
        <PopularDestinationsSection setPrefillDestination={setPrefillDestination} />
      </div>
      <div id="testimonials">
        <TestimonialsSection />
      </div>
      <div id="contact">
        <ContactUsSection />
      </div>
    </main>
  );
}
