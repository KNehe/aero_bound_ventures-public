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
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  return isAuthenticated;
}

/**
 * Hook to protect admin routes
 * Redirects to home page if user is not authenticated or not an admin
 */
export function useRequireAdmin() {
  const router = useRouter();
  const { isAuthenticated, isAdmin } = useAuth();

  useEffect(() => {
    if (!isAuthenticated || !isAdmin()) {
      router.push('/');
    }
  }, [isAuthenticated, isAdmin, router]);

  return isAuthenticated && isAdmin();
}

/**
 * Hook to redirect authenticated users (e.g., for login/signup pages)
 */
export function useRedirectIfAuthenticated(redirectTo: string = '/') {
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, redirectTo, router]);
}
