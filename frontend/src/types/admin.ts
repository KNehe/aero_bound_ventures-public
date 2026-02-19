/**
 * Type definitions for admin dashboard and booking management
 */

export interface BookingUser {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface AmadeusOrderResponse {
  associatedRecords?: Array<{ reference?: string }>;
  travelers?: Array<{
    travelerType?: string;
    name?: { firstName?: string; lastName?: string };
  }>;
  flightOffers?: Array<{
    itineraries?: Array<{
      duration?: string;
      segments?: Array<{
        departure: { iataCode?: string; at?: string };
        arrival: { iataCode?: string; at?: string };
        carrierCode?: string;
        number?: string;
        aircraft?: { code?: string };
        duration?: string;
        numberOfStops?: number;
      }>;
    }>;
  }>;
}

export interface Booking {
  id: string;
  flight_order_id: string;
  status: string;
  created_at: string;
  ticket_url: string | null;
  total_amount?: number;
  user: BookingUser;
  amadeus_order_response: AmadeusOrderResponse;
}

export interface CursorPaginatedBookingsResponse {
  items: Booking[];
  next_cursor: string | null;
  has_more: boolean;
  has_previous: boolean;
  total_count: number | null;
  limit: number;
}

export interface BookingStats {
  total_bookings: number;
  total_revenue: number;
  active_users: number;
  bookings_today: number;
  bookings_this_week: number;
}

export interface TicketUploadResponse {
  message: string;
  ticket_url: string;
  booking_id: string;
  public_id: string;
}
