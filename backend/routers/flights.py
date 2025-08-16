from fastapi import APIRouter, HTTPException, Query
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
from backend.schemas.flight_price_confirm import FlightOfferRequest
from backend.schemas.flight_order import FlightOrderRequestBody

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
    request_body = request.model_dump(exclude_none=True)
    response = amadeus_flight_service.search_flights_get(request_body)
    return response


@router.post("/shopping/flight-offers/pricing", response_model=FlightPricingResponse)
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


@router.post("/booking/flight-orders")
async def flight_order(request: FlightOrderRequestBody):
    """Create order associated with a flight"""
    request_body = request.model_dump(by_alias=True)

    response = amadeus_flight_service.create_flight_order(request_body)
    return response
