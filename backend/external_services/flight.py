import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv

load_dotenv()


class AmadeusFlightService:
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
            response = self.amadeus.shopping.flight_offers_search.post(request_body)
            return response

        except ResponseError as api_error:
            raise Exception(f"{api_error}")

    def confirm_price(self, request_body: dict):
        try:
            response = self.amadeus.shopping.flight_offers.pricing.post(request_body)
            return response

        except ResponseError as error:
            raise error

    def create_flight_order(self, request_body: dict):
        try:
            travelers = request_body.get("travelers")

            body = {
                "originLocationCode": request_body.get("originLocationCode"),
                "destinationLocationCode": request_body.get("destinationLocationCode"),
                "departureDate": request_body.get("departureDate"),
                "adults": request_body.get("adults"),
            }

            if request_body.get("returnDate"):
                body.update({"returnDate": request_body.get("returnDate")})

            flight_search = self.amadeus.shopping.flight_offers_search.get(**body).data

            self.amadeus.shopping.flight_offers.pricing.post(flight_search[0]).data

            booked_flight = self.amadeus.booking.flight_orders.post(
                flight_search[0], travelers
            ).data

            return booked_flight

        except ResponseError as error:
            raise error

    def search_flights_get(self, request_body: dict) -> dict:
        try:
            print("REQUEST BODY")
            print(request_body)
            response = self.amadeus.shopping.flight_offers_search.get(
                **request_body
            ).data
            return response
        except ResponseError as error:
            raise error


# Create a singleton instance
amadeus_flight_service = AmadeusFlightService()
