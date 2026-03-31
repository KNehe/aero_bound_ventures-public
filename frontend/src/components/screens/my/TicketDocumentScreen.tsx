"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import QRCode from "qrcode";
import { useQuery } from "@tanstack/react-query";

import useAuth from "@/store/auth";
import { apiClient, isUnauthorizedError } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import { TicketPageData } from "@/types/booking";

export default function TicketDocumentPage() {
  const params = useParams();
  const router = useRouter();
  const { logout, isAuthenticated, isHydrated } = useAuth();
  const bookingId = params.bookingId as string;

  const [printError, setPrintError] = useState<string | null>(null);

  const {
    data: ticketData,
    error,
    isLoading: loading,
  } = useQuery({
    queryKey: queryKeys.bookingDetails(bookingId),
    queryFn: () => apiClient.get<TicketPageData>(`/booking/flight-orders/${bookingId}`),
    enabled: Boolean(bookingId && isHydrated),
  });

  const { data: qrCodeUrl } = useQuery({
    queryKey: queryKeys.ticketQrCode(ticketData?.ticket_url ?? ""),
    queryFn: () =>
      QRCode.toDataURL(ticketData!.ticket_url!, {
        width: 180,
        margin: 1,
        errorCorrectionLevel: "M",
      }),
    enabled: Boolean(ticketData?.ticket_url),
  });

  useEffect(() => {
    if (!error || !isUnauthorizedError(error)) {
      return;
    }

    const redirectToLogin = async () => {
      await logout();
      router.push(`/auth/login?redirect=${encodeURIComponent(`/my/tickets/${bookingId}`)}`);
    };

    void redirectToLogin();
  }, [bookingId, error, logout, router]);

  useEffect(() => {
    if (!isHydrated) return;
    if (!isAuthenticated) {
      router.push(`/auth/login?redirect=${encodeURIComponent(`/my/tickets/${bookingId}`)}`);
    }
  }, [bookingId, isAuthenticated, isHydrated, router]);

  const fileType = useMemo(() => {
    const ticketUrl = ticketData?.ticket_url?.toLowerCase() || "";
    if (ticketUrl.match(/\.(png|jpg|jpeg|webp)(\?|$)/)) return "image";
    return "pdf";
  }, [ticketData?.ticket_url]);

  const handlePrintTicket = async () => {
    if (!ticketData?.ticket_url) return;
    setPrintError(null);

    try {
      const response = await fetch(ticketData.ticket_url);
      const blob = await response.blob();
      const objectUrl = window.URL.createObjectURL(blob);
      const contentType = response.headers.get("content-type") || "";
      const isImage = contentType.startsWith("image/");
      const printFrame = document.createElement("iframe");
      printFrame.style.position = "fixed";
      printFrame.style.right = "0";
      printFrame.style.bottom = "0";
      printFrame.style.width = "0";
      printFrame.style.height = "0";
      printFrame.style.border = "0";
      printFrame.style.opacity = "0";
      printFrame.setAttribute("aria-hidden", "true");
      document.body.appendChild(printFrame);

      const cleanup = () => {
        window.URL.revokeObjectURL(objectUrl);
        printFrame.remove();
      };

      if (isImage) {
        const doc = printFrame.contentWindow?.document;
        if (!doc || !printFrame.contentWindow) {
          cleanup();
          setPrintError("We couldn't prepare your ticket for printing. Please try again.");
          return;
        }

        doc.open();
        doc.write(`
          <!DOCTYPE html>
          <html>
            <head>
              <title>Print Ticket</title>
              <style>
                html, body {
                  margin: 0;
                  background: #ffffff;
                }
                body {
                  display: flex;
                  align-items: center;
                  justify-content: center;
                }
                img {
                  width: 100%;
                  max-width: 100%;
                  height: auto;
                  object-fit: contain;
                }
                @page {
                  margin: 12mm;
                }
              </style>
            </head>
            <body>
              <img src="${objectUrl}" alt="Ticket" />
            </body>
          </html>
        `);
        doc.close();

        const img = doc.querySelector("img");
        img?.addEventListener("load", () => {
          setTimeout(() => {
            printFrame.contentWindow?.focus();
            printFrame.contentWindow?.print();
          }, 100);
        });
      } else {
        printFrame.onload = () => {
          setTimeout(() => {
            printFrame.contentWindow?.focus();
            printFrame.contentWindow?.print();
          }, 100);
        };
        printFrame.src = objectUrl;
      }

      const afterPrint = () => {
        cleanup();
        window.removeEventListener("afterprint", afterPrint);
      };

      window.addEventListener("afterprint", afterPrint);
      window.setTimeout(() => {
        window.removeEventListener("afterprint", afterPrint);
        cleanup();
      }, 60000);
    } catch (err) {
      console.error("Failed to print ticket", err);
      setPrintError("We couldn't prepare your ticket for printing. Please try again.");
    }
  };

  const handleDownloadTicket = async () => {
    const ticketUrl = ticketData?.ticket_url;
    if (!ticketUrl || !ticketData) return;

    try {
      const response = await fetch(ticketUrl);
      const blob = await response.blob();

      let extension = "pdf";
      const contentType = response.headers.get("content-type");
      if (contentType?.includes("image/jpeg") || contentType?.includes("image/jpg")) {
        extension = "jpg";
      } else if (contentType?.includes("image/png")) {
        extension = "png";
      } else if (ticketUrl.match(/\.(jpg|jpeg|png|pdf)$/i)) {
        extension = ticketUrl.match(/\.(jpg|jpeg|png|pdf)$/i)![1].toLowerCase();
      }

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `ticket-${ticketData.orderId}.${extension}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download ticket", err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-stone-100 flex items-center justify-center">
        <p className="text-sm text-stone-600">Loading ticket document...</p>
      </div>
    );
  }

  if (error || !ticketData) {
    return (
      <div className="min-h-screen bg-stone-100 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-stone-200 p-6">
          <h1 className="text-xl font-semibold text-stone-900 mb-2">Ticket unavailable</h1>
          <p className="text-sm text-stone-600 mb-4">
            {error instanceof Error ? error.message : "Unable to load ticket."}
          </p>
          <Link
            href={`/booking/success/${bookingId}`}
            className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium"
          >
            Back to booking
          </Link>
        </div>
      </div>
    );
  }

  if (!ticketData.ticket_url) {
    return (
      <div className="min-h-screen bg-stone-100 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-stone-200 p-6">
          <h1 className="text-xl font-semibold text-stone-900 mb-2">No ticket uploaded yet</h1>
          <p className="text-sm text-stone-600 mb-4">
            Your ticket is still being prepared. Check back later and you will be able to view, print, or download it here.
          </p>
          <Link
            href={`/booking/success/${bookingId}`}
            className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium"
          >
            Back to booking
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-100 py-8 px-4">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-[auto_1fr_1fr] gap-3">
          <Link
            href={`/booking/success/${bookingId}`}
            className="inline-flex items-center justify-center px-4 py-3 rounded-xl border border-stone-300 bg-white text-sm font-medium text-stone-700"
          >
            Back
          </Link>
          <button
            onClick={handlePrintTicket}
            className="inline-flex items-center justify-center px-4 py-3 rounded-xl bg-blue-600 text-white text-sm font-medium"
          >
            Print Ticket
          </button>
          <button
            onClick={handleDownloadTicket}
            className="inline-flex items-center justify-center px-4 py-3 rounded-xl bg-emerald-600 text-white text-sm font-medium"
          >
            Download Ticket
          </button>
        </div>

        {printError && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {printError}
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-[320px_minmax(0,760px)] gap-6 justify-center">
          <aside className="bg-white border border-stone-200 rounded-3xl shadow-sm p-6 space-y-6 h-fit">
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-stone-500 mb-2">Your Ticket</p>
              <h1 className="text-2xl font-semibold text-stone-900">Travel document</h1>
              <p className="text-sm text-stone-600 mt-2">
                Use this page to keep your ticket handy, print a copy, or download it to your device before travel.
              </p>
            </div>

            <div className="space-y-3">
              <InfoRow label="Booking Reference" value={ticketData.orderId} mono />
              <InfoRow label="PNR" value={ticketData.pnr || "N/A"} />
              <InfoRow label="Status" value={ticketData.status.toUpperCase()} />
            </div>

            {qrCodeUrl && (
              <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
                <p className="text-sm font-medium text-stone-900 mb-1">Scan to open your ticket</p>
                <p className="text-xs text-stone-500 mb-3">
                  Helpful if you want quick access from another device.
                </p>
                <img src={qrCodeUrl} alt="QR code for your ticket" className="w-[180px] h-[180px] mx-auto" />
              </div>
            )}
          </aside>

          <section className="bg-white border border-stone-200 rounded-3xl shadow-sm overflow-hidden min-h-[64vh]">
            {fileType === "image" ? (
              <div className="bg-stone-50 p-4 md:p-6 flex justify-center">
                <img
                  src={ticketData.ticket_url}
                  alt="Uploaded ticket document"
                  className="w-full max-w-[680px] h-auto object-contain rounded-2xl"
                />
              </div>
            ) : (
              <div className="bg-stone-50 p-3 md:p-5">
                <iframe
                  title="Uploaded ticket document"
                  src={ticketData.ticket_url}
                  className="w-full min-h-[62vh] rounded-2xl bg-white"
                />
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

function InfoRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500 mb-2">{label}</p>
      <p className={`text-sm text-stone-900 break-all ${mono ? "font-mono" : "font-medium"}`}>{value}</p>
    </div>
  );
}
