"use client";
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import useAuth from '@/store/auth';

export default function MyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, isAdmin } = useAuth();

  useEffect(() => {
    // Check if user is authenticated
    if (!isAuthenticated) {
      router.push('/auth/login?redirect=/my');
      return;
    }

    // If user is admin, they might want to go to admin dashboard instead
    // but we'll allow them to access regular user pages too
  }, [isAuthenticated, router]);

  // If not authenticated, don't render anything
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
