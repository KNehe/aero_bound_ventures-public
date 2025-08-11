import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv

load_dotenv()


class AmadeusFlightService:
    """Service for interacting with Amadeus Flight Search API using the Amadeus SDK"""

    def __init__(self):
        self.api_key = os.getenv("AMADEUS_API_KEY")
        self.api_secret = os.getenv("AMADEUS_API_SECRET")

        if not self.api_key or not self.api_secret:
            raise ValueError("Amadeus API credentials not configured")

        try:
            self.amadeus = Client(client_id=self.api_key, client_secret=self.api_secret)
        except Exception as e:
            raise Exception(f"Failed to create Amadeus client: {str(e)}")

    def search_flights(self, request_body: dict) -> dict:
        try:
            try:
                response = self.amadeus.shopping.flight_offers_search.post(request_body)

                if hasattr(response, "result"):
                    flight_data = response.result.get("data", [])
                    dictionaries = response.result.get("dictionaries", {})
                    meta = response.result.get("meta", {})

                    result = {
                        "data": flight_data,
                        "dictionaries": dictionaries,
                        "meta": meta,
                    }

                    return result
                else:
                    # Fallback: return empty response
                    return {"data": [], "meta": {"count": 0}, "dictionaries": {}}

            except ResponseError as api_error:
                print(f"Amadeus API error: {api_error}")
                raise Exception(f"{api_error}")

        except Exception as e:
            print(f"Error processing flight search: {e}")
            raise Exception(f"{e}")

    def confirm_price(self, request_body: dict):
        try:
            # Log the request for debugging
            print(
                f"Confirming price for flight offer: {request_body.get('id', 'unknown')}"
            )

            # Validate that required fields are present
            required_fields = [
                "type",
                "id",
                "source",
                "itineraries",
                "price",
                "travelerPricings",
            ]
            for field in required_fields:
                if field not in request_body:
                    raise ValueError(f"Missing required field: {field}")

            response = self.amadeus.shopping.flight_offers.pricing.post(request_body)

            if hasattr(response, "data"):
                return {"data": response.data}
            elif hasattr(response, "result"):
                return {"result": response.result}
            else:
                return {"data": response}

        except ResponseError as api_error:
            print(f"Amadeus API error in confirm_price: {api_error}")
            raise Exception(f"Amadeus API error: {api_error}")
        except Exception as e:
            print(f"Error processing price confirmation: {e}")
            raise Exception(f"Price confirmation failed: {str(e)}")


# Create a singleton instance
amadeus_flight_service = AmadeusFlightService()
