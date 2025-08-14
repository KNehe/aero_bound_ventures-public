from fastapi import APIRouter, HTTPException
from backend.external_services.flight import amadeus_flight_service
from backend.schemas.flights import (
    AmadeusFlightSearchRequest,
    FlightSearchResponse,
    FlightOfferRequest,
    FlightPricingResponse,
    FlightOrderRequest,
)

router = APIRouter()


@router.post("/flights/search", response_model=FlightSearchResponse)
async def search_flights(request: AmadeusFlightSearchRequest):
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


@router.post("/flights/price", response_model=FlightPricingResponse)
async def confirm_price(request: FlightOfferRequest):
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


@router.post("/flights/order")
async def flight_order(request: FlightOrderRequest):
    flight_data = request.flight_offer.model_dump()
    traveler_data = request.traveler.model_dump()
    response = amadeus_flight_service.create_flight_order(flight_data, traveler_data)
    return response
