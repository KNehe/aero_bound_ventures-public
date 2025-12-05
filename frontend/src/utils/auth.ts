/**
 * Authentication utility functions
 * These functions work with both Zustand store and localStorage
 */

import { UserInfo } from '@/types/auth';
import { ADMIN_GROUP_NAME } from '@/constants/auth';

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
 * Get user info from localStorage
 */
export function getUserInfo(): UserInfo | null {
  if (typeof window === 'undefined') return null;
  const userInfoStr = localStorage.getItem('user_info');
  if (!userInfoStr) return null;
  try {
    return JSON.parse(userInfoStr);
  } catch {
    return null;
  }
}

/**
 * Check if user is admin
 */
export function isUserAdmin(): boolean {
  const userInfo = getUserInfo();
  if (!userInfo) return false;
  return userInfo.groups?.some(group => group.name === ADMIN_GROUP_NAME) ?? false;
}

/**
 * Check if user has a specific permission
 */
export function hasPermission(codename: string): boolean {
  const userInfo = getUserInfo();
  if (!userInfo) return false;
  
  // Check all permissions across all groups
  for (const group of userInfo.groups) {
    if (group.permissions.some(perm => perm.codename === codename)) {
      return true;
    }
  }
  return false;
}

/**
 * Check if user belongs to a specific group
 */
export function hasGroup(groupName: string): boolean {
  const userInfo = getUserInfo();
  if (!userInfo) return false;
  return userInfo.groups?.some(group => group.name.toLowerCase() === groupName.toLowerCase()) ?? false;
}

/**
 * Clear authentication data (use the store's logout method instead)
 * @deprecated Use useAuth().logout() instead
 */
export function clearAuth(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('user_email');
  localStorage.removeItem('user_info');
}

/**
 * Set authentication data (use the store's login method instead)
 * @deprecated Use useAuth().login(token, userInfo) instead
 */
export function setAuth(token: string, email: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('access_token', token);
  localStorage.setItem('user_email', email);
}
