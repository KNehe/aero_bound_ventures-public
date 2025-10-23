export type AirportInfo = {
  iataCode: string;
  terminal?: string;
  at: string;
};

export type CO2Emission = {
  weight: number;
  weightUnit: string;
  cabin: string;
};

export type Segment = {
  id: string;
  departure: AirportInfo;
  arrival: AirportInfo;
  carrierCode: string;
  number: string;
  aircraft: { code: string };
  operating: { carrierCode: string };
  duration: string;
  numberOfStops: number;
  co2Emissions?: CO2Emission[];
  blacklistedInEU?: boolean;
};

export type Itinerary = {
  duration?: string;
  segments: Segment[];
};

export type Fee = {
  amount: string;
  type: string;
};

export type Tax = {
  amount: string;
  code: string;
};

export type Price = {
  currency: string;
  total: string;
  base: string;
  fees?: Fee[];
  taxes?: Tax[];
  grandTotal?: string;
  refundableTaxes?: string;
  billingCurrency?: string;
  additionalServices?: Array<{ amount: string; type: string }>;
};

export type PricingOptions = {
  fareType: string[];
  includedCheckedBagsOnly: boolean;
};

export type IncludedCheckedBags = {
  quantity: number;
};

export type FareDetailsBySegment = {
  segmentId: string;
  cabin: string;
  fareBasis: string;
  brandedFare: string;
  class: string;
  includedCheckedBags: IncludedCheckedBags;
};

export type TravelerPricing = {
  travelerId: string;
  fareOption: string;
  travelerType: string;
  price: Price;
  fareDetailsBySegment: FareDetailsBySegment[];
};

export type FlightOffer = {
  type: string;
  id: string;
  source: string;
  instantTicketingRequired: boolean;
  nonHomogeneous: boolean;
  paymentCardRequired?: boolean;
  oneWay?: boolean;
  isUpsellOffer?: boolean;
  lastTicketingDate: string;
  lastTicketingDateTime?: string;
  numberOfBookableSeats?: number;
  itineraries: Itinerary[];
  price: Price;
  pricingOptions: PricingOptions;
  validatingAirlineCodes: string[];
  travelerPricings: TravelerPricing[];
};

export type Phone = {
  deviceType: string;
  countryCallingCode: string;
  number: string;
};

export type Contact = {
  emailAddress: string;
  phones: Phone[];
};

export type TravelerName = {
  firstName: string;
  lastName: string;
};

export type Document = {
  documentType: string;
  birthPlace?: string;
  issuanceLocation?: string;
  issuanceDate: string;
  number: string;
  expiryDate: string;
  issuanceCountry: string;
  validityCountry?: string;
  nationality: string;
  holder: boolean;
};

export type Traveler = {
  id: string;
  dateOfBirth: string;
  name: TravelerName;
  gender: string;
  contact: Contact;
  documents: Document[];
};

export type FlightBookingRequest = {
  flight_offer: FlightOffer;
  travelers: Traveler[];
};