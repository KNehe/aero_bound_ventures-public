import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import ConstructionBanner from '@/components/ConstructionBanner';
import NavigationProgress from '@/components/NavigationProgress';


const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Aero Bound Ventures | Seamless Travel Services",
  description: "Discover premium travel services with Aero Bound Ventures. We specialize in air ticketing, hotel bookings, airport transfers, travel insurance, car rentals, tour & honeymoon packages, as well as passport and visa processing.",
  icons: {
    icon: [
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },
  manifest: "/site.webmanifest",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <Suspense fallback={null}>
          <NavigationProgress />
        </Suspense>
        <div className="sticky top-0 z-50 w-full">
          <ConstructionBanner />
          <Navbar />
        </div>
        {children}


        <Footer />
      </body>
    </html>
  );
}
