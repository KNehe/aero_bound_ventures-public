import HeroSection from '../components/HeroSection';
import HowItWorksSection from '../components/HowItWorksSection';
import PopularDestinationsSection from '../components/PopularDestinationsSection';
import TestimonialsSection from '../components/TestimonialsSection';

export default function Home() {
  return (
    <main>
      <HeroSection />
      <HowItWorksSection />
      <PopularDestinationsSection />
      <TestimonialsSection />
    </main>
  );
}
