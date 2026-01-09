/**
 * Authentication utility functions
 * 
 * Note: With HTTP-only cookies, token management is handled by the browser.
 * These utilities work with the Zustand auth store for user info.
 */

import { UserInfo } from '@/types/auth';
import { ADMIN_GROUP_NAME } from '@/constants/auth';

/**
 * Check if user is admin based on user info
 */
export function isUserAdmin(userInfo: UserInfo | null): boolean {
  if (!userInfo) return false;
  return userInfo.groups?.some(group => group.name === ADMIN_GROUP_NAME) ?? false;
}

/**
 * Check if user has a specific permission
 */
export function hasPermission(userInfo: UserInfo | null, codename: string): boolean {
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
export function hasGroup(userInfo: UserInfo | null, groupName: string): boolean {
  if (!userInfo) return false;
  return userInfo.groups?.some(group => group.name.toLowerCase() === groupName.toLowerCase()) ?? false;
}
