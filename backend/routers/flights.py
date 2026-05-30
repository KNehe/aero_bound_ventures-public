from fastapi import APIRouter, Depends, HTTPException, Query

from backend.application.bookings.create_flight_order import (
    CreateFlightOrder,
    FlightOrderProviderError,
    InvalidFlightOrderRequest,
)
from backend.application.bookings.cancel_booking import (
    BookingAlreadyCancelled,
    BookingCannotBeCancelled,
    BookingNotFound,
    CancelBooking,
    CancelBookingCommand,
)
from backend.application.bookings.get_booking_details import (
    BookingDetailsNotFound,
    GetBookingDetails,
)
from backend.application.bookings.get_seat_map import (
    GetSeatMap,
    InvalidSeatMapRequest,
    SeatMapBookingNotFound,
    SeatMapProviderError,
)
from backend.application.bookings.get_user_bookings import GetUserBookings
from backend.application.flights.confirm_flight_price import (
    ConfirmFlightPrice,
    FlightPricingProviderError,
    InvalidFlightPricingRequest,
)
from backend.application.flights.get_seat_map_from_flight_offer import (
    GetSeatMapFromFlightOffer,
    InvalidSeatMapOfferRequest,
    SeatMapFromOfferProviderError,
)
from backend.application.flights.get_travelled_destinations import (
    GetTravelledDestinations,
    InvalidTravelledDestinationsRequest,
    TravelledDestinationsProviderError,
)
from backend.application.flights.search_flights import (
    FlightSearchProviderError,
    InvalidFlightSearchRequest,
    SearchFlights,
)
from backend.application.flights.search_locations import (
    InvalidLocationSearchRequest,
    LocationSearchProviderError,
    SearchLocations,
)
from backend.external_services.flight import amadeus_flight_service
from backend.infrastructure.bookings.booking_success_presenter import (
    BookingSuccessPresenter,
)
from backend.infrastructure.bookings.kafka_booking_event_publisher import (
    KafkaBookingEventPublisher,
)
from backend.infrastructure.bookings.redis_user_booking_cache import (
    RedisUserBookingCache,
)
from backend.infrastructure.bookings.sqlmodel_booking_repository import (
    SqlModelBookingRepository,
)
from backend.infrastructure.flights.amadeus_flight_order_cancellation_gateway import (
    AmadeusFlightOrderCancellationGateway,
)
from backend.infrastructure.flights.amadeus_flight_order_gateway import (
    AmadeusFlightOrderGateway,
)
from backend.infrastructure.flights.amadeus_location_search_gateway import (
    AmadeusLocationSearchGateway,
)
from backend.infrastructure.flights.amadeus_pricing_gateway import AmadeusPricingGateway
from backend.infrastructure.flights.amadeus_seat_map_gateway import (
    AmadeusSeatMapGateway,
)
from backend.infrastructure.flights.amadeus_search_gateway import AmadeusSearchGateway
from backend.infrastructure.flights.amadeus_travel_analytics_gateway import (
    AmadeusTravelAnalyticsGateway,
)
from backend.schemas.flights import (
    FlightPricingResponse,
)
from typing import Annotated
from backend.schemas.flight_search import FlightSearchRequestGet
from backend.schemas.flight_price_confirm import FlightOffer
from backend.schemas.flight_order import FlightOrderRequestBody
from backend.utils.security import get_current_user
from backend.models.users import UserInDB
from backend.external_services.cache import redis_cache
from backend.schemas.locations import (
    AirportCitySearchRequest as LocationSearchRequest,
    AirportCitySearchResponse as LocationSearchResponse,
)
from backend.schemas.bookings import (
    BookingResponse,
    UserBookingResponse,
    BookingCancellationResponse,
    CursorPaginatedUserBookingResponse,
)
from backend.crud.database import get_session
from backend.utils.pagination import MAX_PAGINATION_LIMIT
from backend.utils.log_manager import get_app_logger
from sqlmodel import Session
from backend.utils.kafka import kafka_producer
import uuid as uuid_module


logger = get_app_logger(__name__)


router = APIRouter()


def get_search_flights_use_case() -> SearchFlights:
    return SearchFlights(
        provider=AmadeusSearchGateway(amadeus_flight_service),
        cache=redis_cache,
    )


def get_confirm_flight_price_use_case() -> ConfirmFlightPrice:
    return ConfirmFlightPrice(
        provider=AmadeusPricingGateway(amadeus_flight_service),
    )


def get_create_flight_order_use_case(
    session: Session = Depends(get_session),
) -> CreateFlightOrder:
    return CreateFlightOrder(
        order_provider=AmadeusFlightOrderGateway(amadeus_flight_service),
        booking_repository=SqlModelBookingRepository(session),
        booking_cache=RedisUserBookingCache(redis_cache),
        event_publisher=KafkaBookingEventPublisher(kafka_producer),
    )


def get_booking_details_use_case(
    session: Session = Depends(get_session),
) -> GetBookingDetails:
    return GetBookingDetails(
        booking_repository=SqlModelBookingRepository(session),
        presenter=BookingSuccessPresenter(),
    )


def get_cancel_booking_use_case(
    session: Session = Depends(get_session),
) -> CancelBooking:
    return CancelBooking(
        booking_repository=SqlModelBookingRepository(session),
        booking_cancellation_provider=AmadeusFlightOrderCancellationGateway(
            amadeus_flight_service
        ),
        booking_cache=RedisUserBookingCache(redis_cache),
        event_publisher=KafkaBookingEventPublisher(kafka_producer),
    )


def get_seat_map_use_case(
    session: Session = Depends(get_session),
) -> GetSeatMap:
    return GetSeatMap(
        booking_repository=SqlModelBookingRepository(session),
        seat_map_provider=AmadeusSeatMapGateway(amadeus_flight_service),
    )


def get_seat_map_from_flight_offer_use_case() -> GetSeatMapFromFlightOffer:
    return GetSeatMapFromFlightOffer(
        seat_map_provider=AmadeusSeatMapGateway(amadeus_flight_service),
    )


def get_location_search_use_case() -> SearchLocations:
    return SearchLocations(
        provider=AmadeusLocationSearchGateway(amadeus_flight_service),
        cache=redis_cache,
    )


def get_travelled_destinations_use_case() -> GetTravelledDestinations:
    return GetTravelledDestinations(
        provider=AmadeusTravelAnalyticsGateway(amadeus_flight_service),
        cache=redis_cache,
    )


def get_user_bookings_use_case(
    session: Session = Depends(get_session),
) -> GetUserBookings:
    return GetUserBookings(
        booking_repository=SqlModelBookingRepository(session),
        cache=RedisUserBookingCache(redis_cache),
    )


@router.get("/shopping/flight-offers")
async def search_flights_get(
    request: Annotated[FlightSearchRequestGet, Query()],
    search_flights_use_case: SearchFlights = Depends(get_search_flights_use_case),
):
    try:
        return search_flights_use_case.execute(request.model_dump(exclude_none=True))
    except InvalidFlightSearchRequest:
        raise HTTPException(status_code=400, detail="Invalid request parameters")
    except FlightSearchProviderError:
        raise HTTPException(
            status_code=500, detail="An error occurred while searching for flights"
        )
    except Exception:
        raise HTTPException(
            status_code=500, detail="An error occurred while searching for flights"
        )


@router.post("/shopping/flight-offers/pricing", response_model=FlightPricingResponse)
async def confirm_price(
    request: FlightOffer,
    confirm_flight_price_use_case: ConfirmFlightPrice = Depends(
        get_confirm_flight_price_use_case
    ),
):
    """
    Confirm flight pricing using the Amadeus Flight Offers Pricing API

    This endpoint accepts a flight offer request and returns confirmed pricing information
    from the Amadeus API.
    """
    try:
        return confirm_flight_price_use_case.execute(request.model_dump())
    except InvalidFlightPricingRequest:
        raise HTTPException(status_code=400, detail="Invalid pricing request")
    except FlightPricingProviderError:
        raise HTTPException(
            status_code=500, detail="An error occurred while confirming flight pricing"
        )
    except Exception:
        raise HTTPException(
            status_code=500, detail="An error occurred while confirming flight pricing"
        )


@router.post("/booking/flight-orders", response_model=BookingResponse)
async def flight_order(
    request: FlightOrderRequestBody,
    current_user: UserInDB = Depends(get_current_user),
    create_flight_order_use_case: CreateFlightOrder = Depends(
        get_create_flight_order_use_case
    ),
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
        booking = create_flight_order_use_case.execute(
            user_id=current_user.id,
            user_email=current_user.email,
            order_request=request.model_dump(by_alias=True),
        )

        response = BookingResponse(
            id=booking.id,
            flight_order_id=booking.flight_order_id,
            status=booking.status,
        )

        logger.info(
            f"Booking record saved successfully for user_id: {current_user.id}, "
            f"flight_order_id: {booking.flight_order_id}"
        )
        return response

    except InvalidFlightOrderRequest as e:
        logger.warning(
            f"Invalid flight order request for user_id: {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except FlightOrderProviderError:
        logger.exception(
            f"Flight provider error during order creation for user_id: {current_user.id}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating the flight order. Please try again.",
        )

    except Exception:
        logger.exception(
            f"Unexpected error during flight order creation for user_id: {current_user.id}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating the flight order. Please try again.",
        )


@router.get("/shopping/seatmaps")
async def view_seat_map_get(
    flight_order_reference: Annotated[str, Query(alias="flightorderId")],
    current_user: UserInDB = Depends(get_current_user),
    seat_map_use_case: GetSeatMap = Depends(get_seat_map_use_case),
):
    try:
        return seat_map_use_case.execute(
            flight_order_reference=flight_order_reference,
            user_id=current_user.id,
        )
    except SeatMapBookingNotFound:
        raise HTTPException(
            status_code=404, detail="Booking not found or access denied"
        )
    except InvalidSeatMapRequest as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SeatMapProviderError:
        raise HTTPException(status_code=500, detail="Failed to retrieve seat map")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Failed to retrieve seat map for ID: {flight_order_reference}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve seat map: {str(e)}"
        )


@router.post("/shopping/seatmaps")
async def view_seat_map_post(
    request: FlightOffer,
    seat_map_from_offer_use_case: GetSeatMapFromFlightOffer = Depends(
        get_seat_map_from_flight_offer_use_case
    ),
):
    try:
        return seat_map_from_offer_use_case.execute(request.model_dump())
    except InvalidSeatMapOfferRequest as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SeatMapFromOfferProviderError:
        raise HTTPException(status_code=500, detail="Failed to retrieve seat map")
    except Exception:
        logger.exception("Failed to retrieve seat map from flight offer")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve seat map from flight offer"
        )


@router.get("/booking/flight-orders/{booking_id}")
async def get_booking_details(
    booking_id: str,
    current_user: UserInDB = Depends(get_current_user),
    booking_details_use_case: GetBookingDetails = Depends(get_booking_details_use_case),
):
    """
    Get complete booking details for the booking success page.
    Uses stored Amadeus order response from the database.

    Args:
        booking_id: Database booking UUID

    Returns:
        Transformed booking data matching frontend BookingSuccessData interface
    """
    logger.info(
        f"Fetching booking details for booking_id: {booking_id}, user_id: {current_user.id}"
    )

    try:
        try:
            booking_uuid = uuid_module.UUID(booking_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid booking ID format")

        booking_details = booking_details_use_case.execute(
            booking_id=booking_uuid,
            user_id=current_user.id,
            user_email=current_user.email,
        )

        logger.info(
            f"Successfully retrieved booking details for booking_id: {booking_id}"
        )
        return booking_details

    except HTTPException:
        raise
    except BookingDetailsNotFound:
        raise HTTPException(
            status_code=404,
            detail="Booking not found or you don't have permission to access it",
        )
    except Exception:
        logger.exception(f"Error fetching booking details for booking_id: {booking_id}")
        raise HTTPException(
            status_code=500, detail="An error occurred while retrieving booking details"
        )


@router.delete("/booking/flight-orders/{booking_id}")
async def cancel_booking(
    booking_id: str,
    current_user: UserInDB = Depends(get_current_user),
    cancel_booking_use_case: CancelBooking = Depends(get_cancel_booking_use_case),
):
    """
    Cancel a booking for the current user.

    This endpoint:
    1. Validates the booking id format
    2. Loads the booking for the current user
    3. Cancels the upstream flight order when present
    4. Updates the booking status and notifies the rest of the system

    Args:
        booking_id: UUID of the booking to cancel

    Returns:
        BookingCancellationResponse with cancellation status

    Raises:
        HTTPException 404: If booking not found
        HTTPException 403: If user doesn't own the booking
        HTTPException 400: If booking cannot be cancelled
    """
    logger.info(
        f"Booking cancellation initiated for booking_id: {booking_id}, user_id: {current_user.id}"
    )

    try:
        try:
            booking_uuid = uuid_module.UUID(booking_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid booking ID format")

        cancelled_booking = cancel_booking_use_case.execute(
            command=CancelBookingCommand(
                booking_id=booking_uuid,
                user_id=current_user.id,
                user_email=current_user.email,
            )
        )
        return BookingCancellationResponse(
            id=cancelled_booking.id,
            status=cancelled_booking.status,
            message=cancelled_booking.message,
        )

    except BookingNotFound:
        raise HTTPException(
            status_code=404,
            detail="Booking not found or you don't have permission to cancel it",
        )
    except BookingAlreadyCancelled:
        raise HTTPException(
            status_code=400,
            detail="This booking has already been cancelled",
        )
    except BookingCannotBeCancelled:
        raise HTTPException(
            status_code=400,
            detail="Booking with status 'reversed', 'failed', or 'refunded' cannot be cancelled",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            f"Error cancelling booking for booking_id: {booking_id}, user_id: {current_user.id}"
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while cancelling the booking",
        )


@router.get("/reference-data/locations", response_model=list[LocationSearchResponse])
async def search_locations(
    request: Annotated[LocationSearchRequest, Query()],
    location_search_use_case: SearchLocations = Depends(get_location_search_use_case),
):
    try:
        return location_search_use_case.execute(request.model_dump())
    except InvalidLocationSearchRequest:
        raise HTTPException(status_code=400, detail="Invalid location search request")
    except LocationSearchProviderError:
        raise HTTPException(
            status_code=500, detail="An error occurred while searching for a location"
        )
    except Exception:
        raise HTTPException(
            status_code=500, detail="An error occurred while searching for a location"
        )


@router.get("/bookings", response_model=CursorPaginatedUserBookingResponse)
async def get_user_bookings(
    cursor: str | None = Query(None, description="Cursor for pagination"),
    limit: int = Query(
        20,
        ge=1,
        le=MAX_PAGINATION_LIMIT,
        description="Maximum number of records to return",
    ),
    include_count: bool = Query(
        False,
        description="Include total_count in response (may be slower)",
    ),
    user: UserInDB = Depends(get_current_user),
    user_bookings_use_case: GetUserBookings = Depends(get_user_bookings_use_case),
):
    """
    Get cursor-paginated bookings for the current user.

    Args:
        cursor: Cursor for pagination (None for first page)
        limit: Maximum number of records to return (default: 20, max: 100)

    Returns:
        Cursor-paginated list of bookings with id, pnr, status, created_at, and ticket_url
    """
    try:
        user_bookings_page = user_bookings_use_case.execute(
            user_id=user.id,
            cursor=cursor,
            limit=limit,
            include_count=include_count,
        )
        response = CursorPaginatedUserBookingResponse(
            items=[
                UserBookingResponse(
                    id=booking.id,
                    pnr=booking.pnr,
                    status=booking.status,
                    created_at=booking.created_at,
                    ticket_url=booking.ticket_url,
                )
                for booking in user_bookings_page.items
            ],
            next_cursor=user_bookings_page.next_cursor,
            has_more=user_bookings_page.has_more,
            has_previous=user_bookings_page.has_previous,
            total_count=user_bookings_page.total_count,
            limit=user_bookings_page.limit,
        )
        logger.info(
            f"Successfully fetched {len(response.items)} bookings for user_id: {user.id} "
            f"(has_more: {response.has_more})"
        )
        return response

    except Exception:
        logger.exception(f"Error fetching bookings for user_id: {user.id}")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching bookings"
        )


@router.get("/analytics/most-travelled-destinations")
def get_most_travelled_destinations(
    origin_city_code: str,
    period: str,
    travelled_destinations_use_case: GetTravelledDestinations = Depends(
        get_travelled_destinations_use_case
    ),
):
    try:
        return travelled_destinations_use_case.execute(
            origin_city_code=origin_city_code,
            period=period,
        )
    except InvalidTravelledDestinationsRequest:
        raise HTTPException(
            status_code=400, detail="Invalid travelled destinations request"
        )
    except TravelledDestinationsProviderError:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching travelled destinations",
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching travelled destinations",
        )
