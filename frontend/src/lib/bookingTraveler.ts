import type { Traveler as ApiTraveler } from "../types/flight-booking";

export interface BookingTraveler {
  id: string;
  travelerType: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: "MALE" | "FEMALE";
  email: string;
  phone: string;
  countryCallingCode: string;
  deviceType: "MOBILE" | "LANDLINE";
  documents: {
    documentType: "PASSPORT" | "ID_CARD";
    number: string;
    expiryDate: string;
    issuanceCountry: string;
    validityCountry: string;
    nationality: string;
    birthPlace: string;
    issuanceLocation: string;
    issuanceDate: string;
    holder: boolean;
  };
}

export type BookingTravelerErrors = Record<string, string>;

const MIN_PASSPORT_VALIDITY_MONTHS = 6;

export const formatDateForBackend = (date: string | Date): string => {
  if (!date) return "";

  if (typeof date === "string") {
    return date;
  }

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export const getMinPassportExpiryDate = (referenceDate = new Date()): string => {
  const minDate = new Date(referenceDate);
  minDate.setMonth(minDate.getMonth() + MIN_PASSPORT_VALIDITY_MONTHS);
  return formatDateForBackend(minDate);
};

export const getMaxPassportExpiryDate = (referenceDate = new Date()): string => {
  const maxDate = new Date(referenceDate);
  maxDate.setFullYear(maxDate.getFullYear() + 10);
  return formatDateForBackend(maxDate);
};

export const getDemoPassportExpiryDate = (referenceDate = new Date()): string => {
  const expiryDate = new Date(referenceDate);
  expiryDate.setFullYear(expiryDate.getFullYear() + 5);
  return formatDateForBackend(expiryDate);
};

export const getDemoPassportIssuanceDate = (referenceDate = new Date()): string => {
  const issuanceDate = new Date(referenceDate);
  issuanceDate.setFullYear(issuanceDate.getFullYear() - 1);
  return formatDateForBackend(issuanceDate);
};

export const buildDemoBookingTraveler = (
  currentTraveler?: BookingTraveler,
  referenceDate = new Date()
): BookingTraveler => ({
  id: currentTraveler?.id || "1",
  travelerType: currentTraveler?.travelerType || "ADULT",
  dateOfBirth: "2000-01-16",
  firstName: "JORGE",
  lastName: "GONZALES",
  gender: "MALE",
  email: "jorge.gonzales833@gmail.com",
  countryCallingCode: "+34",
  phone: "480080076",
  deviceType: "MOBILE",
  documents: {
    documentType: "PASSPORT",
    number: "00000000",
    expiryDate: getDemoPassportExpiryDate(referenceDate),
    issuanceCountry: "ES",
    validityCountry: "ES",
    nationality: "ES",
    birthPlace: "Madrid",
    issuanceLocation: "Madrid",
    issuanceDate: getDemoPassportIssuanceDate(referenceDate),
    holder: true,
  },
});

export const validateBookingTraveler = (
  traveler: BookingTraveler,
  referenceDate = new Date()
): BookingTravelerErrors => {
  const fieldErrors: BookingTravelerErrors = {};

  if (!traveler.firstName.trim()) fieldErrors.firstName = "First name is required";
  if (!traveler.lastName.trim()) fieldErrors.lastName = "Last name is required";
  if (!traveler.dateOfBirth) fieldErrors.dateOfBirth = "Date of birth is required";
  if (!traveler.email.trim()) fieldErrors.email = "Email is required";
  if (!traveler.phone.trim()) fieldErrors.phone = "Phone number is required";
  if (!traveler.documents.number.trim()) {
    fieldErrors["documents.number"] = "Passport number is required";
  }

  if (!traveler.documents.expiryDate) {
    fieldErrors["documents.expiryDate"] = "Passport expiry date is required";
  } else if (
    parseDateInput(traveler.documents.expiryDate) <
    parseDateInput(getMinPassportExpiryDate(referenceDate))
  ) {
    fieldErrors["documents.expiryDate"] =
      "Passport must be valid for at least 6 months after today";
  }

  if (!traveler.documents.nationality) {
    fieldErrors["documents.nationality"] = "Nationality is required";
  }
  if (!traveler.documents.issuanceCountry) {
    fieldErrors["documents.issuanceCountry"] = "Issuance country is required";
  }
  if (!traveler.documents.birthPlace.trim()) {
    fieldErrors["documents.birthPlace"] = "Birth place is required";
  }

  return fieldErrors;
};

export const transformToApiTraveler = (
  bookingTraveler: BookingTraveler
): ApiTraveler => {
  const validityCountry =
    bookingTraveler.documents.validityCountry ||
    bookingTraveler.documents.issuanceCountry;
  const issuanceLocation =
    bookingTraveler.documents.issuanceLocation ||
    bookingTraveler.documents.birthPlace;

  let issuanceDate = bookingTraveler.documents.issuanceDate;
  if (!issuanceDate && bookingTraveler.documents.expiryDate) {
    const expiry = parseDateInput(bookingTraveler.documents.expiryDate);
    const calculatedIssuance = new Date(expiry);
    calculatedIssuance.setFullYear(expiry.getFullYear() - 10);
    issuanceDate = formatDateForBackend(calculatedIssuance);
  }

  return {
    id: bookingTraveler.id,
    dateOfBirth: bookingTraveler.dateOfBirth,
    name: {
      firstName: bookingTraveler.firstName,
      lastName: bookingTraveler.lastName,
    },
    gender: bookingTraveler.gender,
    contact: {
      emailAddress: bookingTraveler.email,
      phones: [
        {
          deviceType: bookingTraveler.deviceType,
          countryCallingCode: bookingTraveler.countryCallingCode.replace("+", ""),
          number: bookingTraveler.phone,
        },
      ],
    },
    documents: [
      {
        documentType: bookingTraveler.documents.documentType,
        birthPlace: bookingTraveler.documents.birthPlace,
        issuanceLocation,
        issuanceDate: issuanceDate || "",
        number: bookingTraveler.documents.number,
        expiryDate: bookingTraveler.documents.expiryDate,
        issuanceCountry: bookingTraveler.documents.issuanceCountry,
        validityCountry,
        nationality: bookingTraveler.documents.nationality,
        holder: bookingTraveler.documents.holder,
      },
    ],
  };
};

const parseDateInput = (value: string): Date => {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
};
