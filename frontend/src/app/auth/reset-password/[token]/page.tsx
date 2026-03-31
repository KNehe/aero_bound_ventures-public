"use client";

import React from "react";

import ResetPasswordForm from "@/components/ResetPasswordForm";

interface PageProps {
  params: Promise<{ token: string }>;
}

export default function ResetPasswordPage({ params }: PageProps) {
  const resolvedParams = React.use(params);
  return <ResetPasswordForm token={resolvedParams.token} />;
}
