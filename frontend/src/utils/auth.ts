/**
 * Authentication utility functions
 * These functions work with both Zustand store and localStorage
 */

import useAuth from '@/store/auth';

/**
 * Get authentication token from localStorage
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

/**
 * Get user email from localStorage
 */
export function getUserEmail(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('user_email');
}

/**
 * Clear authentication data (use the store's logout method instead)
 * @deprecated Use useAuth().logout() instead
 */
export function clearAuth(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('user_email');
}

/**
 * Set authentication data (use the store's login method instead)
 * @deprecated Use useAuth().login(token, email) instead
 */
export function setAuth(token: string, email: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('access_token', token);
  localStorage.setItem('user_email', email);
}
