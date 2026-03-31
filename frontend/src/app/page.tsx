import HowItWorksSection from '@/components/HowItWorksSection';
import PopularDestinationsSection from '@/components/PopularDestinationsSection';
import TestimonialsSection from '@/components/TestimonialsSection';
import ContactUsSection from '@/components/ContactUsSection';
import HomeHeroSection from '@/components/home/HomeHeroSection';
import { HomePrefillProvider } from '@/components/home/HomePrefillProvider';

export default function Home() {
  return (
    <HomePrefillProvider>
      <main>
        <HomeHeroSection />
        <div id="how-it-works">
          <HowItWorksSection />
        </div>
        <div id="destinations">
          <PopularDestinationsSection />
        </div>
        <div id="testimonials">
          <TestimonialsSection />
        </div>
        <div id="contact">
          <ContactUsSection />
        </div>
      </main>
    </HomePrefillProvider>
  );
}
