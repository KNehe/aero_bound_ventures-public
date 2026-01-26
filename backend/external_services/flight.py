import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv
import requests
from amadeus import Location

load_dotenv()


class AmadeusFlightService:
    def __init__(self):
        self.api_key, self.api_secret = self.get_amadeus_credentials()

        try:
            self.amadeus = Client(client_id=self.api_key, client_secret=self.api_secret)
        except Exception as e:
            raise Exception(f"Failed to create Amadeus client: {str(e)}")

    def get_amadeus_credentials(self) -> tuple[str, str]:
        api_key = os.getenv("AMADEUS_API_KEY")
        api_secret = os.getenv("AMADEUS_API_SECRET")
        if not api_key or not api_secret:
            raise ValueError("Amadeus API credentials not configured")
        return (api_key, api_secret)

    def get_amadeus_access_token(self) -> str:
        """
        Retrieves an Amadeus access token using client credentials from environment variables.

        Returns:
            The access token string if the request is successful.
        """
        client_id, client_secret = self.get_amadeus_credentials()

        url = "https://test.api.amadeus.com/v1/security/oauth2/token"

        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            response_json = response.json()
            return response_json.get("access_token")

        except requests.exceptions.RequestException as e:
            raise e

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
        """
        Creates a flight order using a pre-selected and price-confirmed flight offer.

        IMPORTANT: The flight offer must be recent (from a fresh search/pricing call).
        Amadeus flight offers expire quickly and cannot be booked after they become stale.
        """
        try:
            flight_offer = request_body.get("flight_offer")
            travelers = request_body.get("travelers")

            if not flight_offer:
                raise ValueError("flight_offer is required in request body")
            if not travelers:
                raise ValueError("travelers information is required")

            # The Amadeus SDK expects flight_offer and travelers as separate arguments
            booked_flight = self.amadeus.booking.flight_orders.post(
                flight_offer, travelers
            ).data

            return booked_flight

        except ResponseError as error:
            # Log the error for debugging
            print(f"Amadeus API Error: {error}")
            if hasattr(error, "response"):
                print(f"Response body: {error.response.body}")
            raise error

    def search_flights_get(self, request_body: dict) -> dict:
        try:
            response = self.amadeus.shopping.flight_offers_search.get(
                **request_body
            ).data
            return response
        except ResponseError as error:
            raise error

    def view_seat_map_get(self, flightorderId: str) -> dict:
        try:
            response = self.amadeus.shopping.seatmaps.get(
                flightOrderId=flightorderId
            ).data
            return response
        except ResponseError as error:
            raise error

    def view_seat_map_post(self, flight_offer: dict) -> dict:
        try:
            body = {"data": [flight_offer]}
            print("=" * 80)
            print("SEAT MAP REQUEST BODY:")
            print(f"Flight Offer Keys: {flight_offer.keys()}")
            print(f"Full body being sent to Amadeus: {body}")
            print("=" * 80)
            response = self.amadeus.shopping.seatmaps.post(body).data
            return response
        except ResponseError as error:
            print(f"Amadeus Seat Map Error: {error}")
            raise error

    def get_flight_order(self, flight_orderId: str) -> dict:
        """
        Retrieves flight order details using the Amadeus Flight Orders API.

        Args:
            flight_order_id (str): The ID of the flight order to retrieve.

        Returns:
            dict: The flight order details.
        """
        try:
            response = self.amadeus.booking.flight_order(flight_orderId).get()
            return response.data
        except ResponseError as error:
            raise error

    def cancel_flight_order(self, flight_orderId: str) -> dict:
        """
        Cancels flight order details using the Amadeus Flight Orders API.

        Args:
            flight_order_id (str): The ID of the flight order to retrieve.

        Returns:
            dict: The flight order details.
        """
        try:
            response = self.amadeus.booking.flight_order(flight_orderId).delete()
            return response
        except ResponseError as error:
            raise error

    def airport_city_search(self, request_body: dict) -> dict:
        try:
            keyword = request_body.get("keyword")
            sub_type = request_body.get("sub_type", "ANY")
            if sub_type.upper() == "AIRPORT":
                sub_type = Location.AIRPORT
            elif sub_type.upper() == "CITY":
                sub_type = Location.CITY
            else:
                sub_type = Location.ANY

            response = self.amadeus.reference_data.locations.get(
                keyword=keyword, subType=sub_type
            )
            return response.data
        except ResponseError as error:
            raise error

    def get_flight_orders(self, flight_order_ids: list[str]):
        try:
            """
             Retrieve multiple flight orders based on their ids
            """
            flight_orders = []
            for order_id in flight_order_ids:
                response = self.amadeus.booking.flight_order(order_id).get()
                flight_orders.append(response.data)
            return flight_orders
        except ResponseError as error:
            raise error

    def get_most_travelled_destinations(
        self, origin_city_code: str, period: str
    ) -> list[dict]:
        """
        Fetches the most travelled destinations from a given origin city and period using Amadeus API.
        Args:
            origin_city_code (str): IATA code of the origin city (e.g., 'MAD').
            period (str): Period in 'YYYY-MM' format (e.g., '2017-01').
        Returns:
            list[dict]: List of destination data dictionaries.
        """
        try:
            response = self.amadeus.travel.analytics.air_traffic.traveled.get(
                originCityCode=origin_city_code, period=period
            )
            return response.data
        except ResponseError as error:
            raise error


amadeus_flight_service = AmadeusFlightService()
