from fastapi import APIRouter, Depends, HTTPException, Query

from backend.application.bookings.create_flight_order import (
    CreateFlightOrder,
    FlightOrderProviderError,
    InvalidFlightOrderRequest,
)
from backend.application.bookings.get_flight_order_details import (
    FlightOrderDetailsNotFound,
    GetFlightOrderDetails,
)
from backend.application.flights.confirm_flight_price import (
    ConfirmFlightPrice,
    FlightPricingProviderError,
    InvalidFlightPricingRequest,
)
from backend.application.flights.search_flights import (
    FlightSearchProviderError,
    InvalidFlightSearchRequest,
    SearchFlights,
)
from backend.external_services.flight import amadeus_flight_service
from backend.infrastructure.bookings.booking_success_presenter import (
    BookingSuccessPresenter,
)
from backend.infrastructure.bookings.kafka_booking_event_publisher import (
    KafkaBookingEventPublisher,
)
from backend.infrastructure.bookings.redis_user_booking_cache import RedisUserBookingCache
from backend.infrastructure.bookings.sqlmodel_booking_repository import (
    SqlModelBookingRepository,
)
from backend.infrastructure.flights.amadeus_flight_order_gateway import (
    AmadeusFlightOrderGateway,
)
from backend.infrastructure.flights.amadeus_error_parser import (
    parse_amadeus_client_error,
)
from backend.infrastructure.flights.amadeus_pricing_gateway import AmadeusPricingGateway
from backend.infrastructure.flights.amadeus_search_gateway import AmadeusSearchGateway
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
from backend.models.bookings import Booking, BookingStatus
from backend.schemas.bookings import (
    BookingResponse,
    UserBookingResponse,
    BookingCancellationResponse,
    CursorPaginatedUserBookingResponse,
)
from backend.crud.database import get_session
from backend.crud.bookings import (
    get_user_bookings_cursor,
)
from backend.utils.pagination import MAX_PAGINATION_LIMIT
from backend.utils.log_manager import get_app_logger
from sqlmodel import Session, select
from backend.utils.kafka import kafka_producer
import uuid as uuid_module

from backend.utils.constants import KafkaTopics, KafkaEventTypes


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


def get_flight_order_details_use_case(
    session: Session = Depends(get_session),
) -> GetFlightOrderDetails:
    return GetFlightOrderDetails(
        booking_repository=SqlModelBookingRepository(session),
        presenter=BookingSuccessPresenter(),
    )


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
    flightorderId: Annotated[str, Query()],
    current_user: UserInDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        amadeus_order_id = flightorderId
        # Check if flightorderId is a database UUID
        try:
            booking_uuid = uuid_module.UUID(flightorderId)
            booking = session.exec(
                select(Booking)
                .where(Booking.id == booking_uuid)
                .where(Booking.user_id == current_user.id)
            ).first()

            if booking:
                amadeus_order_id = booking.flight_order_id
                logger.info(
                    f"Mapped booking UUID {flightorderId} to Amadeus order ID {amadeus_order_id}"
                )
            else:
                # If it's a UUID but not found in DB for this user, it's either someone else's or invalid
                raise HTTPException(
                    status_code=404, detail="Booking not found or access denied"
                )
        except ValueError:
            # Not a UUID, use as is (direct Amadeus ID)
            pass

        logger.info(
            f"Final Amadeus Flight Order ID for seatmap retrieval: {amadeus_order_id}"
        )
        response = amadeus_flight_service.view_seat_map_get(
            flightorderId=amadeus_order_id
        )
        return response
    except ClientError as e:
        error_detail = _parse_amadeus_client_error(e)
        raise HTTPException(status_code=400, detail=error_detail)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to retrieve seat map for ID: {flightorderId}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve seat map: {str(e)}"
        )


@router.post("/shopping/seatmaps")
async def view_seat_map_post(request: FlightOffer):
    try:
        request_body = request.model_dump()
        response = amadeus_flight_service.view_seat_map_post(request_body)
        return response
    except ClientError as e:
        error_detail = _parse_amadeus_client_error(e)
        raise HTTPException(status_code=400, detail=error_detail)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve seat map: {str(e)}"
        )


@router.get("/booking/flight-orders/{booking_id}")
async def get_flight_order(
    booking_id: str,
    current_user: UserInDB = Depends(get_current_user),
    flight_order_details_use_case: GetFlightOrderDetails = Depends(
        get_flight_order_details_use_case
    ),
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

        booking_details = flight_order_details_use_case.execute(
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
    except FlightOrderDetailsNotFound:
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
async def cancel_flight_order(
    booking_id: str,
    current_user: UserInDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Cancel a booking for the current user.

    This endpoint:
    1. Validates the booking exists and belongs to the user
    2. Checks if the booking is eligible for cancellation
    3. Calls Amadeus API to cancel the flight order
    4. Updates the booking status in the database
    5. Invalidates the user's booking cache
    6. Sends a Kafka event for notification to user and admins

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
        # Validate UUID format
        try:
            booking_uuid = uuid_module.UUID(booking_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid booking ID format")

        # 1. Get the booking from database
        booking = session.exec(
            select(Booking)
            .where(Booking.id == booking_uuid)
            .where(Booking.user_id == current_user.id)
        ).first()

        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Booking not found or you don't have permission to cancel it",
            )

        # 2. Check if booking is already cancelled
        if booking.status == BookingStatus.CANCELLED:
            raise HTTPException(
                status_code=400,
                detail="This booking has already been cancelled",
            )

        # 3. Check if booking can be cancelled (only confirmed, pending, or paid bookings)
        non_cancellable_statuses = [
            BookingStatus.REVERSED,
            BookingStatus.FAILED,
            BookingStatus.REFUNDED,
        ]
        if booking.status in non_cancellable_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Booking with status '{booking.status}' cannot be cancelled",
            )

        # 4. Get PNR for notification before cancellation
        pnr = None
        if booking.amadeus_order_response:
            associated_records = booking.amadeus_order_response.get(
                "associatedRecords", []
            )
            if associated_records:
                pnr = associated_records[0].get("reference")

        # 5. Cancel flight order in Amadeus (if flight_order_id exists)
        if booking.flight_order_id:
            try:
                amadeus_flight_service.cancel_flight_order(booking.flight_order_id)
                logger.info(
                    f"Successfully cancelled flight order in Amadeus: {booking.flight_order_id}"
                )
            except ClientError as e:
                logger.warning(f"Failed to cancel in Amadeus: {str(e)}")
                # Continue with local cancellation even if Amadeus fails
                # This handles cases where the order was already cancelled externally

        # 6. Update booking status in database
        booking.status = BookingStatus.CANCELLED
        session.add(booking)
        session.commit()
        session.refresh(booking)

        # 7. Invalidate user's booking cache
        pattern = f"user_bookings:{str(current_user.id)}*"
        redis_cache.delete_pattern(pattern)

        # 8. Send Kafka event for notification (user and admins)
        kafka_producer.send(
            KafkaTopics.BOOKING_EVENTS,
            {
                "event_type": KafkaEventTypes.BOOKING_CANCELLED,
                "booking_id": str(booking.id),
                "user_id": str(current_user.id),
                "pnr": pnr,
                "user_email": current_user.email,
            },
        )

        logger.info(
            f"Booking successfully cancelled for booking_id: {booking_id}, user_id: {current_user.id}"
        )

        return BookingCancellationResponse(
            id=booking.id,
            status=booking.status,
            message="Booking has been successfully cancelled",
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception(
            f"Error cancelling booking for booking_id: {booking_id}, user_id: {current_user.id}"
        )
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while cancelling the booking",
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
    return parse_amadeus_client_error(error)


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
    session: Session = Depends(get_session),
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
        cache_key = build_redis_key(
            {"user_bookings": str(user.id), "cursor": cursor or "first", "limit": limit}
        )
        cached_response = redis_cache.get(cache_key)
        if cached_response:
            logger.info(
                f"Returning cached bookings for user_id: {user.id}, cursor: {cursor}, limit: {limit}"
            )
            return cached_response

        logger.info(
            f"Fetching bookings for user_id: {user.id}, cursor: {cursor}, limit: {limit}"
        )

        bookings, next_cursor, has_more, total_count = get_user_bookings_cursor(
            session, user.id, cursor=cursor, limit=limit, include_count=include_count
        )

        items = []
        for booking in bookings:
            pnr = None
            if booking.amadeus_order_response:
                associated_records = booking.amadeus_order_response.get(
                    "associatedRecords", []
                )
                if associated_records:
                    pnr = associated_records[0].get("reference")

            items.append(
                UserBookingResponse(
                    id=booking.id,
                    pnr=pnr,
                    status=booking.status,
                    created_at=booking.created_at,
                    ticket_url=booking.ticket_url,
                )
            )

        response = CursorPaginatedUserBookingResponse(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
            has_previous=cursor is not None,
            total_count=total_count,
            limit=limit,
        )

        redis_cache.set(cache_key, response.model_dump(mode="json"))

        logger.info(
            f"Successfully fetched {len(items)} bookings for user_id: {user.id} (has_more: {has_more})"
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
