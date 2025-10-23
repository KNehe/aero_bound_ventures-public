import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  userEmail: string | null;
  isAuthenticated: boolean;
  login: (token: string, email: string) => void;
  logout: () => void;
}

const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userEmail: null,
      isAuthenticated: false,
      login: (token: string, email: string) => {
        set({ token, userEmail: email, isAuthenticated: true });
        // Also store in localStorage for backward compatibility
        localStorage.setItem('access_token', token);
        localStorage.setItem('user_email', email);
      },
      logout: () => {
        set({ token: null, userEmail: null, isAuthenticated: false });
        // Also clear localStorage
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_email');
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);

export default useAuth;
