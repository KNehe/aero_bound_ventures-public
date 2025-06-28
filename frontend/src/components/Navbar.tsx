"use client";
import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";

const navLinks = [
  { name: "Home", href: "#" },
  { name: "How it Works", href: "#how-it-works" },
  { name: "Destinations", href: "#destinations" },
  { name: "Testimonials", href: "#testimonials" },
  { name: "Contact", href: "#contact" },
];

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("");

  // Handle active section tracking (only on home page)
  useEffect(() => {
    if (pathname !== "/") return;
    
    const handleScroll = () => {
      const sections = navLinks.map(link => link.href.replace('#', ''));
      const current = sections.find(section => {
        if (section === '') return window.scrollY < 100;
        const element = document.getElementById(section);
        if (element) {
          const rect = element.getBoundingClientRect();
          return rect.top <= 100 && rect.bottom >= 100;
        }
        return false;
      });
      setActiveSection(current || '');
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [pathname]);

  // Smart navigation handler
  const handleNavigation = (href: string) => {
    const sectionId = href.replace('#', '');
    
    if (pathname === "/") {
      // On home page, scroll to section
      if (sectionId === '') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        const element = document.getElementById(sectionId);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth' });
        }
      }
    } else {
      // On other pages, navigate to home and then scroll
      router.push('/');
      // Use setTimeout to ensure navigation completes before scrolling
      setTimeout(() => {
        if (sectionId === '') {
          window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
          const element = document.getElementById(sectionId);
          if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
          }
        }
      }, 100);
    }
    
    setMenuOpen(false);
  };

  return (
    <nav className="sticky top-0 z-50 w-full bg-white shadow flex items-center justify-between px-6 py-3">
      {/* Left: Logo and Name */}
      <Link href="/" className="flex items-center gap-2">
        <Image src="/globe.svg" alt="Aero Bound Ventures Logo" width={32} height={32} />
        <span className="text-2xl font-extrabold text-blue-700 tracking-wide">Aero Bound Ventures</span>
      </Link>
      {/* Desktop Nav Links */}
      <div className="hidden md:flex gap-8">
        {navLinks.map((link) => {
          const isActive = pathname === "/" && (activeSection === link.href.replace('#', '') || 
                          (link.href === '#' && activeSection === ''));
          return (
            <button 
              key={link.name} 
              onClick={() => handleNavigation(link.href)}
              className={`font-medium transition-all duration-200 relative ${
                isActive 
                  ? 'text-blue-600' 
                  : 'text-gray-800 hover:text-blue-600'
              }`}
            >
              {link.name}
              {isActive && (
                <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-blue-600 rounded-full" />
              )}
            </button>
          );
        })}
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
        {navLinks.map((link) => {
          const isActive = pathname === "/" && (activeSection === link.href.replace('#', '') || 
                          (link.href === '#' && activeSection === ''));
          return (
            <button
              key={link.name}
              onClick={() => handleNavigation(link.href)}
              className={`font-medium text-lg transition-all duration-200 ${
                isActive 
                  ? 'text-blue-600' 
                  : 'text-gray-800 hover:text-blue-600'
              }`}
            >
              {link.name}
            </button>
          );
        })}
      </div>
    </nav>
  );
} 