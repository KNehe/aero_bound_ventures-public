import { FaTwitter, FaInstagram, FaFacebookF } from 'react-icons/fa';

const navLinks = [
  { name: 'Home', href: '/' },
  { name: 'Destinations', href: '#' },
  { name: 'About', href: '#' },
  { name: 'Contact', href: '#' },
];

export default function Footer() {
  return (
    <footer className="w-full bg-blue-900 text-white py-10 px-4">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center md:items-start justify-between gap-8">
        {/* Brand */}
        <div className="mb-6 md:mb-0 flex flex-col items-center md:items-start">
          <span className="text-2xl font-extrabold tracking-tight">Aero Bound Ventures</span>
          <span className="text-blue-200 text-sm mt-2">Your journey, our passion.</span>
        </div>
        {/* Navigation */}
        <nav className="mb-6 md:mb-0">
          <ul className="flex flex-col md:flex-row gap-4 md:gap-8 items-center">
            {navLinks.map(link => (
              <li key={link.name}>
                <a
                  href={link.href}
                  className="text-blue-100 hover:text-white transition-colors text-base font-medium"
                >
                  {link.name}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
      <div className="mt-8 text-center text-blue-200 text-xs">
        &copy; {new Date().getFullYear()} Aero Bound Ventures. All rights reserved.
      </div>
    </footer>
  );
} 