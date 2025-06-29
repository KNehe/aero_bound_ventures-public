"use client";
import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Traveler {
  id: string;
  travelerType: "ADULT" | "CHILD" | "INFANT";
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: "MALE" | "FEMALE";
  email: string;
  phone: string;
  countryCallingCode: string;
  documents: {
    documentType: "PASSPORT" | "ID_CARD";
    number: string;
    expiryDate: string;
    issuanceCountry: string;
    nationality: string;
  };
}

interface ContactInfo {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  countryCallingCode: string;
  address: {
    street: string;
    city: string;
    postalCode: string;
    country: string;
  };
}

export default function BookingPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const resolvedParams = React.use(params);
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Mock flight data (in real app, this would come from the pricing API)
  const [travelers, setTravelers] = useState<Traveler[]>([
    {
      id: "1",
      travelerType: "ADULT",
      firstName: "",
      lastName: "",
      dateOfBirth: "",
      gender: "MALE",
      email: "",
      phone: "",
      countryCallingCode: "+1",
      documents: {
        documentType: "PASSPORT",
        number: "",
        expiryDate: "",
        issuanceCountry: "",
        nationality: "",
      },
    },
    {
      id: "2",
      travelerType: "CHILD",
      firstName: "",
      lastName: "",
      dateOfBirth: "",
      gender: "FEMALE",
      email: "",
      phone: "",
      countryCallingCode: "+1",
      documents: {
        documentType: "PASSPORT",
        number: "",
        expiryDate: "",
        issuanceCountry: "",
        nationality: "",
      },
    },
  ]);

  const [contactInfo, setContactInfo] = useState<ContactInfo>({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    countryCallingCode: "+1",
    address: {
      street: "",
      city: "",
      postalCode: "",
      country: "",
    },
  });

  const [paymentInfo, setPaymentInfo] = useState({
    cardNumber: "",
    expiryDate: "",
    cvv: "",
    cardholderName: "",
  });

  const [termsAccepted, setTermsAccepted] = useState(false);

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

  const updateContactInfo = (field: string, value: string) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setContactInfo(prev => ({
        ...prev,
        [parent]: { ...prev[parent as keyof ContactInfo], [child]: value }
      }));
    } else {
      setContactInfo(prev => ({ ...prev, [field]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate API call
    setTimeout(() => {
      setIsSubmitting(false);
      // Generate a mock order ID and navigate to success page
      const orderId = `MOCK_BOOKING_ID_${Date.now()}`;
      router.push(`/booking/success/${orderId}`);
    }, 2000);
  };

  const totalSteps = 4;
  const progress = (currentStep / totalSteps) * 100;

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
            <div className="text-right">
              <div className="text-2xl font-bold">EUR 546.70</div>
              <div className="text-sm opacity-90">Total for all passengers</div>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Step {currentStep} of {totalSteps}</span>
            <span className="text-sm text-gray-500">{Math.round(progress)}% Complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-500">
            <span>Traveler Info</span>
            <span>Contact Details</span>
            <span>Payment</span>
            <span>Review</span>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Step 1: Traveler Information */}
          {currentStep === 1 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Traveler Information</h2>
              
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
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                        <input
                          type="text"
                          required
                          value={traveler.lastName}
                          onChange={(e) => updateTraveler(index, 'lastName', e.target.value)}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth *</label>
                        <input
                          type="date"
                          required
                          value={traveler.dateOfBirth}
                          onChange={(e) => updateTraveler(index, 'dateOfBirth', e.target.value)}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Gender *</label>
                        <select
                          required
                          value={traveler.gender}
                          onChange={(e) => updateTraveler(index, 'gender', e.target.value)}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
                        <div className="flex">
                          <select
                            value={traveler.countryCallingCode}
                            onChange={(e) => updateTraveler(index, 'countryCallingCode', e.target.value)}
                            className="border border-gray-300 rounded-l-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="+1">+1</option>
                            <option value="+44">+44</option>
                            <option value="+33">+33</option>
                            <option value="+49">+49</option>
                          </select>
                          <input
                            type="tel"
                            required
                            value={traveler.phone}
                            onChange={(e) => updateTraveler(index, 'phone', e.target.value)}
                            className="flex-1 border border-gray-300 rounded-r-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                          <select
                            required
                            value={traveler.documents.documentType}
                            onChange={(e) => updateTraveler(index, 'documents.documentType', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="PASSPORT">Passport</option>
                            <option value="ID_CARD">ID Card</option>
                          </select>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Document Number *</label>
                          <input
                            type="text"
                            required
                            value={traveler.documents.number}
                            onChange={(e) => updateTraveler(index, 'documents.number', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date *</label>
                          <input
                            type="date"
                            required
                            value={traveler.documents.expiryDate}
                            onChange={(e) => updateTraveler(index, 'documents.expiryDate', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Nationality *</label>
                          <select
                            required
                            value={traveler.documents.nationality}
                            onChange={(e) => updateTraveler(index, 'documents.nationality', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="">Select Nationality</option>
                            <option value="US">United States</option>
                            <option value="GB">United Kingdom</option>
                            <option value="FR">France</option>
                            <option value="DE">Germany</option>
                            <option value="ES">Spain</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Contact Information */}
          {currentStep === 2 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Contact Information</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                  <input
                    type="text"
                    required
                    value={contactInfo.firstName}
                    onChange={(e) => updateContactInfo('firstName', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                  <input
                    type="text"
                    required
                    value={contactInfo.lastName}
                    onChange={(e) => updateContactInfo('lastName', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                  <input
                    type="email"
                    required
                    value={contactInfo.email}
                    onChange={(e) => updateContactInfo('email', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
                  <div className="flex">
                    <select
                      value={contactInfo.countryCallingCode}
                      onChange={(e) => updateContactInfo('countryCallingCode', e.target.value)}
                      className="border border-gray-300 rounded-l-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="+1">+1</option>
                      <option value="+44">+44</option>
                      <option value="+33">+33</option>
                      <option value="+49">+49</option>
                    </select>
                    <input
                      type="tel"
                      required
                      value={contactInfo.phone}
                      onChange={(e) => updateContactInfo('phone', e.target.value)}
                      className="flex-1 border border-gray-300 rounded-r-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Street Address *</label>
                  <input
                    type="text"
                    required
                    value={contactInfo.address.street}
                    onChange={(e) => updateContactInfo('address.street', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
                  <input
                    type="text"
                    required
                    value={contactInfo.address.city}
                    onChange={(e) => updateContactInfo('address.city', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Postal Code *</label>
                  <input
                    type="text"
                    required
                    value={contactInfo.address.postalCode}
                    onChange={(e) => updateContactInfo('address.postalCode', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Country *</label>
                  <select
                    required
                    value={contactInfo.address.country}
                    onChange={(e) => updateContactInfo('address.country', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select Country</option>
                    <option value="US">United States</option>
                    <option value="GB">United Kingdom</option>
                    <option value="FR">France</option>
                    <option value="DE">Germany</option>
                    <option value="ES">Spain</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Payment Information */}
          {currentStep === 3 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Payment Information</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cardholder Name *</label>
                  <input
                    type="text"
                    required
                    value={paymentInfo.cardholderName}
                    onChange={(e) => setPaymentInfo(prev => ({ ...prev, cardholderName: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Card Number *</label>
                  <input
                    type="text"
                    required
                    placeholder="1234 5678 9012 3456"
                    value={paymentInfo.cardNumber}
                    onChange={(e) => setPaymentInfo(prev => ({ ...prev, cardNumber: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date *</label>
                  <input
                    type="text"
                    required
                    placeholder="MM/YY"
                    value={paymentInfo.expiryDate}
                    onChange={(e) => setPaymentInfo(prev => ({ ...prev, expiryDate: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">CVV *</label>
                  <input
                    type="text"
                    required
                    placeholder="123"
                    value={paymentInfo.cvv}
                    onChange={(e) => setPaymentInfo(prev => ({ ...prev, cvv: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm text-blue-800">
                    <p className="font-medium">Secure Payment</p>
                    <p>Your payment information is encrypted and secure. We use industry-standard SSL encryption to protect your data.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Review and Confirm */}
          {currentStep === 4 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Review and Confirm</h2>
              
              <div className="space-y-6">
                {/* Flight Summary */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">Flight Summary</h3>
                  <div className="text-sm text-gray-600">
                    <p><strong>Route:</strong> SYD → SIN → DMK (Round Trip)</p>
                    <p><strong>Date:</strong> Feb 1, 2021 - Feb 5, 2021</p>
                    <p><strong>Passengers:</strong> 2 (1 Adult, 1 Child)</p>
                    <p><strong>Total:</strong> EUR 546.70</p>
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
                
                {/* Contact Summary */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">Contact Information</h3>
                  <div className="text-sm text-gray-600">
                    <p>{contactInfo.firstName} {contactInfo.lastName}</p>
                    <p>{contactInfo.email}</p>
                    <p>{contactInfo.countryCallingCode} {contactInfo.phone}</p>
                    <p>{contactInfo.address.street}, {contactInfo.address.city}, {contactInfo.address.postalCode}, {contactInfo.address.country}</p>
                  </div>
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
              onClick={() => setCurrentStep(prev => Math.max(1, prev - 1))}
              disabled={currentStep === 1}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            
            <div className="flex gap-3">
              {currentStep < totalSteps ? (
                <button
                  type="button"
                  onClick={() => setCurrentStep(prev => prev + 1)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
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