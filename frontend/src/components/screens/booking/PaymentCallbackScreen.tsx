"use client";
import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

interface PaymentCallbackResponse {
  status: "success" | "failed" | "pending" | "error" | "reversed";
  message: string;
}

function PaymentCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"processing" | "success" | "failed">("processing");
  const [message, setMessage] = useState("Processing your payment...");
  const [originalBookingId, setOriginalBookingId] = useState<string>("");
  const orderTrackingId = searchParams.get("OrderTrackingId");
  const orderMerchantReference = searchParams.get("OrderMerchantReference");

  useEffect(() => {
    if (!orderMerchantReference) {
      return;
    }

    const bookingId = orderMerchantReference.includes("-")
      ? orderMerchantReference.substring(0, orderMerchantReference.lastIndexOf("-"))
      : orderMerchantReference;

    setOriginalBookingId(bookingId);
  }, [orderMerchantReference]);

  const { data, error } = useQuery({
    queryKey: queryKeys.paymentCallback(orderTrackingId ?? "", orderMerchantReference ?? ""),
    queryFn: () =>
      apiClient.get<PaymentCallbackResponse>("/payments/pesapal/callback", {
        params: {
          OrderTrackingId: orderTrackingId!,
          OrderMerchantReference: orderMerchantReference!,
        },
      }),
    enabled: Boolean(orderTrackingId && orderMerchantReference),
  });

  useEffect(() => {
    if (!orderTrackingId || !orderMerchantReference) {
      setStatus("failed");
      setMessage("Invalid payment callback");
      return;
    }

    if (error) {
      setStatus("failed");
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to verify payment. Please contact support."
      );
      return;
    }

    if (!data) {
      return;
    }

    if (data.status === "success") {
      setStatus("success");
      setMessage("Payment completed successfully!");
      window.setTimeout(() => {
        router.push(`/booking/success/${originalBookingId}?payment=success`);
      }, 5000);
      return;
    }

    if (data.status === "pending") {
      setStatus("processing");
      setMessage("Payment is pending. Please complete the payment to confirm your booking.");
      window.setTimeout(() => {
        router.push(`/booking/success/${originalBookingId}?payment=pending`);
      }, 5000);
      return;
    }

    setStatus("failed");
    setMessage(data.message || "Payment verification failed. Please contact support.");
  }, [data, error, orderMerchantReference, orderTrackingId, originalBookingId, router]);

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

export default function PaymentCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Loading...</h2>
          </div>
        </div>
      </div>
    }>
      <PaymentCallbackContent />
    </Suspense>
  );
}
