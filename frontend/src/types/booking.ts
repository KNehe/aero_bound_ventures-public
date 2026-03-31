export interface TicketPageData {
  orderId: string;
  pnr: string;
  bookingDate: string;
  status:
    | "confirmed"
    | "pending"
    | "cancelled"
    | "paid"
    | "reversed"
    | "failed"
    | "refunded";
  ticket_url?: string;
}

export interface BookingSuccessData extends TicketPageData {
  flightDetails: {
    outbound: {
      date: string;
      segments: Array<{
        departure: { airport: string; time: string; terminal?: string };
        arrival: { airport: string; time: string; terminal?: string };
        flight: string;
        duration: string;
      }>;
    };
    return?: {
      date: string;
      segments: Array<{
        departure: { airport: string; time: string; terminal?: string };
        arrival: { airport: string; time: string; terminal?: string };
        flight: string;
        duration: string;
      }>;
    };
  };
  passengers: Array<{
    id: string;
    type: string;
    name: string;
    seat?: string;
  }>;
  pricing: {
    total: string;
    currency: string;
    breakdown: Array<{
      item: string;
      amount: string;
    }>;
  };
  contact: {
    name: string;
    email: string;
    phone: string;
  };
}
