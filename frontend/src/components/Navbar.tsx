"use client";
import React, { useState } from "react";
import Image from "next/image";
import Link from "next/link";

const navLinks = [
  { name: "Home", href: "#" },
  { name: "How it Works", href: "#how-it-works" },
  { name: "Destinations", href: "#destinations" },
  { name: "Testimonials", href: "#testimonials" },
  { name: "Contact", href: "#contact" },
];

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 w-full bg-white shadow flex items-center justify-between px-6 py-3">
      {/* Left: Logo and Name */}
      <div className="flex items-center gap-2">
        <Image src="/globe.svg" alt="Aero Bound Ventures Logo" width={32} height={32} />
        <span className="text-2xl font-extrabold text-blue-700 tracking-wide">Aero Bound Ventures</span>
      </div>
      {/* Desktop Nav Links */}
      <div className="hidden md:flex gap-8">
        {navLinks.map((link) => (
          <Link key={link.name} href={link.href} className="text-gray-800 font-medium hover:text-blue-600 transition-colors">
            {link.name}
          </Link>
        ))}
      </div>
      {/* Hamburger Icon */}
      <button
        className="md:hidden text-2xl ml-2 text-black"
        aria-label="Toggle menu"
        onClick={() => setMenuOpen((open) => !open)}
      >
        &#9776;
      </button>
      {/* Mobile Menu */}
      <div
        className={`fixed top-0 right-0 h-full bg-white shadow-lg flex flex-col items-start gap-8 px-8 py-20 transition-transform duration-300 z-50 w-3/4 max-w-xs md:hidden ${menuOpen ? 'translate-x-0' : 'translate-x-full'}`}
      >
        <button
          className="absolute top-4 right-4 text-2xl text-black"
          aria-label="Close menu"
          onClick={() => setMenuOpen(false)}
        >
          &times;
        </button>
        {navLinks.map((link) => (
          <Link
            key={link.name}
            href={link.href}
            className="text-gray-800 font-medium text-lg hover:text-blue-600 transition-colors"
            onClick={() => setMenuOpen(false)}
          >
            {link.name}
          </Link>
        ))}
      </div>
    </nav>
  );
} 