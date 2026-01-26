/**
 * Type definitions for admin dashboard and booking management
 */

export interface BookingUser {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface Booking {
  id: string;
  flight_order_id: string;
  status: string;
  created_at: string;
  ticket_url: string | null;
  total_amount?: number;
  user: BookingUser;
  amadeus_order_response: Record<string, unknown>;
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
