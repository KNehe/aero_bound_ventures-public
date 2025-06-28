import HeroSection from '@/components/HeroSection';
import HowItWorksSection from '@/components/HowItWorksSection';
import PopularDestinationsSection from '@/components/PopularDestinationsSection';
import TestimonialsSection from '@/components/TestimonialsSection';
import ContactUsSection from '@/components/ContactUsSection';

export default function Home() {
  return (
    <main>
      <HeroSection />
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
  );
}
