import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.consumers.booking_notifications import process_booking_notifications
from backend.consumers.payment_notifications import process_payment_notifications
from backend.utils.constants import KafkaEventTypes
import uuid


@pytest.fixture
def mock_email(mocker):
    return mocker.patch(
        "backend.consumers.booking_notifications.send_email", new_callable=AsyncMock
    )


@pytest.fixture
def mock_notif_service(mocker):
    return mocker.patch(
        "backend.consumers.booking_notifications.create_and_publish_notification",
        new_callable=AsyncMock,
    )


@pytest.mark.asyncio
async def test_process_booking_created_event(
    session, mocker, mock_email, mock_notif_service
):
    mock_session_ctx = MagicMock()
    mock_session_ctx.__enter__.return_value = session
    mocker.patch(
        "backend.consumers.booking_notifications.Session", return_value=mock_session_ctx
    )
    mocker.patch(
        "backend.consumers.booking_notifications.get_admin_emails",
        return_value=["admin@example.com"],
    )

    user_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    event_payload = {
        "event_type": KafkaEventTypes.BOOKING_CREATED,
        "booking_id": booking_id,
        "user_id": str(user_id),
        "user_email": "user@example.com",
        "pnr": "PNR123",
    }
    await process_booking_notifications(event_payload)

    assert mock_email.call_count == 2
    mock_notif_service.assert_called_once()

    args, kwargs = mock_notif_service.call_args
    assert kwargs["user_id"] == user_id
    assert "PNR123" in kwargs["message"]


@pytest.mark.asyncio
async def test_process_paymeny_sucess_event(session, mocker):
    mock_email = mocker.patch(
        "backend.consumers.payment_notifications.send_email", new_callable=AsyncMock
    )
    mock_notif = mocker.patch(
        "backend.consumers.payment_notifications.create_and_publish_notification",
        new_callable=AsyncMock,
    )

    mock_session_ctx = MagicMock()
    mock_session_ctx.__enter__.return_value = session
    mocker.patch(
        "backend.consumers.payment_notifications.Session", return_value=mock_session_ctx
    )

    user_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    event_payload = {
        "event_type": KafkaEventTypes.PAYMENT_SUCCESSFUL,
        "booking_id": booking_id,
        "user_id": str(user_id),
        "user_email": "user@example.com",
        "pnr": "PNR123",
    }
    await process_payment_notifications(event_payload)

    mock_email.assert_any_call(
        recipients=["user@example.com"],
        subject="Payment Successful : Aero Bound Ventures",
        template_name="payment_success.html",
        extra={
            "pnr": "PNR123",
            "booking_id": str(booking_id),
        },
    )
    mock_notif.assert_called_once()
