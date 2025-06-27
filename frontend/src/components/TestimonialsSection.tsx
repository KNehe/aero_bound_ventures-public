const testimonials = [
  {
    name: 'Ava Martinez',
    location: 'Barcelona, Spain',
    quote:
      'Aero Bound Ventures made my honeymoon unforgettable! The booking was seamless and the flight options were perfect for our budget. Highly recommended!',
    image: 'https://randomuser.me/api/portraits/women/44.jpg',
  },
  {
    name: 'Liam Chen',
    location: 'Vancouver, Canada',
    quote:
      'I was amazed by the personalized service. They found me a last-minute deal to Tokyo and even gave me tips for my first solo trip. Will book again!',
    image: 'https://randomuser.me/api/portraits/men/32.jpg',
  },
  {
    name: 'Priya Patel',
    location: 'Mumbai, India',
    quote:
      'The best travel experience I have ever had! The team was so responsive and made sure every detail was taken care of. Thank you, Aero Bound!',
    image: 'https://randomuser.me/api/portraits/women/68.jpg',
  },
];

export default function TestimonialsSection() {
  return (
    <section className="w-full bg-white py-20 px-4 md:px-0">
      <div className="max-w-4xl mx-auto text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-extrabold text-blue-900 mb-4">What Our Travelers Say</h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Real stories from real adventurers who trusted Aero Bound Ventures for their journeys.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        {testimonials.map((t, i) => (
          <div
            key={i}
            className="bg-gray-50 rounded-2xl shadow p-8 flex flex-col items-center text-center transition-transform hover:-translate-y-2 hover:shadow-lg"
          >
            <img
              src={t.image}
              alt={`Photo of ${t.name}`}
              className="w-20 h-20 rounded-full object-cover mb-4 border-4 border-blue-100 shadow"
              loading="lazy"
            />
            <blockquote className="text-blue-800 italic mb-4">“{t.quote}”</blockquote>
            <div className="font-bold text-blue-900">{t.name}</div>
            <div className="text-sm text-gray-500">{t.location}</div>
          </div>
        ))}
      </div>
    </section>
  );
} 