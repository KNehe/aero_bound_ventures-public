"use client";
import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import useAuth from "@/store/auth";
import NotificationBell from "./NotificationBell";

const navLinks = [
  { name: "Home", href: "#" },
  { name: "How It Works", href: "#how-it-works" },
  { name: "Destinations", href: "#destinations" },
  { name: "Testimonials", href: "#testimonials" },
  { name: "Contact", href: "#contact" },
];

const brandName = "Aero Bound Ventures";
const brandTagline = "Flights & Travel Concierge";
const travelHomePath = "/travel";

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("");

  // Use Zustand store for auth state
  const { isAuthenticated, userEmail, logout, isAdmin } = useAuth();

  // Handle active section tracking (only on home page)
  useEffect(() => {
    if (pathname !== travelHomePath) return;

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

    if (pathname === travelHomePath) {
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
      router.push(travelHomePath);
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

  const handleLogout = () => {
    logout();
    router.push(travelHomePath);
    setMenuOpen(false);
  };

  return (
    <nav className="relative isolate z-50 flex w-full items-center justify-between border-b border-white/60 bg-white/72 px-4 py-2 shadow-[0_14px_40px_rgba(15,23,42,0.08)] ring-1 ring-slate-200/60 backdrop-blur-xl supports-[backdrop-filter]:bg-white/58 md:px-6">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[linear-gradient(115deg,rgba(255,255,255,0.96)_0%,rgba(240,249,255,0.92)_34%,rgba(224,242,254,0.82)_65%,rgba(219,234,254,0.78)_100%)]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -left-16 top-[-3.5rem] h-24 w-40 rounded-full bg-cyan-200/45 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute right-[-2.5rem] top-1/2 h-28 w-44 -translate-y-1/2 rounded-full bg-blue-300/30 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-white/90"
      />
      {/* Left: Logo and Name */}
      <Link href={travelHomePath} className="relative z-10 flex min-w-0 flex-1 items-center gap-2.5 md:flex-none md:gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/90 shadow-[0_10px_24px_rgba(14,116,144,0.16)] ring-1 ring-sky-100/80 md:h-11 md:w-11">
          <Image src="/logo.png" alt="AeroBound logo" width={34} height={34} className="object-contain" />
        </div>
        <div className="flex min-w-0 flex-col leading-none">
          <span className="truncate text-base font-black tracking-[-0.04em] text-slate-900 sm:text-lg md:text-[1.35rem]">
            {brandName}
          </span>
          <span className="mt-1 hidden text-[0.68rem] font-semibold uppercase tracking-[0.24em] text-sky-700/80 md:block">
            {brandTagline}
          </span>
        </div>
      </Link>
      {/* Desktop Nav Links */}
      <div className="relative z-10 hidden items-center gap-8 md:flex">
        {navLinks.map((link) => {
          const isActive = pathname === travelHomePath && (activeSection === link.href.replace('#', '') ||
            (link.href === '#' && activeSection === ''));
          return (
            <button
              key={link.name}
              onClick={() => handleNavigation(link.href)}
              className={`relative text-sm font-semibold tracking-[0.02em] transition-all duration-200 ${isActive
                ? 'text-sky-700'
                : 'text-slate-700 hover:text-sky-700'
                }`}
            >
              {link.name}
              {isActive && (
                <div className="absolute -bottom-2 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full bg-sky-600" />
              )}
            </button>
          );
        })}
        {/* Bookings/Dashboard Link - Only show when authenticated */}
        {isAuthenticated && (
          isAdmin() ? (
            <Link
              href="/admin"
              className="ml-2 rounded-full border border-sky-200/80 bg-white/75 px-4 py-2 text-sm font-semibold text-slate-700 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] transition-colors hover:border-sky-300 hover:text-sky-700"
            >
              Control Center
            </Link>
          ) : (
            <Link
              href="/my"
              className="ml-2 rounded-full border border-sky-200/80 bg-white/75 px-4 py-2 text-sm font-semibold text-slate-700 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] transition-colors hover:border-sky-300 hover:text-sky-700"
            >
              My Trips
            </Link>
          )
        )}
        {/* Auth Links */}
        {isAuthenticated ? (
          <div className="ml-2 flex items-center gap-3">
            <NotificationBell />
            <button
              onClick={() => router.push('/profile')}
              className="text-sm font-medium text-slate-600 transition-colors hover:text-sky-700"
            >
              {userEmail}
            </button>
            <button
              onClick={handleLogout}
              className="rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:border-red-200 hover:bg-red-50 hover:text-red-600"
            >
              Sign Out
            </button>
          </div>
        ) : (
          <Link
            href="/auth/login"
            className="ml-2 rounded-full bg-[linear-gradient(135deg,#0f172a_0%,#0f3f75_45%,#0284c7_100%)] px-5 py-2 text-sm font-semibold text-white shadow-[0_12px_28px_rgba(2,132,199,0.28)] transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-[0_16px_32px_rgba(2,132,199,0.32)]"
          >
            Sign In
          </Link>
        )}
      </div>
      {/* Hamburger Icon */}
      <button
        className="relative z-10 ml-3 shrink-0 rounded-full border border-sky-100 bg-white/80 p-2 text-2xl text-slate-900 shadow-sm md:hidden"
        aria-label="Toggle menu"
        onClick={() => setMenuOpen((open) => !open)}
      >
        &#9776;
      </button>
      {/* Mobile Menu */}
      <div
        className={`fixed inset-0 z-50 transition-opacity duration-300 md:hidden ${menuOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0'}`}
      >
        <button
          className="absolute inset-0 bg-slate-950/24 backdrop-blur-[2px]"
          aria-label="Close menu"
          onClick={() => setMenuOpen(false)}
        />
        <div
          className={`absolute inset-y-0 right-0 flex h-dvh min-h-screen w-3/4 max-w-xs flex-col items-start gap-8 overflow-y-auto border-l border-sky-100 bg-[linear-gradient(180deg,rgba(255,255,255,0.99)_0%,rgba(240,249,255,0.99)_100%)] px-8 py-20 shadow-2xl transition-transform duration-300 ${menuOpen ? 'translate-x-0' : 'translate-x-full'}`}
        >
          <button
            className="absolute right-4 top-4 text-2xl text-slate-900"
            aria-label="Close menu"
            onClick={() => setMenuOpen(false)}
          >
            &times;
          </button>
          {navLinks.map((link) => {
            const isActive = pathname === travelHomePath && (activeSection === link.href.replace('#', '') ||
              (link.href === '#' && activeSection === ''));
            return (
              <button
                key={link.name}
                onClick={() => handleNavigation(link.href)}
                className={`text-lg font-semibold transition-all duration-200 ${isActive
                  ? 'text-sky-700'
                  : 'text-slate-800 hover:text-sky-700'
                  }`}
              >
                {link.name}
              </button>
            );
          })}
          {/* Bookings/Dashboard Link - Only show when authenticated */}
          {isAuthenticated && (
            isAdmin() ? (
              <Link
                href="/admin"
                className="rounded-full border border-sky-200/80 bg-white/80 px-4 py-2 text-lg font-semibold text-slate-800 transition-colors hover:border-sky-300 hover:text-sky-700"
              >
                Control Center
              </Link>
            ) : (
              <Link
                href="/my"
                className="rounded-full border border-sky-200/80 bg-white/80 px-4 py-2 text-lg font-semibold text-slate-800 transition-colors hover:border-sky-300 hover:text-sky-700"
              >
                My Trips
              </Link>
            )
          )}
          {/* Auth Links */}
          {isAuthenticated ? (
            <div className="flex flex-col gap-3">
              {/* Notification Bell for Mobile */}
              <div className="flex items-center gap-2">
                <NotificationBell />
                <span className="text-sm font-medium text-slate-600">Notifications</span>
              </div>
              <button
                onClick={() => router.push('/profile')}
                className="text-sm font-medium text-slate-600 transition-colors hover:text-sky-700"
              >
                {userEmail}
              </button>
              <button
                onClick={handleLogout}
                className="rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-lg font-semibold text-slate-700 transition-colors hover:border-red-200 hover:bg-red-50 hover:text-red-600"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <Link
              href="/auth/login"
              className="rounded-full bg-[linear-gradient(135deg,#0f172a_0%,#0f3f75_45%,#0284c7_100%)] px-5 py-2 text-lg font-semibold text-white shadow-[0_12px_28px_rgba(2,132,199,0.28)] transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-[0_16px_32px_rgba(2,132,199,0.32)]"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
