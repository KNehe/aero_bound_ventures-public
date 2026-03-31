export const queryKeys = {
  popularDestinations: (originCityCode: string, period: string) =>
    ["popular-destinations", originCityCode, period] as const,
  locationSearch: (keyword: string) => ["location-search", keyword] as const,
  flights: (params: Record<string, string>) => ["flights", params] as const,
  flightPricing: (flightId: string | undefined) => ["flight-pricing", flightId] as const,
  adminStats: ["admin-stats"] as const,
  adminBookings: (pageSize: number) => ["admin-bookings", pageSize] as const,
  adminBooking: (bookingId: string) => ["admin-booking", bookingId] as const,
  bookingDetails: (bookingId: string) => ["booking-details", bookingId] as const,
  userBookings: (cursor: string | null) => ["bookings", cursor] as const,
  verifyResetToken: (token: string) => ["verify-reset-token", token] as const,
  paymentCallback: (orderTrackingId: string, merchantReference: string) =>
    ["payment-callback", orderTrackingId, merchantReference] as const,
  ticketQrCode: (ticketUrl: string) => ["ticket-qr-code", ticketUrl] as const,
  notifications: ["notifications"] as const,
};
