"""
Utility for transforming Amadeus flight order data into frontend-friendly format.
"""

from datetime import datetime
import re


def transform_amadeus_to_booking_success(
    booking_id: str, booking_date: datetime, booking_status: str, amadeus_order: dict
) -> dict:
    """
    Transform Amadeus flight order response and database booking data
    into the format expected by the frontend booking success page.

    Args:
        booking_id: Database booking UUID
        booking_date: When the booking was created
        booking_status: Current booking status (pending/confirmed/cancelled)
        amadeus_order: Raw Amadeus flight order response

    Returns:
        dict: Transformed booking data matching BookingSuccessData interface
    """

    # Extract PNR from associatedRecords
    pnr = "N/A"
    if "associatedRecords" in amadeus_order and amadeus_order["associatedRecords"]:
        pnr = amadeus_order["associatedRecords"][0].get("reference", "N/A")

    # Map database status to frontend expected values
    status_map = {
        "pending": "PENDING",
        "confirmed": "CONFIRMED",
        "cancelled": "CANCELLED",
    }
    status = status_map.get(booking_status.lower(), "PENDING")

    # Extract flight offer (first one)
    flight_offers = amadeus_order.get("flightOffers", [])
    flight_offer = flight_offers[0] if flight_offers else {}

    # Transform flight details
    flight_details = _transform_flight_details(flight_offer)

    # Transform passengers
    passengers = _transform_passengers(amadeus_order.get("travelers", []))

    # Transform pricing
    pricing = _transform_pricing(flight_offer.get("price", {}))

    # Extract contact information
    contact = _transform_contact(amadeus_order.get("contacts", []))

    return {
        "orderId": booking_id,
        "pnr": pnr,
        "bookingDate": booking_date.isoformat(),
        "status": status,
        "flightDetails": flight_details,
        "passengers": passengers,
        "pricing": pricing,
        "contact": contact,
    }


def _transform_flight_details(flight_offer: dict) -> dict:
    """Transform Amadeus itineraries into outbound/return format"""
    itineraries = flight_offer.get("itineraries", [])

    result = {}

    if len(itineraries) > 0:
        result["outbound"] = _transform_itinerary(itineraries[0])

    if len(itineraries) > 1:
        result["return"] = _transform_itinerary(itineraries[1])

    return result


def _transform_itinerary(itinerary: dict) -> dict:
    """Transform a single itinerary"""
    segments = itinerary.get("segments", [])

    if not segments:
        return {"date": "", "segments": []}

    # Get date from first segment
    departure_date = segments[0].get("departure", {}).get("at", "")
    date = departure_date.split("T")[0] if departure_date else ""

    transformed_segments = []
    for segment in segments:
        departure = segment.get("departure", {})
        arrival = segment.get("arrival", {})

        # Parse times
        dep_time = departure.get("at", "")
        arr_time = arrival.get("at", "")

        dep_time_str = dep_time.split("T")[1][:5] if "T" in dep_time else ""
        arr_time_str = arr_time.split("T")[1][:5] if "T" in arr_time else ""

        # Calculate duration
        duration = segment.get("duration", "PT0H0M")
        duration_str = _format_duration(duration)

        # Build flight number
        carrier_code = segment.get("carrierCode", "")
        flight_number = segment.get("number", "")
        flight = f"{carrier_code}{flight_number}"

        transformed_segments.append(
            {
                "departure": {
                    "airport": departure.get("iataCode", ""),
                    "time": dep_time_str,
                    "terminal": departure.get("terminal"),
                },
                "arrival": {
                    "airport": arrival.get("iataCode", ""),
                    "time": arr_time_str,
                    "terminal": arrival.get("terminal"),
                },
                "flight": flight,
                "duration": duration_str,
            }
        )

    return {"date": date, "segments": transformed_segments}


def _format_duration(iso_duration: str) -> str:
    """Convert ISO 8601 duration (PT2H30M) to readable format (2h 30m)"""
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", iso_duration)
    if not match:
        return "0h 0m"

    hours = match.group(1) or "0"
    minutes = match.group(2) or "0"

    return f"{hours}h {minutes}m"


def _transform_passengers(travelers: list) -> list[dict]:
    """Transform Amadeus travelers to passenger format"""
    passengers = []

    for traveler in travelers:
        traveler_id = traveler.get("id", "")

        # Determine passenger type
        traveler_type = traveler.get("travelerType", "ADULT")
        type_map = {
            "ADULT": "Adult",
            "CHILD": "Child",
            "HELD_INFANT": "Infant",
            "SEATED_INFANT": "Infant",
        }
        passenger_type = type_map.get(traveler_type, "Adult")

        # Build name
        name_data = traveler.get("name", {})
        first_name = name_data.get("firstName", "")
        last_name = name_data.get("lastName", "")
        name = f"{first_name} {last_name}".strip()

        passengers.append(
            {
                "id": traveler_id,
                "type": passenger_type,
                "name": name,
                "seat": None,  # Seat assignment not in flight order
            }
        )

    return passengers


def _transform_pricing(price_data: dict) -> dict:
    """Transform Amadeus pricing to frontend format"""
    total = price_data.get("grandTotal", "0.00")
    currency = price_data.get("currency", "USD")

    # Build breakdown
    breakdown = []

    base_price = price_data.get("base", "0.00")
    if base_price and float(base_price) > 0:
        breakdown.append({"item": "Base Fare", "amount": base_price})

    # Add fees
    fees = price_data.get("fees", [])
    total_fees = sum(float(fee.get("amount", "0")) for fee in fees)
    if total_fees > 0:
        breakdown.append({"item": "Fees", "amount": str(total_fees)})

    # Add taxes
    taxes = price_data.get("taxes", [])
    tax_total = sum(float(tax.get("amount", "0")) for tax in taxes)
    if tax_total > 0:
        breakdown.append({"item": "Taxes", "amount": f"{tax_total:.2f}"})

    return {"total": total, "currency": currency, "breakdown": breakdown}


def _transform_contact(contacts: list) -> dict:
    """Extract primary contact information"""
    if not contacts:
        return {"name": "N/A", "email": "N/A", "phone": "N/A"}

    primary_contact = contacts[0]

    # Get email
    email_address = primary_contact.get("emailAddress", "N/A")

    # Get phone
    phones = primary_contact.get("phones", [])
    phone_number = "N/A"
    if phones:
        country_code = phones[0].get("countryCallingCode", "")
        number = phones[0].get("number", "")
        if country_code and number:
            phone_number = f"+{country_code} {number}"
        elif number:
            phone_number = number

    # Try to get name from contact or construct from travelers
    name = primary_contact.get("name", "N/A")

    return {"name": name, "email": email_address, "phone": phone_number}
