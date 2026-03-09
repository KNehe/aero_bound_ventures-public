"""
Flight service protocol defining the contract for all flight service implementations.

This protocol enables the Strategy pattern, allowing seamless switching between
providers (Amadeus, Mock, etc.) via the FLIGHT_SERVICE_PROVIDER env var.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class FlightServiceProtocol(Protocol):
    """Protocol defining the interface for flight service implementations."""

    def search_flights(self, request_body: dict) -> dict:
        """Search for flights using a POST request body."""
        ...

    def search_flights_get(self, request_body: dict) -> dict:
        """Search for flights using GET query parameters."""
        ...

    def confirm_price(self, request_body: dict) -> dict:
        """Confirm pricing for a selected flight offer."""
        ...

    def create_flight_order(self, request_body: dict) -> dict:
        """Create a flight order from a price-confirmed offer."""
        ...

    def view_seat_map_get(self, flightorderId: str) -> dict:
        """Retrieve seat map using a flight order ID."""
        ...

    def view_seat_map_post(self, flight_offer: dict) -> dict:
        """Retrieve seat map using a flight offer payload."""
        ...

    def get_flight_order(self, flight_orderId: str) -> dict:
        """Retrieve a single flight order by ID."""
        ...

    def cancel_flight_order(self, flight_orderId: str) -> dict:
        """Cancel a flight order by ID."""
        ...

    def airport_city_search(self, request_body: dict) -> dict:
        """Search for airports and cities by keyword."""
        ...

    def get_flight_orders(self, flight_order_ids: list[str]) -> list:
        """Retrieve multiple flight orders by their IDs."""
        ...

    def get_most_travelled_destinations(
        self, origin_city_code: str, period: str
    ) -> list[dict]:
        """Fetch most travelled destinations from an origin city."""
        ...

    def get_amadeus_access_token(self) -> str:
        """Retrieve an API access token (or mock equivalent)."""
        ...
