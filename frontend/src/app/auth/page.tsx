"use client";
import React, { useState } from "react";
import SignupModal from "../../components/SignupModal";
import LoginModal from "../../components/LoginModal";
import UserAccount from "../../components/UserAccount";

// Sample user data
const sampleUser = {
  id: "1",
  firstName: "John",
  lastName: "Smith",
  email: "john.smith@email.com",
  phone: "+1 555-123-4567",
};

// Sample bookings data
const sampleBookings = [
  {
    id: "1",
    bookingId: "ABV123456",
    origin: "New York",
    destination: "London",
    departureDate: "2024-03-15",
    returnDate: "2024-03-22",
    status: "confirmed" as const,
    passengers: 2,
    totalPrice: 1200,
    airline: "British Airways",
  },
  {
    id: "2",
    bookingId: "ABV789012",
    origin: "Los Angeles",
    destination: "Tokyo",
    departureDate: "2024-04-10",
    status: "pending" as const,
    passengers: 1,
    totalPrice: 850,
    airline: "Japan Airlines",
  },
  {
    id: "3",
    bookingId: "ABV345678",
    origin: "Miami",
    destination: "Paris",
    departureDate: "2024-02-28",
    returnDate: "2024-03-07",
    status: "cancelled" as const,
    passengers: 3,
    totalPrice: 2100,
    airline: "Air France",
  },
];

export default function AuthDemoPage() {
  const [showSignup, setShowSignup] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleSignupSuccess = () => {
    setIsLoggedIn(true);
    alert("Account created successfully! You are now logged in.");
  };

  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
    alert("Logged in successfully!");
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    alert("Logged out successfully!");
  };

  const handleSwitchToSignup = () => {
    setShowSignup(true);
  };

  if (isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <h1 className="text-xl font-semibold text-gray-900">Aero Bound Ventures</h1>
              <button
                onClick={handleLogout}
                className="text-gray-600 hover:text-gray-800 font-medium"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
        <UserAccount
          user={sampleUser}
          bookings={sampleBookings}
          onLogout={handleLogout}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-xl font-semibold text-gray-900">Aero Bound Ventures</h1>
            <div className="flex space-x-4">
              <button
                onClick={() => setShowLogin(true)}
                className="text-gray-600 hover:text-gray-800 font-medium"
              >
                Sign In
              </button>
              <button
                onClick={() => setShowSignup(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium"
              >
                Sign Up
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="max-w-2xl mx-auto text-center">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Authentication Demo
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              This page demonstrates the signup, login, and user account management features.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Signup Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Create Account</h3>
              <p className="text-gray-600 mb-4">
                Sign up for a new account to access your bookings and manage your profile.
              </p>
              <button
                onClick={() => setShowSignup(true)}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 font-medium"
              >
                Sign Up
              </button>
            </div>

            {/* Login Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Sign In</h3>
              <p className="text-gray-600 mb-4">
                Access your existing account to view bookings and manage your profile.
              </p>
              <button
                onClick={() => setShowLogin(true)}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 font-medium"
              >
                Sign In
              </button>
            </div>
          </div>

          {/* Features List */}
          <div className="mt-12">
            <h3 className="text-xl font-semibold text-gray-900 mb-6">Features Included</h3>
            <div className="grid md:grid-cols-3 gap-4 text-left">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h4 className="font-medium text-gray-900 mb-2">User Registration</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Form validation</li>
                  <li>• Password confirmation</li>
                  <li>• Terms agreement</li>
                  <li>• Responsive design</li>
                </ul>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h4 className="font-medium text-gray-900 mb-2">User Authentication</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Email/password login</li>
                  <li>• Social login options</li>
                  <li>• Remember me functionality</li>
                  <li>• Forgot password link</li>
                </ul>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h4 className="font-medium text-gray-900 mb-2">Account Management</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Profile editing</li>
                  <li>• Booking history</li>
                  <li>• Account settings</li>
                  <li>• Secure logout</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <SignupModal
        isOpen={showSignup}
        onClose={() => setShowSignup(false)}
        onSuccess={handleSignupSuccess}
        bookingId="DEMO123"
      />

      <LoginModal
        isOpen={showLogin}
        onClose={() => setShowLogin(false)}
        onSuccess={handleLoginSuccess}
        onSwitchToSignup={handleSwitchToSignup}
      />
    </div>
  );
} 