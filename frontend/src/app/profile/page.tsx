"use client";

import Image from "next/image";
import { useState, ChangeEvent, FormEvent } from "react";
import useAuth from '@/store/auth';
import { MIN_PASSWORD_LENGTH } from '@/constants/auth';
import { apiClient, isUnauthorizedError, ApiClientError } from '@/lib/api';
import { useRouter } from 'next/navigation';

interface FormData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

interface FormErrors {
  old_password?: string;
  new_password?: string;
  confirm_password?: string;
}

export default function ProfilePage() {
  const userEmail = useAuth((state) => state.userEmail);
  const logout = useAuth((state) => state.logout);
  const router = useRouter();

  const [formData, setFormData] = useState<FormData>({
    old_password: "",
    new_password: "",
    confirm_password: ""
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [messageType, setMessageType] = useState<'success' | 'error' | null>(null);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: "" }));
    }
  };

  const validateForm = (): FormErrors => {
    const newErrors: FormErrors = {};
    if (!formData.old_password) newErrors.old_password = "Old password is required";
    if (!formData.new_password) {
      newErrors.new_password = "New password is required";
    } else if (formData.new_password.length < MIN_PASSWORD_LENGTH) {
      newErrors.new_password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters`;
    } else if (!/[A-Z]/.test(formData.new_password)) {
      newErrors.new_password = "Password must contain at least one uppercase letter";
    } else if (!/[a-z]/.test(formData.new_password)) {
      newErrors.new_password = "Password must contain at least one lowercase letter";
    } else if (!/[0-9]/.test(formData.new_password)) {
      newErrors.new_password = "Password must contain at least one digit";
    } else if (!/[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(formData.new_password)) {
      newErrors.new_password = "Password must contain at least one special character";
    }
    if (formData.new_password !== formData.confirm_password) newErrors.confirm_password = "Passwords do not match";
    return newErrors;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setIsSubmitting(true);
    setMessage(null); // Clear previous messages
    try {
      await apiClient.post('/change-password/', {
        old_password: formData.old_password,
        new_password: formData.new_password,
        confirm_password: formData.confirm_password,
      });

      setMessage("Password changed successfully! Redirecting to login...");
      setMessageType('success');
      setFormData({ old_password: "", new_password: "", confirm_password: "" });

      // Session is invalidated by the backend, logout and redirect
      setTimeout(async () => {
        await logout();
        router.push('/auth/login');
      }, 2000);
    } catch (error) {
      console.error('Password change error:', error);
      if (isUnauthorizedError(error)) {
        await logout();
        router.push('/auth/login?redirect=/profile');
        return;
      }
      if (error instanceof ApiClientError) {
        setMessage(error.detail || "Failed to change password");
      } else {
        setMessage(error instanceof Error ? error.message : "Failed to change password. Please try again.");
      }
      setMessageType('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 py-12 px-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        {/* Avatar and Email */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-24 h-24 mb-4 rounded-full overflow-hidden border-4 border-blue-500">
            <Image src="/logo.png" alt="User Avatar" width={96} height={96} className="object-contain" />
          </div>
          <div className="text-xl font-semibold text-gray-800">{userEmail}</div>
        </div>

        {/* Password Change Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <h2 className="text-2xl font-bold text-center text-gray-900">Change Password</h2>

          {message && (
            <div className={`p-4 rounded-md ${messageType === 'success' ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-red-100 text-red-800 border border-red-200'}`}>
              {message}
            </div>
          )}

          <div>
            <label htmlFor="old_password" className="block text-sm font-medium text-gray-700 mb-1">
              Old Password
            </label>
            <div className="relative">
              <input
                type={showOldPassword ? "text" : "password"}
                id="old_password"
                name="old_password"
                value={formData.old_password}
                onChange={handleChange}
                className="w-full px-3 py-2 pr-10 border border-gray-300 text-gray-900 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-500"
                placeholder="Enter your old password"
              />
              <button
                type="button"
                onClick={() => setShowOldPassword(!showOldPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
              >
                {showOldPassword ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" /></svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                )}
              </button>
            </div>
            {errors.old_password && <p className="mt-1 text-sm text-red-600">{errors.old_password}</p>}
          </div>

          <div>
            <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-1">
              New Password
            </label>
            <div className="relative">
              <input
                type={showNewPassword ? "text" : "password"}
                id="new_password"
                name="new_password"
                value={formData.new_password}
                onChange={handleChange}
                className="w-full px-3 py-2 pr-10 border border-gray-300 text-gray-900 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-500"
                placeholder="Enter your new password"
              />
              <button
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
              >
                {showNewPassword ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" /></svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                )}
              </button>
            </div>
            {errors.new_password && <p className="mt-1 text-sm text-red-600">{errors.new_password}</p>}
          </div>

          <div>
            <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-1">
              Confirm New Password
            </label>
            <div className="relative">
              <input
                type={showConfirmPassword ? "text" : "password"}
                id="confirm_password"
                name="confirm_password"
                value={formData.confirm_password}
                onChange={handleChange}
                className="w-full px-3 py-2 pr-10 border border-gray-300 text-gray-900 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-500"
                placeholder="Confirm your new password"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
              >
                {showConfirmPassword ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" /></svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                )}
              </button>
            </div>
            {errors.confirm_password && <p className="mt-1 text-sm text-red-600">{errors.confirm_password}</p>}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? "Changing Password..." : "Change Password"}
          </button>
        </form>
      </div>
    </div>
  );
}
