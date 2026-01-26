// Flight Booking Types

export interface FlightBookingData {
  flight_offer: FlightOffer;
  travelers: Traveler[];
}

export interface FlightOffer {
  type: string;
  id: string;
  source: string;
  instantTicketingRequired: boolean;
  nonHomogeneous: boolean;
  paymentCardRequired: boolean;
  lastTicketingDate: string;
  itineraries: Itinerary[];
  price: Price;
  pricingOptions: PricingOptions;
  validatingAirlineCodes: string[];
  travelerPricings: TravelerPricing[];
}

export interface Itinerary {
  segments: Segment[];
}

export interface Segment {
  departure: LocationInfo;
  arrival: LocationInfo;
  carrierCode: string;
  number: string;
  aircraft: Aircraft;
  operating: Operating;
  duration: string;
  id: string;
  numberOfStops: number;
  co2Emissions: Co2Emission[];
}

export interface LocationInfo {
  iataCode: string;
  terminal: string;
  at: string;
}

export interface Aircraft {
  code: string;
}

export interface Operating {
  carrierCode: string;
}

export interface Co2Emission {
  weight: number;
  weightUnit: string;
  cabin: string;
}

export interface Price {
  currency: string;
  total: string;
  base: string;
  fees: Fee[];
  grandTotal: string;
  billingCurrency: string;
  taxes?: Tax[];
  refundableTaxes?: string;
}

export interface Fee {
  amount: string;
  type: string;
}

export interface Tax {
  amount: string;
  code: string;
}

export interface PricingOptions {
  fareType: string[];
  includedCheckedBagsOnly: boolean;
}

export interface TravelerPricing {
  travelerId: string;
  fareOption: string;
  travelerType: string;
  price: Price;
  fareDetailsBySegment: FareDetails[];
}

export interface FareDetails {
  segmentId: string;
  cabin: string;
  fareBasis: string;
  brandedFare: string;
  class: string;
  includedCheckedBags: IncludedCheckedBags;
  additionalServices?: AdditionalServices;
}

export interface AdditionalServices {
  chargeableSeatNumber?: string;
}

export interface IncludedCheckedBags {
  quantity: number;
}

export interface Traveler {
  id: string;
  dateOfBirth: string;
  name: Name;
  gender: string;
  contact: Contact;
  documents: Document[];
}

export interface Name {
  firstName: string;
  lastName: string;
}

export interface Contact {
  emailAddress: string;
  phones: Phone[];
}

export interface Phone {
  deviceType: string;
  countryCallingCode: string;
  number: string;
}

export interface Document {
  documentType: string;
  birthPlace: string;
  issuanceLocation: string;
  issuanceDate: string;
  number: string;
  expiryDate: string;
  issuanceCountry: string;
  validityCountry: string;
  nationality: string;
  holder: boolean;
}
