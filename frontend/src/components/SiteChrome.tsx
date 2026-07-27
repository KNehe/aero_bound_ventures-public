"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ConstructionBanner from "@/components/ConstructionBanner";

type SiteChromeProps = {
  children: ReactNode;
};

export default function SiteChrome({ children }: SiteChromeProps) {
  const pathname = usePathname();
  const isHybridLanding = pathname === "/";

  if (isHybridLanding) {
    return <>{children}</>;
  }

  return (
    <>
      <div className="sticky top-0 z-50 w-full">
        <ConstructionBanner />
        <Navbar />
      </div>
      {children}
      <Footer />
    </>
  );
}
