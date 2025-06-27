import { FaRegPaperPlane, FaRegListAlt, FaRegCheckCircle, FaRegSmile } from 'react-icons/fa';

const steps = [
  {
    icon: <FaRegListAlt className="text-blue-600 w-10 h-10 mb-2" />,
    title: 'Share Your Travel Plans',
    desc: 'Tell us your destination, dates, and preferences in a quick form or chat.'
  },
  {
    icon: <FaRegPaperPlane className="text-blue-600 w-10 h-10 mb-2" />,
    title: 'Get Personalized Options',
    desc: 'We search for the best flights and deals tailored just for you.'
  },
  {
    icon: <FaRegCheckCircle className="text-blue-600 w-10 h-10 mb-2" />,
    title: 'Choose & Confirm',
    desc: 'Pick your favorite option and confirm. We handle the booking, or you do it yourself.'
  },
  {
    icon: <FaRegSmile className="text-blue-600 w-10 h-10 mb-2" />,
    title: 'Fly with Confidence',
    desc: 'Enjoy your trip, knowing you got the best deal and service.'
  },
];

export default function HowItWorksSection() {
  return (
    <section className="w-full bg-white py-20 px-4 md:px-0">
      <div className="max-w-5xl mx-auto text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-extrabold text-blue-900 mb-4">How It Works</h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Booking with Aero Bound Ventures is simple and personal. Here's how we make your travel easy:
        </p>
      </div>
      <div className="flex flex-col md:flex-row justify-between items-stretch gap-10 md:gap-6 max-w-5xl mx-auto">
        {steps.map((step, i) => (
          <div key={step.title} className="flex-1 bg-blue-50 rounded-2xl shadow p-8 flex flex-col items-center text-center transition-transform hover:-translate-y-2 hover:shadow-lg">
            <div className="mb-3">{step.icon}</div>
            <h3 className="text-xl font-bold text-blue-800 mb-2">{step.title}</h3>
            <p className="text-gray-600 text-base">{step.desc}</p>
            {i < steps.length - 1 && (
              <div className="hidden md:block absolute right-0 top-1/2 transform -translate-y-1/2 translate-x-1/2 w-8 h-1 bg-blue-200 rounded-full" />
            )}
          </div>
        ))}
      </div>
    </section>
  );
} 