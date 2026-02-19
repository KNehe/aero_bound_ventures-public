"use client";
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import useAuth from '@/store/auth';

export default function ProfileLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, isHydrated } = useAuth();

  useEffect(() => {
    // Check if user is authenticated
    if (isHydrated && !isAuthenticated) {
      router.push('/auth/login?redirect=/profile');
      return;
    }
  }, [isAuthenticated, isHydrated, router]);

  // If not authenticated, don't render anything
  if (!isHydrated || !isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
