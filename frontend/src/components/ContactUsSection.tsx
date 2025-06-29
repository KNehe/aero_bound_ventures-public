import { FaWhatsapp } from 'react-icons/fa';

export default function ContactUsSection() {
  return (
    <section className="w-full bg-gray-50 py-20 px-4 md:px-0">
      <div className="max-w-2xl mx-auto text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-extrabold text-blue-900 mb-4">Contact Us</h2>
        <p className="text-lg text-gray-600 max-w-xl mx-auto">
          Have questions, need help, or want to share feedback? Fill out the form below or email us at
          <a href="mailto:support@aerobound.com" className="text-blue-600 underline ml-1">support@aerobound.com</a>.
        </p>
      </div>
      <form className="max-w-md mx-auto bg-white rounded-2xl shadow p-6 flex flex-col gap-4">
        <div className="flex flex-col text-left">
          <label htmlFor="name" className="text-blue-900 font-semibold mb-2">Name</label>
          <input
            type="text"
            id="name"
            name="name"
            required
            className="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 placeholder-gray-700"
            placeholder="Your Name"
          />
        </div>
        <div className="flex flex-col text-left">
          <label htmlFor="email" className="text-blue-900 font-semibold mb-2">Email</label>
          <input
            type="email"
            id="email"
            name="email"
            required
            className="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-gray-900 placeholder-gray-700"
            placeholder="you@email.com"
          />
        </div>
        <div className="flex flex-col text-left">
          <label htmlFor="message" className="text-blue-900 font-semibold mb-2">Message</label>
          <textarea
            id="message"
            name="message"
            required
            rows={4}
            className="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none text-gray-900 placeholder-gray-700"
            placeholder="How can we help you?"
          />
        </div>
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400 text-base"
        >
          Send Message
        </button>
      </form>
      <div className="max-w-md mx-auto flex flex-col items-center mt-6">
        <span className="text-gray-700 mb-2 text-sm">Or reach us instantly:</span>
        <a
          href="https://wa.me/1234567890"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-400 text-base shadow"
        >
          <FaWhatsapp className="text-xl" /> Contact us on WhatsApp
        </a>
      </div>
    </section>
  );
} 