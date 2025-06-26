import Image from "next/image";

export default function HeroSection() {
  return (
    <section className="relative flex flex-col md:flex-row items-center justify-between gap-8 px-6 py-16 md:py-24 overflow-hidden" style={{ backgroundImage: 'url(/aeroplane.jpg)', backgroundSize: 'cover', backgroundPosition: 'center' }}>
      {/* Overlay for readability */}
      <div className="absolute inset-0 bg-black/40 z-0" aria-hidden="true" />
      {/* Left: Text Content */}
      <div className="flex-1 max-w-xl z-10">
        <h1 className="text-4xl md:text-5xl font-extrabold text-white mb-6 leading-tight drop-shadow-lg">
          Book Flights <span className="text-blue-200">Your Way</span>
        </h1>
        <p className="text-lg md:text-xl text-gray-100 mb-8 drop-shadow">
          With Aero Bound Ventures, you choose: let our expert team handle your booking for a stress-free experience, or take control and book it yourself. Enjoy flexibility, great deals, and a personal touch every time you fly.
        </p>
        <div className="flex gap-4 mb-8">
          <a
            href="#contact"
            className="inline-block bg-blue-700 hover:bg-blue-800 text-white font-semibold px-6 py-3 rounded-lg shadow transition-colors text-lg drop-shadow"
          >
            We Book For You
          </a>
          <a
            href="#diy"
            className="inline-block border border-blue-200 text-blue-200 hover:bg-blue-50 hover:text-black font-semibold px-6 py-3 rounded-lg shadow transition-colors text-lg drop-shadow"
          >
            Do It Yourself
          </a>
        </div>
        <div className="mt-6 flex gap-4 items-center text-sm text-blue-100">
          <span className="inline-flex items-center gap-1">
            <svg className="w-5 h-5 text-blue-200" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
            Personalized Service
          </span>
          <span className="inline-flex items-center gap-1">
            <svg className="w-5 h-5 text-blue-200" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
            Best Deals
          </span>
        </div>
      </div>
      {/* Right: Illustration */}
      <div className="flex-1 flex justify-center items-center relative z-10">
        {/* Main image */}
        <div className="relative w-72 h-72 md:w-96 md:h-96">
          <Image
            src="/smiling_couple_airport2.webp"
            alt="Another smiling couple at the airport"
            fill
            className="object-cover rounded-xl drop-shadow-xl animate-float"
            priority
          />
          {/* Overlapping secondary image */}
          <div className="absolute -bottom-10 -right-10 w-40 h-40 md:w-52 md:h-52 border-4 border-white rounded-xl shadow-lg bg-white">
            <Image
              src="/smilling_couple_airport.webp"
              alt="Smiling couple at the airport"
              fill
              className="object-cover rounded-xl"
              priority={false}
            />
          </div>
        </div>
        {/* Decorative background shapes */}
        <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-100 rounded-full blur-2xl opacity-60 z-0" />
        <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-blue-200 rounded-full blur-2xl opacity-40 z-0" />
      </div>
    </section>
  );
}

// Add a simple float animation for the illustration
// Add this to your globals.css or tailwind config:
// @layer utilities {
//   .animate-float {
//     animation: float 3s ease-in-out infinite;
//   }
//   @keyframes float {
//     0%, 100% { transform: translateY(0); }
//     50% { transform: translateY(-16px); }
//   }
// } 