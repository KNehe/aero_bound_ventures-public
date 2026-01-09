import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserInfo } from '@/types/auth';
import { ADMIN_GROUP_NAME } from '@/constants/auth';
import { apiClient, isUnauthorizedError } from '@/lib/api';

interface AuthState {
  userEmail: string | null;
  userInfo: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (userInfo: UserInfo) => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<boolean>;
  isAdmin: () => boolean;
}

const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      userEmail: null,
      userInfo: null,
      isAuthenticated: false,
      isLoading: false,
      
      setUser: (userInfo: UserInfo) => {
        set({ userEmail: userInfo.email, userInfo, isAuthenticated: true });
      },
      
      logout: async () => {
        try {
          await apiClient.post('/logout');
        } catch (error) {
          console.error('Logout error:', error);
        }
        set({ userEmail: null, userInfo: null, isAuthenticated: false });
      },
      
      checkAuth: async () => {
        try {
          set({ isLoading: true });
          const userInfo = await apiClient.get<UserInfo>('/me/');
          set({ userEmail: userInfo.email, userInfo, isAuthenticated: true });
          return true;
        } catch (error) {
          if (isUnauthorizedError(error)) {
            set({ userEmail: null, userInfo: null, isAuthenticated: false });
          }
          return false;
        } finally {
          set({ isLoading: false });
        }
      },
      
      isAdmin: () => {
        const state = get();
        return state.userInfo?.groups?.some(group => group.name === ADMIN_GROUP_NAME) ?? false;
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        userEmail: state.userEmail,
        userInfo: state.userInfo,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export default useAuth;
