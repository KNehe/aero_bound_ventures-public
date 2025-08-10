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
                raise Exception(f"Amadeus API error: {api_error}")

        except Exception as e:
            print(f"Error processing flight search: {e}")
            raise Exception(f"Error processing flight search: {str(e)}")


# Create a singleton instance
amadeus_flight_service = AmadeusFlightService()
