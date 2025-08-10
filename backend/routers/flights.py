from fastapi import APIRouter, HTTPException
from backend.external_services.flight import amadeus_flight_service
from backend.schemas.flights import AmadeusFlightSearchRequest, FlightSearchResponse

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
