"""
Mock flight service implementation for demo/development mode.

Returns realistic pre-built JSON fixtures instead of calling external flight APIs.
Activated by setting FLIGHT_SERVICE_PROVIDER=mock in the environment.
"""

import json
import copy
import uuid
from datetime import datetime
from pathlib import Path

from backend.utils.log_manager import get_app_logger

logger = get_app_logger(__name__)


MOCK_DATA_DIR = Path(__file__).parent / "mock_data"


def _load_fixture(filename: str):
    """Load a JSON fixture file from the mock_data directory."""
    filepath = MOCK_DATA_DIR / filename
    with open(filepath, "r") as f:
        return json.load(f)


class MockFlightService:
    """
    Flight service that returns cached/static mock data.

    Implements the same interface as AmadeusFlightService so it can be
    swapped in transparently via the FLIGHT_SERVICE_PROVIDER env var.
    """

    def __init__(self):
        logger.info("MockFlightService initialized — using mock flight data")
        self._flight_search = _load_fixture("flight_search_results.json")
        self._flight_pricing = _load_fixture("flight_pricing.json")
        self._flight_order = _load_fixture("flight_order.json")
        self._seat_map = _load_fixture("seat_map.json")
        self._airport_search = _load_fixture("airport_search.json")
        self._destinations = _load_fixture("destinations.json")

        self._created_orders: dict[str, dict] = {}

    def search_flights(self, request_body: dict) -> dict:
        """Return mock flight search results (POST variant)."""
        logger.info("[mock] search_flights (POST) called")
        return _MockResponse(data=copy.deepcopy(self._flight_search))

    def search_flights_get(self, request_body: dict) -> dict:
        """Return mock flight search results (GET variant), with optional filtering."""
        origin = request_body.get("originLocationCode", "any")
        destination = request_body.get("destinationLocationCode", "any")
        logger.info(f"[mock] search_flights (GET) called — {origin} → {destination}")
        results = copy.deepcopy(self._flight_search)

        origin = request_body.get("originLocationCode")
        destination = request_body.get("destinationLocationCode")

        if origin or destination:
            filtered = []
            for offer in results:
                segments = offer.get("itineraries", [{}])[0].get("segments", [])
                if segments:
                    first_seg = segments[0]
                    last_seg = segments[-1]
                    origin_match = (
                        not origin
                        or first_seg.get("departure", {}).get("iataCode") == origin
                    )
                    dest_match = (
                        not destination
                        or last_seg.get("arrival", {}).get("iataCode") == destination
                    )
                    if origin_match and dest_match:
                        filtered.append(offer)
            # If filters match nothing, return all results (better demo experience)
            return filtered if filtered else results

        return results

    def confirm_price(self, request_body: dict) -> dict:
        """Return mock pricing confirmation."""
        logger.info("[mock] confirm_price called")
        return _MockResponse(data=copy.deepcopy(self._flight_pricing))

    def create_flight_order(self, request_body: dict) -> dict:
        """Create a mock flight order and store it in memory."""
        logger.info("[mock] create_flight_order called")
        order = copy.deepcopy(self._flight_order)

        # Generate a unique order ID and PNR
        order_id = f"MOCK_{uuid.uuid4().hex[:8].upper()}"
        mock_pnr = f"MK{uuid.uuid4().hex[:4].upper()}"

        order["id"] = order_id
        if order.get("associatedRecords"):
            order["associatedRecords"][0]["reference"] = mock_pnr
            order["associatedRecords"][0]["creationDate"] = datetime.now().strftime(
                "%Y-%m-%d"
            )

        # Use travelers from request if provided
        travelers = request_body.get("travelers")
        if travelers:
            order["travelers"] = travelers

        # Store for later retrieval
        self._created_orders[order_id] = order

        return order

    def view_seat_map_get(self, flightorderId: str) -> dict:
        """Return mock seat map data."""
        logger.info(f"[mock] view_seat_map_get called — order: {flightorderId}")
        return copy.deepcopy(self._seat_map)

    def view_seat_map_post(self, flight_offer: dict) -> dict:
        """Return mock seat map data for a flight offer."""
        logger.info("[mock] view_seat_map_post called")
        return copy.deepcopy(self._seat_map)

    def get_flight_order(self, flight_orderId: str) -> dict:
        """Retrieve a mock flight order by ID."""
        source = "memory" if flight_orderId in self._created_orders else "fixture"
        logger.info(f"[mock] get_flight_order called — id: {flight_orderId} (from {source})")
        # Check in-memory store first, then fall back to fixture
        if flight_orderId in self._created_orders:
            return copy.deepcopy(self._created_orders[flight_orderId])
        return copy.deepcopy(self._flight_order)

    def cancel_flight_order(self, flight_orderId: str) -> dict:
        """Simulate cancelling a flight order."""
        logger.info(f"[mock] cancel_flight_order called — id: {flight_orderId}")
        # Remove from in-memory store if present
        self._created_orders.pop(flight_orderId, None)
        return _MockResponse(status_code=204, data=None)

    def airport_city_search(self, request_body: dict) -> dict:
        """Return mock airport/city search results, filtered by keyword."""
        keyword = request_body.get("keyword", "").upper()
        logger.info(f"[mock] airport_city_search called — keyword: {keyword or 'all'}")
        results = copy.deepcopy(self._airport_search)

        if keyword:
            filtered = [
                loc
                for loc in results
                if keyword in loc.get("name", "").upper()
                or keyword in loc.get("iataCode", "").upper()
                or keyword
                in loc.get("address", {}).get("cityName", "").upper()
                or keyword
                in loc.get("address", {}).get("countryName", "").upper()
            ]
            return filtered if filtered else results

        return results

    def get_flight_orders(self, flight_order_ids: list[str]) -> list:
        """Retrieve multiple mock flight orders."""
        logger.info(f"[mock] get_flight_orders called — {len(flight_order_ids)} order(s)")
        orders = []
        for order_id in flight_order_ids:
            orders.append(self.get_flight_order(order_id))
        return orders

    def get_most_travelled_destinations(
        self, origin_city_code: str, period: str
    ) -> list[dict]:
        """Return mock popular destinations data."""
        logger.info(f"[mock] get_most_travelled_destinations called — origin: {origin_city_code}, period: {period}")
        return copy.deepcopy(self._destinations)

    def get_amadeus_access_token(self) -> str:
        """Return a dummy access token for mock mode."""
        logger.info("[mock] get_amadeus_access_token called — returning dummy token")
        return "mock-access-token-for-demo-purposes"


class _MockResponse:
    """
    Minimal mock of the Amadeus SDK Response object.

    The AmadeusFlightService methods return the raw SDK response in some cases
    (search_flights, confirm_price), which has a .data attribute. This class
    mimics that interface so the router code works without changes.
    """

    def __init__(self, data=None, status_code=200):
        self.data = data
        self.status_code = status_code
        self.body = json.dumps(data) if data else ""

    def __getitem__(self, key):
        if isinstance(self.data, dict):
            return self.data[key]
        raise KeyError(key)
