"use client";

import BookingFlowScreen from "@/components/screens/booking/BookingFlowScreen";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function BookingPage({ params }: PageProps) {
  return <BookingFlowScreen params={params} />;
}
