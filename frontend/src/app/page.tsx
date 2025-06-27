import HeroSection from '../components/HeroSection';
import HowItWorksSection from '../components/HowItWorksSection';
import PopularDestinationsSection from '../components/PopularDestinationsSection';
import TestimonialsSection from '../components/TestimonialsSection';
import ContactUsSection from '../components/ContactUsSection';

export default function Home() {
  return (
    <main>
      <HeroSection />
      <HowItWorksSection />
      <PopularDestinationsSection />
      <TestimonialsSection />
      <ContactUsSection />
    </main>
  );
}
