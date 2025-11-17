"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { Traveler as ApiTraveler, FlightBookingData, FlightOffer } from "@/types/flight-booking";
import useFlights from "@/store/flights";
import useAuth from "@/store/auth";
import countryCodes from "@/data/countryCodes.json";

// Local interface for form state - simplified for the booking form
interface BookingTraveler {
  id: string;
  travelerType: string; // ADULT, CHILD, INFANT - from API
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: "MALE" | "FEMALE";
  email: string;
  phone: string;
  countryCallingCode: string;
  deviceType: "MOBILE" | "LANDLINE";
  documents: {
    documentType: "PASSPORT" | "ID_CARD";
    number: string;
    expiryDate: string;
    issuanceCountry: string;
    validityCountry: string;
    nationality: string;
    birthPlace: string;
    issuanceLocation: string;
    issuanceDate: string;
    holder: boolean;
  };
}

// Helper function to transform BookingTraveler to API Traveler format
const transformToApiTraveler = (bookingTraveler: BookingTraveler): ApiTraveler => {
  // Smart defaults for optional fields
  const validityCountry = bookingTraveler.documents.validityCountry || bookingTraveler.documents.issuanceCountry;
  const issuanceLocation = bookingTraveler.documents.issuanceLocation || bookingTraveler.documents.birthPlace;
  
  // Calculate issuance date if not provided (assume 10 years before expiry for new passports)
  let issuanceDate = bookingTraveler.documents.issuanceDate;
  if (!issuanceDate && bookingTraveler.documents.expiryDate) {
    const expiry = new Date(bookingTraveler.documents.expiryDate);
    const calculatedIssuance = new Date(expiry);
    calculatedIssuance.setFullYear(expiry.getFullYear() - 10);
    issuanceDate = calculatedIssuance.toISOString().split('T')[0];
  }
  
  return {
    id: bookingTraveler.id,
    dateOfBirth: bookingTraveler.dateOfBirth,
    name: {
      firstName: bookingTraveler.firstName,
      lastName: bookingTraveler.lastName,
    },
    gender: bookingTraveler.gender,
    contact: {
      emailAddress: bookingTraveler.email,
      phones: [
        {
          deviceType: bookingTraveler.deviceType,
          countryCallingCode: bookingTraveler.countryCallingCode.replace('+', ''), // Remove + prefix
          number: bookingTraveler.phone,
        },
      ],
    },
    documents: [
      {
        documentType: bookingTraveler.documents.documentType,
        birthPlace: bookingTraveler.documents.birthPlace,
        issuanceLocation: issuanceLocation,
        issuanceDate: issuanceDate || '',
        number: bookingTraveler.documents.number,
        expiryDate: bookingTraveler.documents.expiryDate,
        issuanceCountry: bookingTraveler.documents.issuanceCountry,
        validityCountry: validityCountry,
        nationality: bookingTraveler.documents.nationality,
        holder: bookingTraveler.documents.holder,
      },
    ],
  };
};

export default function BookingPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const resolvedParams = React.use(params);
  const [currentStep, setCurrentStep] = useState(0); // Step 0: Traveler Info
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Use Zustand stores
  const { token, isAuthenticated, logout } = useAuth();
  const selectedFlight = useFlights((state) => state.selectedFlight?.data?.flightOffers[0]) as FlightOffer | null;

  // console.log("Selected Flight in Booking Page:", selectedFlight?.data.flightOffers[0]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Initialize travelers based on flight offer
  const [travelers, setTravelers] = useState<BookingTraveler[]>([]);

  // Check authentication on mount
  useEffect(() => {
    if (!isAuthenticated) {
      // Redirect to login with current page as redirect target
      const currentPath = `/booking/${resolvedParams.id}`;
      router.push(`/auth/login?redirect=${encodeURIComponent(currentPath)}`);
    }
  }, [isAuthenticated, resolvedParams.id, router]);

  // Initialize travelers based on selected flight offer
  useEffect(() => {
    if (selectedFlight) {
      // Initialize travelers based on travelerPricings from the flight offer
      if (selectedFlight.travelerPricings && selectedFlight.travelerPricings.length > 0) {
        const initialTravelers: BookingTraveler[] = selectedFlight.travelerPricings.map((pricing) => ({
          id: pricing.travelerId,
          travelerType: pricing.travelerType,
          firstName: "",
          lastName: "",
          dateOfBirth: "",
          gender: "MALE",
          email: "",
          phone: "",
          countryCallingCode: "+1",
          deviceType: "MOBILE",
          documents: {
            documentType: "PASSPORT",
            number: "",
            expiryDate: "",
            issuanceCountry: "",
            validityCountry: "",
            nationality: "",
            birthPlace: "",
            issuanceLocation: "",
            issuanceDate: "",
            holder: true,
          },
        }));
        console.log(selectedFlight)
        setTravelers(initialTravelers);
      }
    }
    setIsLoading(false);
  }, [selectedFlight]);

  const [termsAccepted, setTermsAccepted] = useState(false);
  // Removed payment and authentication-related state/handlers

  // Helper function to format date to YYYY-MM-DD format
  const formatDateForBackend = (date: string | Date): string => {
    if (!date) return '';
    const d = typeof date === 'string' ? new Date(date) : date;
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Helper functions for passport expiry date validation
  const getMinPassportExpiryDate = () => {
    // Passport must be valid for at least 6 months beyond today
    const today = new Date();
    const minDate = new Date(today);
    minDate.setMonth(minDate.getMonth() + 6);
    return formatDateForBackend(minDate);
  };

  const getMaxPassportExpiryDate = () => {
    // Passports typically valid for 10 years maximum from today
    const today = new Date();
    const maxDate = new Date(today);
    maxDate.setFullYear(maxDate.getFullYear() + 10);
    return formatDateForBackend(maxDate);
  };

  const updateTraveler = (index: number, field: string, value: string) => {
    const updatedTravelers = [...travelers];
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      (updatedTravelers[index] as any)[parent][child] = value;
    } else {
      (updatedTravelers[index] as any)[field] = value;
    }
    setTravelers(updatedTravelers);
  };

  // DEV ONLY: Populate test traveler data
  const populateTestData = () => {
    const testTravelerData: BookingTraveler = {
      id: "1",
      travelerType: travelers[0]?.travelerType || "ADULT",
      dateOfBirth: "2000-01-16",
      firstName: "JORGE",
      lastName: "GONZALES",
      gender: "MALE",
      email: "jorge.gonzales833@gmail.com",
      countryCallingCode: "+34",
      phone: "480080076",
      deviceType: "MOBILE",
      documents: {
        documentType: "PASSPORT",
        number: "00000000",
        expiryDate: "2026-04-14",
        issuanceCountry: "ES",
        validityCountry: "ES",
        nationality: "ES",
        birthPlace: "Madrid",
        issuanceLocation: "Madrid",
        issuanceDate: "2025-04-14",
        holder: true,
      },
    };

    const updatedTravelers = [...travelers];
    if (updatedTravelers.length > 0) {
      updatedTravelers[0] = testTravelerData;
      setTravelers(updatedTravelers);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Transform booking travelers to API format
      const apiTravelers: ApiTraveler[] = travelers.map(transformToApiTraveler);

      // Prepare booking payload with flight offer and travelers
      const bookingPayload: FlightBookingData = {
        flight_offer: selectedFlight!,
        travelers: apiTravelers,
      };

      console.log("Booking Payload:", bookingPayload);

      // Get the base URL from environment variables
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

      // Get auth token from Zustand store (should always exist due to mount check, but double-check)
      if (!token) {
        // If no token, redirect to login with current page as redirect target
        const currentPath = `/booking/${resolvedParams.id}`;
        router.push(`/auth/login?redirect=${encodeURIComponent(currentPath)}`);
        return;
      }

      // Send booking request to API
      const response = await fetch(`${baseUrl}/booking/flight-orders`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(bookingPayload),
      });
            
      if (response.status === 401) logout()
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create booking');
      }

      const bookingResult = await response.json();

      console.log("Booking Result:", bookingResult);

      router.push(`/booking/success/${bookingResult.id}`);

    } catch (error) {
      console.error("Booking error:", error);
      alert(error instanceof Error ? error.message : 'An error occurred while creating your booking. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalSteps = 2; // Traveler Info -> Review
  const progress = (currentStep / totalSteps) * 100;

  // Show loading/redirecting state while checking authentication
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // Show loading state while fetching flight offer
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading flight details...</p>
        </div>
      </div>
    );
  }

  if (!selectedFlight) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-xl mb-4">No flight selected</p>
          <p className="text-gray-600 mb-6">Please select a flight to proceed with booking.</p>
          <Link href="/flights" className="text-blue-600 hover:underline font-semibold">
            Return to flight search
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <Link href={`/flights/${resolvedParams.id}`} className="flex items-center gap-2 hover:opacity-80 transition-opacity">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span className="font-semibold">Back to Flight Details</span>
            </Link>
            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-2xl font-bold">{selectedFlight.price.currency} {selectedFlight.price.total}</div>
                <div className="text-sm opacity-90">Total for all passengers</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Step {currentStep + 1} of {totalSteps}</span>
            <span className="text-sm text-gray-500">{Math.round(progress)}% Complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-500">
            <span>Traveler Info</span>
            <span>Review</span>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form onSubmit={handleSubmit} className="space-y-8">c
          {/* Step 1: Traveler Information */}
          {currentStep === 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Traveler Information</h2>
                {process.env.NODE_ENV === 'development' && (
                  <button
                    type="button"
                    onClick={populateTestData}
                    className="px-3 py-1 bg-yellow-400 text-yellow-900 text-sm font-medium rounded hover:bg-yellow-500 transition-colors"
                  >
                    Fill Test Data (DEV)
                  </button>
                )}
              </div>
              
              <div className="space-y-8">
                {travelers.map((traveler, index) => (
                  <div key={traveler.id} className="border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 capitalize">
                      {traveler.travelerType} {index + 1}
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                        <input
                          type="text"
                          required
                          value={traveler.firstName}
                          onChange={(e) => updateTraveler(index, 'firstName', e.target.value)}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                        <input
                          type="text"
                          required
                          value={traveler.lastName}
                          onChange={(e) => updateTraveler(index, 'lastName', e.target.value)}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth *</label>
                        <input
                          type="date"
                          required
                          max={formatDateForBackend(new Date())}
                          value={traveler.dateOfBirth}
                          onChange={(e) => updateTraveler(index, 'dateOfBirth', e.target.value)}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Gender *</label>
                        <select
                          required
                          value={traveler.gender}
                          onChange={(e) => updateTraveler(index, 'gender', e.target.value)}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                        >
                          <option value="MALE">Male</option>
                          <option value="FEMALE">Female</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                        <input
                          type="email"
                          required
                          value={traveler.email}
                          onChange={(e) => updateTraveler(index, 'email', e.target.value)}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
                        <div className="flex">
                          <select
                            value={traveler.countryCallingCode}
                            onChange={(e) => updateTraveler(index, 'countryCallingCode', e.target.value)}
                            className="border border-gray-300 rounded-l-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                          >
                            {countryCodes.map((country, i) => (
                              <option key={i} value={`+${country.code}`}>
                                +{country.code}
                              </option>
                            ))}
                          </select>
                          <input
                            type="tel"
                            required
                            value={traveler.phone}
                            onChange={(e) => updateTraveler(index, 'phone', e.target.value)}
                            className="flex-1 border border-gray-300 rounded-r-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                          />
                        </div>
                      </div>
                    </div>
                    
                    {/* Document Information */}
                    <div className="mt-6 pt-6 border-t border-gray-200">
                      <h4 className="text-md font-semibold text-gray-800 mb-4">Travel Document</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Document Type *</label>
                          <input
                            type="text"
                            value="Passport"
                            readOnly
                            className="w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-100 text-gray-900 cursor-not-allowed"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Document Number *</label>
                          <input
                            type="text"
                            required
                            value={traveler.documents.number}
                            onChange={(e) => updateTraveler(index, 'documents.number', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Passport Expiry Date *
                            <span className="text-xs text-gray-500 ml-1">(must be valid for 6+ months)</span>
                          </label>
                          <input
                            type="date"
                            required
                            min={getMinPassportExpiryDate()}
                            max={getMaxPassportExpiryDate()}
                            value={traveler.documents.expiryDate}
                            onChange={(e) => updateTraveler(index, 'documents.expiryDate', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Must be valid for at least 6 months from today
                          </p>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Nationality *</label>
                          <select
                            required
                            value={traveler.documents.nationality}
                            onChange={(e) => updateTraveler(index, 'documents.nationality', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                          >
                            <option value="">Select Nationality</option>
                            {countryCodes.map((country, i) => (
                              <option key={i} value={country.iso}>
                                {country.country}
                              </option>
                            ))}
                          </select>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Issuance Country *</label>
                          <select
                            required
                            value={traveler.documents.issuanceCountry}
                            onChange={(e) => updateTraveler(index, 'documents.issuanceCountry', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                          >
                            <option value="">Select Issuance Country</option>
                            {countryCodes.map((country, i) => (
                              <option key={i} value={country.iso}>
                                {country.country}
                              </option>
                            ))}
                          </select>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Validity Country 
                            <span className="text-xs text-gray-500 ml-1">(Optional - defaults to issuance country)</span>
                          </label>
                          <select
                            value={traveler.documents.validityCountry}
                            onChange={(e) => updateTraveler(index, 'documents.validityCountry', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                          >
                            <option value="">Same as Issuance Country</option>
                            {countryCodes.map((country, i) => (
                              <option key={i} value={country.iso}>
                                {country.country}
                              </option>
                            ))}
                          </select>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Birth Place *</label>
                          <input
                            type="text"
                            required
                            placeholder="City of birth"
                            value={traveler.documents.birthPlace}
                            onChange={(e) => updateTraveler(index, 'documents.birthPlace', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Issuance Location 
                            <span className="text-xs text-gray-500 ml-1">(Optional - defaults to birth place)</span>
                          </label>
                          <input
                            type="text"
                            placeholder="City where passport was issued"
                            value={traveler.documents.issuanceLocation}
                            onChange={(e) => updateTraveler(index, 'documents.issuanceLocation', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Issuance Date 
                            <span className="text-xs text-gray-500 ml-1">(Optional - auto-calculated if omitted)</span>
                          </label>
                          <input
                            type="date"
                            max={formatDateForBackend(new Date())}
                            value={traveler.documents.issuanceDate}
                            onChange={(e) => updateTraveler(index, 'documents.issuanceDate', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Will be calculated from expiry date if not provided
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Review and Confirm */}
          {currentStep === 1 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Review and Confirm</h2>
              
              <div className="space-y-6">
                {/* Flight Summary */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">Flight Summary</h3>
                  <div className="text-sm text-gray-600">
                    <p><strong>Flight ID:</strong> {selectedFlight.id}</p>
                    <p><strong>Passengers:</strong> {travelers.length} ({travelers.map(t => t.travelerType).join(', ')})</p>
                    <p><strong>Total:</strong> {selectedFlight.price.currency} {selectedFlight.price.total}</p>
                  </div>
                </div>
                
                {/* Traveler Summary */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">Traveler Information</h3>
                  {travelers.map((traveler, index) => (
                    <div key={traveler.id} className="mb-3 last:mb-0">
                      <p className="font-medium text-gray-800 capitalize">{traveler.travelerType} {index + 1}</p>
                      <p className="text-sm text-gray-600">
                        {traveler.firstName} {traveler.lastName} • {traveler.dateOfBirth} • {traveler.gender}
                      </p>
                    </div>
                  ))}
                </div>
                
                {/* Terms and Conditions */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <input
                      type="checkbox"
                      required
                      checked={termsAccepted}
                      onChange={(e) => setTermsAccepted(e.target.checked)}
                      className="mt-1 mr-3"
                    />
                    <div className="text-sm text-gray-600">
                      <p>I agree to the <Link href="#" className="text-blue-600 hover:underline">Terms and Conditions</Link> and <Link href="#" className="text-blue-600 hover:underline">Privacy Policy</Link>.</p>
                      <p className="mt-2">I understand that this booking is subject to the airline's terms and conditions and may be subject to change.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))}
              disabled={currentStep === 0}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            
            <div className="flex gap-3">
              {currentStep < totalSteps - 1 ? (
                <button
                  type="button"
                  onClick={() => setCurrentStep(prev => prev + 1)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={isSubmitting || !termsAccepted}
                  className="px-8 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Processing...
                    </div>
                  ) : (
                    'Confirm Booking'
                  )}
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
} 