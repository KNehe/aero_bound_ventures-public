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
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    // Check if user is authenticated
    if (!isAuthenticated) {
      router.push('/auth/login?redirect=/profile');
      return;
    }
  }, [isAuthenticated, router]);

  // If not authenticated, don't render anything
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
