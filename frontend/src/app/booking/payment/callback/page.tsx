"use client";
import React, { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

export default function PaymentCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"processing" | "success" | "failed">("processing");
  const [message, setMessage] = useState("Processing your payment...");
  const [originalBookingId, setOriginalBookingId] = useState<string>("");

  useEffect(() => {
    const orderTrackingId = searchParams.get("OrderTrackingId");
    const orderMerchantReference = searchParams.get("OrderMerchantReference");

    if (!orderTrackingId || !orderMerchantReference) {
      setStatus("failed");
      setMessage("Invalid payment callback");
      return;
    }

    // Extract original booking ID from merchant reference (format: booking_id-timestamp)
    const originalBookingId = orderMerchantReference.includes('-') 
      ? orderMerchantReference.substring(0, orderMerchantReference.lastIndexOf('-'))
      : orderMerchantReference;

    setOriginalBookingId(originalBookingId);

    // Call backend to verify payment
    const verifyPayment = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
        const response = await fetch(
          `${baseUrl}/payments/pesapal/callback?OrderTrackingId=${orderTrackingId}&OrderMerchantReference=${orderMerchantReference}`
        );

        if (!response.ok) {
          throw new Error("Failed to verify payment");
        }

        const data = await response.json();

        if (data.status === "success") {
          setStatus("success");
          setMessage("Payment completed successfully!");
          
          // Redirect to booking success page after 2 seconds (use original booking ID)
          setTimeout(() => {
            router.push(`/booking/success/${originalBookingId}?payment=success`);
          }, 5000);
        } else if (data.status === "failed") {
          setStatus("failed");
          setMessage("Payment failed. Please try again.");
        } else if (data.status === "pending") {
          setStatus("processing");
          setMessage("Payment is pending. Please complete the payment to confirm your booking.");
          
          // Redirect to booking page (use original booking ID)
          setTimeout(() => {
            router.push(`/booking/success/${originalBookingId}?payment=pending`);
          }, 5000);
        } else {
          setStatus("failed");
          setMessage(data.message || "Payment verification failed. Please contact support.");
        }
      } catch (error) {
        console.error("Payment verification error:", error);
        setStatus("failed");
        setMessage("Unable to verify payment. Please contact support.");
      }
    };

    verifyPayment();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        {status === "processing" && (
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Processing Payment</h2>
            <p className="text-gray-600">{message}</p>
          </div>
        )}

        {status === "success" && (
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Payment Successful!</h2>
            <p className="text-gray-600 mb-4">{message}</p>
            <p className="text-sm text-gray-500">Redirecting to your booking...</p>
          </div>
        )}

        {status === "failed" && (
          <div className="text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Payment Failed</h2>
            <p className="text-gray-600 mb-6">{message}</p>
            <Link
              href={originalBookingId ? `/booking/success/${originalBookingId}` : "/"}
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors"
            >
              Try Payment Again
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
