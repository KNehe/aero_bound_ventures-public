"use client";
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import useAuth from '@/store/auth';

/**
 * Hook to protect routes that require authentication
 * Redirects to home page if user is not authenticated
 */
export function useRequireAuth() {
  const router = useRouter();
  const { isAuthenticated, isHydrated } = useAuth();

  useEffect(() => {
    // Only redirect if store is hydrated and user is not authenticated
    if (isHydrated && !isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, isHydrated, router]);

  return isHydrated && isAuthenticated;
}

/**
 * Hook to protect admin routes
 * Redirects to home page if user is not authenticated or not an admin
 */
export function useRequireAdmin() {
  const router = useRouter();
  const { isAuthenticated, isHydrated, isAdmin } = useAuth();

  useEffect(() => {
    if (isHydrated && (!isAuthenticated || !isAdmin())) {
      router.push('/');
    }
  }, [isAuthenticated, isHydrated, isAdmin, router]);

  return isHydrated && isAuthenticated && isAdmin();
}

/**
 * Hook to redirect authenticated users (e.g., for login/signup pages)
 */
export function useRedirectIfAuthenticated(redirectTo: string = '/') {
  const router = useRouter();
  const { isAuthenticated, isHydrated } = useAuth();

  useEffect(() => {
    if (isHydrated && isAuthenticated) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, isHydrated, redirectTo, router]);
}
