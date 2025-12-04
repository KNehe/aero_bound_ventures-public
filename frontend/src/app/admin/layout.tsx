"use client";
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import useAuth from '@/store/auth';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, isAdmin } = useAuth();

  useEffect(() => {
    // Check if user is authenticated
    if (!isAuthenticated) {
      router.push('/auth/login?redirect=/admin');
      return;
    }

    // Check if user is admin
    if (!isAdmin()) {
      router.push('/');
      return;
    }
  }, [isAuthenticated, isAdmin, router]);

  // If not authenticated or not admin, don't render anything
  if (!isAuthenticated || !isAdmin()) {
    return null;
  }

  return <>{children}</>;
}
