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
  const { isAuthenticated, isAdmin, isHydrated } = useAuth();

  // Authentication and authorization check
  useEffect(() => {
    if (!isHydrated) return;

    if (!isAuthenticated) {
      router.push('/auth/login?redirect=/admin');
      return;
    }

    if (!isAdmin()) {
      router.push('/');
      return;
    }
  }, [isHydrated, isAuthenticated, isAdmin, router]);

  // Show loading while checking authentication
  if (!isHydrated || !isAuthenticated || !isAdmin()) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
