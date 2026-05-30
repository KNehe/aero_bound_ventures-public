import uuid
from datetime import datetime, timezone

import pytest

from backend.application.bookings.create_flight_order import CreatedFlightBooking
from backend.application.bookings.cancel_booking import CancelledBooking
from backend.application.bookings.get_user_bookings import (
    BookingListItemRecord,
    UserBookingsPage,
)
from backend.application.payments.initiate_payment import (
    InitiatedPayment,
)
from backend.application.payments.payment_status import PaymentStatus
from backend.application.payments.process_payment_callback import (
    ProcessedPaymentCallback,
)
from backend.application.payments.process_payment_notification import (
    ProcessedPaymentNotification,
)
from backend.application.payments.request_payment_refund import RequestedPaymentRefund
from backend.crud.users import create_user
from backend.routers.flights import (
    get_cancel_booking_use_case,
    get_confirm_flight_price_use_case,
    get_create_flight_order_use_case,
    get_booking_details_use_case,
    get_user_bookings_use_case,
    get_search_flights_use_case,
)
from backend.routers.payments import get_payment_status_use_case
from backend.routers.payments import get_initiate_payment_use_case
from backend.routers.payments import get_process_payment_callback_use_case
from backend.routers.payments import get_process_payment_notification_use_case
from backend.routers.payments import get_request_payment_refund_use_case


API_V1_PREFIX = "/api/v1"


class StubSearchFlightsUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, criteria):
        self.calls.append(criteria)
        return [{"id": "flight_1"}]


class StubConfirmFlightPriceUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, flight_offer):
        self.calls.append(flight_offer)
        return {"data": {"flightOffers": []}}


class StubCreateFlightOrderUseCase:
    def __init__(self):
        self.calls = []
        self.booking_id = uuid.uuid4()

    def execute(self, *, user_id, user_email, order_request):
        self.calls.append(
            {
                "user_id": user_id,
                "user_email": user_email,
                "order_request": order_request,
            }
        )
        return CreatedFlightBooking(
            id=self.booking_id,
            flight_order_id="AMADEUS_ORDER_1",
            status="confirmed",
        )


class StubCancelBookingUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, *, command):
        self.calls.append(command)
        return CancelledBooking(
            id=command.booking_id,
            status="cancelled",
            message="Booking has been successfully cancelled",
        )


class StubBookingDetailsUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, *, booking_id, user_id, user_email):
        self.calls.append(
            {
                "booking_id": booking_id,
                "user_id": user_id,
                "user_email": user_email,
            }
        )
        return {
            "orderId": str(booking_id),
            "status": "confirmed",
            "ticket_url": "https://tickets.example.com/ticket.pdf",
        }


class StubUserBookingsUseCase:
    def __init__(self):
        self.calls = []
        self.booking_id = uuid.uuid4()

    def execute(self, *, user_id, cursor, limit, include_count):
        self.calls.append(
            {
                "user_id": user_id,
                "cursor": cursor,
                "limit": limit,
                "include_count": include_count,
            }
        )
        return UserBookingsPage(
            items=[
                BookingListItemRecord(
                    id=self.booking_id,
                    pnr="PNR123",
                    status="confirmed",
                    created_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
                    ticket_url="https://tickets.example.com/ticket.pdf",
                )
            ],
            next_cursor="cursor_2",
            has_more=False,
            has_previous=False,
            total_count=1,
            limit=limit,
        )


class StubInitiatePaymentUseCase:
    def __init__(self):
        self.calls = []

    async def execute(self, *, user_id, command):
        self.calls.append({"user_id": user_id, "command": command})
        return InitiatedPayment(
            payment_order_id="track_123",
            merchant_reference=command.booking_id,
            redirect_url="https://pesapal.com/pay/123",
            status="200",
        )


class StubProcessPaymentCallbackUseCase:
    def __init__(self):
        self.calls = []

    async def execute(self, command):
        self.calls.append(command)
        return ProcessedPaymentCallback(
            status="success",
            message="Payment completed successfully",
            payment_order_id=command.payment_order_id,
            payment_method="Visa",
            amount=100,
            confirmation_code="CONFIRM123",
        )


class StubProcessPaymentNotificationUseCase:
    def __init__(self):
        self.calls = []

    async def execute(self, command):
        self.calls.append(command)
        return ProcessedPaymentNotification(
            payment_order_id=command.payment_order_id or "",
            merchant_reference=command.merchant_reference or "",
            status=200,
        )


class StubGetPaymentStatusUseCase:
    def __init__(self):
        self.calls = []

    async def execute(self, payment_order_id: str):
        self.calls.append(payment_order_id)
        return PaymentStatus(
            payment_method="Visa",
            amount=100,
            created_date="2026-05-30T10:00:00Z",
            confirmation_code="CONFIRM123",
            payment_status_description="Completed",
            description="Payment completed",
            message="Request processed successfully",
            payment_account="476173**0010",
            call_back_url="https://frontend.com/callback",
            status_code=1,
            merchant_reference="booking_123",
            payment_status_code="COMPLETED",
            currency="USD",
        )


class StubRequestPaymentRefundUseCase:
    def __init__(self):
        self.calls = []

    async def execute(self, *, user_id, user_email, command):
        self.calls.append(
            {
                "user_id": user_id,
                "user_email": user_email,
                "command": command,
            }
        )
        return RequestedPaymentRefund(
            status="200",
            message="Refund request submitted",
            confirmation_code=command.confirmation_code,
        )


@pytest.fixture
def test_user(session):
    return create_user(session, "test_external@example.com", "password")


@pytest.fixture
def auth_header(client, test_user):
    # Overrides the authentication dependency to use the test user
    from backend.utils.security import get_current_user

    client.app.dependency_overrides[get_current_user] = lambda: test_user
    yield
    client.app.dependency_overrides.clear()


def test_initiate_payment_route_uses_payment_use_case(client, test_user, auth_header):
    use_case = StubInitiatePaymentUseCase()
    client.app.dependency_overrides[get_initiate_payment_use_case] = lambda: use_case
    payload = {
        "booking_id": "booking_123",
        "amount": 100.0,
        "description": "Test payment",
        "callback_url": "https://frontend.com/callback",
        "billing_address": {
            "email_address": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        },
    }
    try:
        response = client.post(
            f"{API_V1_PREFIX}/payments/pesapal/initiate", json=payload
        )
    finally:
        client.app.dependency_overrides.pop(get_initiate_payment_use_case, None)

    assert response.status_code == 200
    assert response.json()["redirect_url"] == "https://pesapal.com/pay/123"
    assert len(use_case.calls) == 1
    assert use_case.calls[0]["user_id"] == test_user.id
    command = use_case.calls[0]["command"]
    assert command.booking_id == "booking_123"
    assert command.amount == 100.0
    assert command.currency == "USD"
    assert command.callback_url == "https://frontend.com/callback"
    assert command.billing_address.email_address == "test@example.com"


def test_payment_callback_route_uses_callback_use_case(client):
    use_case = StubProcessPaymentCallbackUseCase()
    client.app.dependency_overrides[get_process_payment_callback_use_case] = (
        lambda: use_case
    )

    try:
        response = client.get(
            f"{API_V1_PREFIX}/payments/pesapal/callback",
            params={
                "OrderTrackingId": "track_123",
                "OrderMerchantReference": "booking_123-1234567890",
            },
        )
    finally:
        client.app.dependency_overrides.pop(get_process_payment_callback_use_case, None)

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Payment completed successfully",
        "order_tracking_id": "track_123",
        "payment_method": "Visa",
        "amount": 100,
        "confirmation_code": "CONFIRM123",
    }
    assert len(use_case.calls) == 1
    assert use_case.calls[0].payment_order_id == "track_123"
    assert use_case.calls[0].merchant_reference == "booking_123-1234567890"


def test_payment_notification_route_uses_notification_use_case(client):
    use_case = StubProcessPaymentNotificationUseCase()
    client.app.dependency_overrides[get_process_payment_notification_use_case] = (
        lambda: use_case
    )

    try:
        response = client.get(
            f"{API_V1_PREFIX}/payments/pesapal/ipn",
            params={
                "OrderTrackingId": "track_123",
                "OrderMerchantReference": "booking_123-1234567890",
                "OrderNotificationType": "IPNCHANGE",
            },
        )
    finally:
        client.app.dependency_overrides.pop(
            get_process_payment_notification_use_case, None
        )

    assert response.status_code == 200
    assert response.json() == {
        "orderNotificationType": "IPNCHANGE",
        "orderTrackingId": "track_123",
        "orderMerchantReference": "booking_123-1234567890",
        "status": 200,
    }
    assert len(use_case.calls) == 1
    assert use_case.calls[0].payment_order_id == "track_123"
    assert use_case.calls[0].merchant_reference == "booking_123-1234567890"
    assert use_case.calls[0].notification_type == "IPNCHANGE"


def test_payment_status_route_uses_status_use_case(client, auth_header):
    use_case = StubGetPaymentStatusUseCase()
    client.app.dependency_overrides[get_payment_status_use_case] = lambda: use_case

    try:
        response = client.get(
            f"{API_V1_PREFIX}/payments/pesapal/status/track_123",
        )
    finally:
        client.app.dependency_overrides.pop(get_payment_status_use_case, None)

    assert response.status_code == 200
    assert response.json() == {
        "payment_method": "Visa",
        "amount": 100.0,
        "created_date": "2026-05-30T10:00:00Z",
        "confirmation_code": "CONFIRM123",
        "payment_status_description": "Completed",
        "description": "Payment completed",
        "message": "Request processed successfully",
        "payment_account": "476173**0010",
        "call_back_url": "https://frontend.com/callback",
        "status_code": 1,
        "merchant_reference": "booking_123",
        "payment_status_code": "COMPLETED",
        "currency": "USD",
        "error": None,
    }
    assert use_case.calls == ["track_123"]


def test_request_refund_route_uses_refund_use_case(client, test_user, auth_header):
    use_case = StubRequestPaymentRefundUseCase()
    client.app.dependency_overrides[get_request_payment_refund_use_case] = (
        lambda: use_case
    )
    payload = {
        "confirmation_code": "CONFIRM123",
        "amount": 25.5,
        "remarks": "Customer requested itinerary change",
    }

    try:
        response = client.post(f"{API_V1_PREFIX}/payments/pesapal/refund", json=payload)
    finally:
        client.app.dependency_overrides.pop(get_request_payment_refund_use_case, None)

    assert response.status_code == 200
    assert response.json() == {
        "status": "200",
        "message": "Refund request submitted",
        "confirmation_code": "CONFIRM123",
    }
    assert len(use_case.calls) == 1
    assert use_case.calls[0]["user_id"] == test_user.id
    assert use_case.calls[0]["user_email"] == test_user.email
    command = use_case.calls[0]["command"]
    assert command.confirmation_code == "CONFIRM123"
    assert command.amount == 25.5
    assert command.remarks == "Customer requested itinerary change"


def test_search_flights_mock(client):
    use_case = StubSearchFlightsUseCase()
    client.app.dependency_overrides[get_search_flights_use_case] = lambda: use_case

    params = {
        "originLocationCode": "NYC",
        "destinationLocationCode": "LON",
        "departureDate": "2024-12-01",
        "adults": 1,
    }
    try:
        response = client.get(f"{API_V1_PREFIX}/shopping/flight-offers", params=params)
    finally:
        client.app.dependency_overrides.pop(get_search_flights_use_case, None)

    assert response.status_code == 200
    assert response.json() == [{"id": "flight_1"}]
    assert use_case.calls == [
        {
            "originLocationCode": "NYC",
            "destinationLocationCode": "LON",
            "departureDate": "2024-12-01",
            "adults": 1,
            "max": 5,
            "currencyCode": "USD",
        }
    ]


def test_confirm_price_route_uses_pricing_use_case(client):
    use_case = StubConfirmFlightPriceUseCase()
    client.app.dependency_overrides[get_confirm_flight_price_use_case] = (
        lambda: use_case
    )
    # Minimal flight offer payload matching FlightOffer schema
    payload = {
        "type": "flight-offer",
        "id": "1",
        "source": "GDS",
        "instantTicketingRequired": False,
        "nonHomogeneous": False,
        "oneWay": False,
        "isUpsellOffer": False,
        "lastTicketingDate": "2024-11-01",
        "numberOfBookableSeats": 1,
        "lastTicketingDateTime": "2024-11-01",
        "itineraries": [],
        "price": {
            "currency": "USD",
            "total": "100.0",
            "base": "90.0",
            "fees": [],
            "grandTotal": "100.0",
        },
        "pricingOptions": {"fareType": ["PUBLISHED"], "includedCheckedBagsOnly": False},
        "validatingAirlineCodes": ["AA"],
        "travelerPricings": [],
    }
    try:
        response = client.post(
            f"{API_V1_PREFIX}/shopping/flight-offers/pricing", json=payload
        )
    finally:
        client.app.dependency_overrides.pop(get_confirm_flight_price_use_case, None)

    assert response.status_code == 200
    assert response.json() == {
        "data": {"flightOffers": []},
        "result": None,
        "meta": None,
    }
    assert len(use_case.calls) == 1
    assert use_case.calls[0]["id"] == "1"
    assert use_case.calls[0]["price"] == {
        "currency": "USD",
        "total": "100.0",
        "base": "90.0",
        "fees": [],
        "grandTotal": "100.0",
        "billingCurrency": None,
        "taxes": None,
        "refundableTaxes": None,
    }


def test_create_flight_order_route_uses_create_flight_order_use_case(
    client, test_user, auth_header
):
    use_case = StubCreateFlightOrderUseCase()
    client.app.dependency_overrides[get_create_flight_order_use_case] = lambda: use_case
    payload = {
        "flight_offer": {"id": "offer_1"},
        "travelers": [{"id": "1"}],
    }

    try:
        response = client.post(f"{API_V1_PREFIX}/booking/flight-orders", json=payload)
    finally:
        client.app.dependency_overrides.pop(get_create_flight_order_use_case, None)

    assert response.status_code == 200
    assert response.json() == {
        "id": str(use_case.booking_id),
        "flight_order_id": "AMADEUS_ORDER_1",
        "status": "confirmed",
    }
    assert use_case.calls == [
        {
            "user_id": test_user.id,
            "user_email": test_user.email,
            "order_request": payload,
        }
    ]


def test_get_booking_details_route_uses_booking_details_use_case(
    client, test_user, auth_header
):
    use_case = StubBookingDetailsUseCase()
    booking_id = uuid.uuid4()
    client.app.dependency_overrides[get_booking_details_use_case] = lambda: use_case

    try:
        response = client.get(f"{API_V1_PREFIX}/booking/flight-orders/{booking_id}")
    finally:
        client.app.dependency_overrides.pop(get_booking_details_use_case, None)

    assert response.status_code == 200
    assert response.json() == {
        "orderId": str(booking_id),
        "status": "confirmed",
        "ticket_url": "https://tickets.example.com/ticket.pdf",
    }
    assert use_case.calls == [
        {
            "booking_id": booking_id,
            "user_id": test_user.id,
            "user_email": test_user.email,
        }
    ]


def test_cancel_booking_route_uses_cancel_use_case(client, test_user, auth_header):
    use_case = StubCancelBookingUseCase()
    booking_id = uuid.uuid4()
    client.app.dependency_overrides[get_cancel_booking_use_case] = lambda: use_case

    try:
        response = client.delete(f"{API_V1_PREFIX}/booking/flight-orders/{booking_id}")
    finally:
        client.app.dependency_overrides.pop(get_cancel_booking_use_case, None)

    assert response.status_code == 200
    assert response.json() == {
        "id": str(booking_id),
        "status": "cancelled",
        "message": "Booking has been successfully cancelled",
    }
    assert len(use_case.calls) == 1
    command = use_case.calls[0]
    assert command.booking_id == booking_id
    assert command.user_id == test_user.id
    assert command.user_email == test_user.email


def test_get_user_bookings_route_uses_bookings_use_case(client, test_user, auth_header):
    use_case = StubUserBookingsUseCase()
    client.app.dependency_overrides[get_user_bookings_use_case] = lambda: use_case

    try:
        response = client.get(
            f"{API_V1_PREFIX}/bookings",
            params={"cursor": "cursor_1", "limit": 20, "include_count": True},
        )
    finally:
        client.app.dependency_overrides.pop(get_user_bookings_use_case, None)

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": str(use_case.booking_id),
                "pnr": "PNR123",
                "status": "confirmed",
                "created_at": "2026-01-01T12:00:00Z",
                "ticket_url": "https://tickets.example.com/ticket.pdf",
            }
        ],
        "next_cursor": "cursor_2",
        "has_more": False,
        "has_previous": False,
        "total_count": 1,
        "limit": 20,
    }
    assert use_case.calls == [
        {
            "user_id": test_user.id,
            "cursor": "cursor_1",
            "limit": 20,
            "include_count": True,
        }
    ]
