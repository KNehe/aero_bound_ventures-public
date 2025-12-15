from fastapi import APIRouter, HTTPException, Query, Depends, Path, BackgroundTasks
from backend.external_services.flight import amadeus_flight_service
from backend.schemas.flights import (
    FlightSearchResponse,
    FlightPricingResponse,
)
from typing import Annotated
from backend.schemas.flight_search import (
    FlightSearchRequestGet,
    FlightSearchRequestPost,
)
from backend.schemas.flight_price_confirm import FlightOffer
from backend.schemas.flight_order import FlightOrderRequestBody
from backend.utils.security import get_current_user
from backend.models.users import UserInDB
from amadeus.client.errors import ClientError
from backend.external_services.cache import redis_cache
from backend.utils.helpers import build_redis_key
from backend.schemas.locations import (
    AirportCitySearchRequest,
    AirportCitySearchResponse,
)
from backend.models.bookings import Booking
from backend.schemas.bookings import BookingResponse, UserBookingResponse
from backend.crud.database import get_session
from backend.utils.log_manager import get_app_logger
from sqlmodel import Session, select
from backend.external_services.email import send_email
from backend.crud.users import get_admin_emails


logger = get_app_logger(__name__)


router = APIRouter()


@router.post("/shopping/flight-offers", response_model=FlightSearchResponse)
async def search_flights(request: FlightSearchRequestPost):
    """
    Search for flights using the Amadeus Flight Search API

    This endpoint accepts a validated flight search request and returns available flight offers
    from the Amadeus API. The request is validated using Pydantic models.
    """
    try:
        request_body = request.model_dump()

        # TO DO: Search in cache first (REDIS)

        response = amadeus_flight_service.search_flights(request_body)
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flight search failed: {str(e)}")


@router.get("/shopping/flight-offers")
async def search_flights2(request: Annotated[FlightSearchRequestGet, Query()]):
    try:
        request_body = request.model_dump(exclude_none=True)

        key = build_redis_key(request_body)
        flight_data = redis_cache.get(key)
        if flight_data:
            return flight_data

        response = amadeus_flight_service.search_flights_get(request_body)
        redis_cache.set(key, response)

        return response
    except ClientError:
        raise HTTPException(status_code=400, detail="Invalid request parameters")
    except Exception:
        raise HTTPException(
            status_code=500, detail="An error occurred while searching for flights"
        )


@router.post("/shopping/flight-offers/pricing", response_model=FlightPricingResponse)
async def confirm_price(request: FlightOffer):
    """
    Confirm flight pricing using the Amadeus Flight Offers Pricing API

    This endpoint accepts a flight offer request and returns confirmed pricing information
    from the Amadeus API.
    """
    try:
        request_body = request.model_dump()
        response = amadeus_flight_service.confirm_price(request_body)
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Price confirmation failed: {str(e)}"
        )


@router.post("/booking/flight-orders", response_model=BookingResponse)
async def flight_order(
    background_tasks: BackgroundTasks,
    request: FlightOrderRequestBody,
    current_user: UserInDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Create a flight order from a pre-selected and price-confirmed flight offer.

    IMPORTANT:
    - The flight_offer must come from a RECENT pricing confirmation call
    - Flight offers expire quickly (typically within minutes)
    - Always call /shopping/flight-offers/pricing before this endpoint
    """
    logger.info(f"Flight order creation initiated by user_id: {current_user.id}")

    try:
        logger.debug(
            f"Preparing flight order request body for user_id: {current_user.id}"
        )
        request_body = request.model_dump(by_alias=True)

        logger.info(
            f"Creating flight order with Amadeus service for user_id: {current_user.id}"
        )
        response = amadeus_flight_service.create_flight_order(request_body)
        flight_order_id = response.get("id")

        logger.info(
            f"Flight order created successfully: {flight_order_id} for user_id: {current_user.id}"
        )

        logger.debug(
            f"Saving booking record for user_id: {current_user.id}, flight_order_id: {flight_order_id}"
        )
        total_price = 0.0
        if response:
            flight_offers = response.get("flightOffers", [])
            if flight_offers:
                price_info = flight_offers[0].get("price", {})
                grand_total = price_info.get("grandTotal", "0")
                try:
                    total_price = float(grand_total)
                except (ValueError, TypeError):
                    logger.warning(f"Failed to parse grandTotal: {grand_total}")
                    total_price = 0.0

        logger.info(f"Extracted total_price: {total_price} for booking")

        booking = Booking(
            user_id=current_user.id,
            flight_order_id=flight_order_id,
            amadeus_order_response=response,
            total_price=total_price,
        )
        session.add(booking)
        session.commit()

        booking_id = booking.id
        booking_flight_order_id = booking.flight_order_id
        booking_status = booking.status

        session.expunge(booking)

        background_tasks.add_task(
            send_email,
            recipients=[current_user.email],
            subject="Your Booking Order Received : Aero Bound Ventures",
            template_name="order_confirmation.html",
            extra={
                "pnr": response.get("associatedRecords", [{}])[0].get(
                    "reference", "N/A"
                )
            },
        )

        # Notify all admins
        admin_emails = get_admin_emails(session)
        background_tasks.add_task(
            send_email,
            recipients=admin_emails,
            subject="[ADMIN] New Booking Order Placed",
            template_name="admin_order_notification.html",
            extra={
                "pnr": response.get("associatedRecords", [{}])[0].get(
                    "reference", "N/A"
                ),
                "user_email": current_user.email,
                "booking_id": str(booking_id),
            },
        )

        response = BookingResponse(
            id=booking_id,
            flight_order_id=booking_flight_order_id,
            status=booking_status,
        )

        logger.info(
            f"Booking record saved successfully for user_id: {current_user.id}, flight_order_id: {flight_order_id}"
        )
        return response

    except ValueError as e:
        logger.warning(
            f"ValueError during flight order creation for user_id: {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))

    except ClientError as e:
        logger.error(
            f"ClientError during flight order creation for user_id: {current_user.id}: {str(e)}"
        )
        # Parse Amadeus error for user-friendly message
        error_detail = _parse_amadeus_client_error(e)
        raise HTTPException(status_code=400, detail=error_detail)

    except Exception:
        logger.exception(
            f"Unexpected error during flight order creation for user_id: {current_user.id}"
        )
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating the flight order. Please try again.",
        )


@router.get("/shopping/seatmaps")
async def view_seat_map_get(flightorderId: Annotated[str, Query()]):
    response = amadeus_flight_service.view_seat_map(flightorderId=flightorderId)
    return response


@router.post("/shopping/seatmaps")
async def view_seat_map_post(request: FlightOffer):
    request_body = request.model_dump()
    response = amadeus_flight_service.view_seat_map_post(request_body)
    return response


@router.get("/booking/flight-orders/{booking_id}")
async def get_flight_order(
    booking_id: str,
    current_user: UserInDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get complete booking details for the booking success page.
    Uses stored Amadeus order response from the database.

    Args:
        booking_id: Database booking UUID

    Returns:
        Transformed booking data matching frontend BookingSuccessData interface
    """
    from backend.utils.booking_transformer import transform_amadeus_to_booking_success
    import uuid as uuid_module

    logger.info(
        f"Fetching booking details for booking_id: {booking_id}, user_id: {current_user.id}"
    )

    try:
        try:
            booking_uuid = uuid_module.UUID(booking_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid booking ID format")

        booking = session.exec(
            select(Booking)
            .where(Booking.id == booking_uuid)
            .where(Booking.user_id == current_user.id)
        ).first()

        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Booking not found or you don't have permission to access it",
            )

        # Use stored Amadeus order response
        amadeus_order = booking.amadeus_order_response

        # Transform to frontend format, passing user email and ticket_url as fallback
        booking_details = transform_amadeus_to_booking_success(
            booking_id=str(booking.id),
            booking_date=booking.created_at,
            booking_status=booking.status,
            amadeus_order=amadeus_order,
            user_email=current_user.email,
            ticket_url=booking.ticket_url,
        )

        logger.info(
            f"Successfully retrieved booking details for booking_id: {booking_id}"
        )
        return booking_details

    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Error fetching booking details for booking_id: {booking_id}")
        raise HTTPException(
            status_code=500, detail="An error occurred while retrieving booking details"
        )


@router.delete("/booking/flight-orders/{flight_orderId:path}")
async def cancel_flight_order_management(
    flight_orderId: Annotated[str, Path()],
    current_user: UserInDB = Depends(get_current_user),
):
    """Cancel flight order by flight order ID"""
    try:
        response = amadeus_flight_service.cancel_flight_order(flight_orderId)
        return response.data
    except ClientError:
        raise HTTPException(status_code=400, detail="Invalid flight order ID")
    except Exception:
        raise HTTPException(
            status_code=500, detail="An error occurred while deleting the flight order"
        )


@router.get("/reference-data/locations", response_model=list[AirportCitySearchResponse])
async def airport_city_search(request: Annotated[AirportCitySearchRequest, Query()]):
    try:
        request_body = request.model_dump()

        key = build_redis_key(request_body)
        data = redis_cache.get(key)
        if data:
            return data

        response = amadeus_flight_service.airport_city_search(request_body)
        redis_cache.set(key, response)
        return response

    except Exception:
        raise HTTPException(
            status_code=500, detail="An error occurred while searching for a location"
        )


def _parse_amadeus_client_error(error: ClientError) -> str:
    """
    Parse Amadeus ClientError and return user-friendly error message.

    Args:
        error: ClientError from Amadeus SDK

    Returns:
        str: User-friendly error message
    """
    import json

    # Error code to message mapping
    ERROR_MESSAGES = {
        477: (
            "Invalid data format. Please check that all fields are correctly formatted "
            "(dates: YYYY-MM-DD, airport codes: 3-letter IATA codes)."
        ),
        1304: "The provided credit card is not accepted. Please try a different payment method.",
        2781: "Invalid data length. One or more fields exceed the maximum allowed length.",
        4926: "Invalid data received. Please verify all required fields are filled correctly.",
        9112: "Ticketing error occurred. Please contact support for assistance.",
        2668: "Invalid parameter combination. Please adjust your search criteria.",
        32171: "Missing required information. Please ensure all mandatory fields are provided.",
        34107: "The selected fare is not applicable. Please search for new flights.",
        34651: (
            "Flight is no longer available for booking. Flight offers expire within minutes. "
            "Please search for flights again and complete the entire booking process quickly."
        ),
        34733: "Payment processing failed. Please try again or use a different payment method.",
        36870: "Booking failed. The reservation could not be completed. Please search for flights again.",
        37200: "Price discrepancy detected. The flight price has changed. Please review the updated pricing.",
        38034: "One or more requested services are not available. Please review your selections.",
        141: "A system error occurred. Please try again in a few moments.",
    }

    DEFAULT_MESSAGE = "Unable to process your booking request. Please verify your information and try again."

    if not hasattr(error, "response") or not hasattr(error.response, "body"):
        return DEFAULT_MESSAGE

    try:
        # Parse error body
        body = error.response.body
        error_body = json.loads(body) if isinstance(body, str) else body

        errors = error_body.get("errors", [])
        if not errors:
            return f"Booking service error: {body}"

        # Extract first error
        first_error = errors[0]
        error_code = first_error.get("code")
        error_title = first_error.get("title", "Unknown error")
        error_detail = first_error.get("detail", "")
        error_source = first_error.get("source", {})

        # Return mapped message if code exists
        if isinstance(error_code, int) and error_code in ERROR_MESSAGES:
            return ERROR_MESSAGES[error_code]

        # Construct message from title and detail
        message = error_title
        if error_detail:
            message = f"{error_title}: {error_detail}"

        # Add source information if available
        if error_source and "parameter" in error_source:
            param = error_source.get("parameter")
            example = error_source.get("example", "")
            if example:
                message += f" (Parameter: {param}, Example: {example})"
            else:
                message += f" (Parameter: {param})"

        return message if message != "Unknown error" else DEFAULT_MESSAGE

    except Exception:
        return DEFAULT_MESSAGE


@router.get("/bookings", response_model=list[UserBookingResponse])
async def get_user_bookings(
    user: UserInDB = Depends(get_current_user), session: Session = Depends(get_session)
):
    """
    Get all bookings for the current user.

    Returns:
        List of bookings with id, pnr, status, created_at, and ticket_url
    """
    try:
        key = build_redis_key({"user_bookings": str(user.id)})
        cached_bookings = redis_cache.get(key)
        if cached_bookings:
            logger.info(f"Returning cached bookings for user_id: {user.id}")
            return cached_bookings

        logger.info(f"Fetching bookings for user_id: {user.id}")

        bookings = session.exec(
            select(Booking)
            .where(Booking.user_id == user.id)
            .order_by(Booking.created_at.desc())
        ).all()

        response = []
        for booking in bookings:
            pnr = None
            if booking.amadeus_order_response:
                print(f"amadeus_order_response: {booking.amadeus_order_response}")
                associated_records = booking.amadeus_order_response.get(
                    "associatedRecords", []
                )
                if associated_records:
                    pnr = associated_records[0].get("reference")

            response.append(
                UserBookingResponse(
                    id=booking.id,
                    pnr=pnr,
                    status=booking.status,
                    created_at=booking.created_at,
                    ticket_url=booking.ticket_url,
                )
            )

        response_data = [b.model_dump(mode="json") for b in response]
        redis_cache.set(key, response_data)

        logger.info(
            f"Successfully fetched {len(response)} bookings for user_id: {user.id}"
        )
        return response

    except Exception:
        logger.exception(f"Error fetching bookings for user_id: {user.id}")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching bookings"
        )


@router.get("/analytics/most-travelled-destinations")
def get_most_travelled_destinations(origin_city_code: str, period: str):
    try:
        key = build_redis_key({"city_code_period": f"{origin_city_code}{period}"})
        destinations = redis_cache.get(key)
        if destinations:
            return destinations

        response = amadeus_flight_service.get_most_travelled_destinations(
            origin_city_code, period
        )

        if len(response) > 0:
            redis_cache.set(key, response)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
