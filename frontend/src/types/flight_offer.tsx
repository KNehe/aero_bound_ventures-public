export type AirportInfo = {
  iataCode: string;
  terminal?: string;
  at: string;
};

export type Segment = {
  id: string;
  departure: AirportInfo;
  arrival: AirportInfo;
  carrierCode?: string;
  number?: string;
  aircraft?: { code?: string };
  operating?: { carrierCode?: string };
  duration?: string;
  numberOfStops?: number;
  blacklistedInEU?: boolean;
};

export type Itinerary = {
  duration?: string;
  segments: Segment[];
};

export type Price = {
  currency?: string;
  total: string;
  base?: string;
  fees?: Array<{ amount: string; type: string }>;
  grandTotal?: string;
  additionalServices?: Array<{ amount: string; type: string }>;
};

export type FlightOffer = {
  type?: string;
  id?: string;
  source?: string;
  instantTicketingRequired?: boolean;
  nonHomogeneous?: boolean;
  oneWay?: boolean;
  isUpsellOffer?: boolean;
  lastTicketingDate?: string;
  lastTicketingDateTime?: string;
  numberOfBookableSeats?: number;
  itineraries: Itinerary[];
  price: Price;
  pricingOptions?: any;
  validatingAirlineCodes?: string[];
  travelerPricings?: any[];
};