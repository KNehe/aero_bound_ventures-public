import { FaWhatsapp } from 'react-icons/fa';

const whatsappNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER;


export default function ContactUsSection() {
  return (
    <section className="w-full bg-gray-50 py-20 px-4 md:px-0">
      <div className="max-w-2xl mx-auto text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-extrabold text-blue-900 mb-4">Contact Us</h2>
        <p className="text-lg text-gray-600 max-w-xl mx-auto">
          Have questions, need help, or want to share feedback? Email us at
          <a href="mailto:aeroboundventures@gmail.com" className="text-blue-600 underline ml-1">aeroboundventures@gmail.com</a>.
        </p>
      </div>
      <div className="max-w-md mx-auto flex flex-col items-center mt-6">
        <span className="text-gray-700 mb-2 text-sm">Or reach us instantly:</span>
        <a
          href={`https://wa.me/${whatsappNumber}`}
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