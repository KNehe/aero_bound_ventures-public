import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserInfo } from '@/types/auth';

interface AuthState {
  token: string | null;
  userEmail: string | null;
  userInfo: UserInfo | null;
  isAuthenticated: boolean;
  login: (token: string, userInfo: UserInfo) => void;
  logout: () => void;
  isAdmin: () => boolean;
}

const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      userEmail: null,
      userInfo: null,
      isAuthenticated: false,
      login: (token: string, userInfo: UserInfo) => {
        set({ token, userEmail: userInfo.email, userInfo, isAuthenticated: true });
        // Also store in localStorage for backward compatibility
        localStorage.setItem('access_token', token);
        localStorage.setItem('user_email', userInfo.email);
        localStorage.setItem('user_info', JSON.stringify(userInfo));
      },
      logout: () => {
        set({ token: null, userEmail: null, userInfo: null, isAuthenticated: false });
        // Also clear localStorage
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_email');
        localStorage.removeItem('user_info');
      },
      isAdmin: () => {
        const state = get();
        return state.userInfo?.groups?.some(group => group.name.toLowerCase() === 'admin') ?? false;
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);

export default useAuth;
