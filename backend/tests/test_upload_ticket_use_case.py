from uuid import uuid4

import pytest

from backend.application.tickets.upload_ticket import (
    StoredTicketFile,
    TicketBookingNotFound,
    TicketBookingRecord,
    TicketBookingUpdateFailed,
    UploadTicket,
    UploadTicketCommand,
    UploadedTicket,
)


BOOKING_ID = uuid4()
USER_ID = uuid4()


class StubTicketBookingRepository:
    def __init__(self, booking: TicketBookingRecord | None):
        self.booking = booking
        self.lookup_calls = []
        self.update_calls = []
        self.update_succeeds = True

    def get_ticket_booking(self, booking_id):
        self.lookup_calls.append(booking_id)
        return self.booking

    def update_ticket_url(self, *, booking_id, ticket_url: str):
        self.update_calls.append({"booking_id": booking_id, "ticket_url": ticket_url})
        return self.update_succeeds


class StubTicketFileStorage:
    def __init__(self):
        self.calls = []

    def store_ticket_file(self, file):
        self.calls.append(file)
        return StoredTicketFile(
            ticket_url="https://tickets.example.com/ticket.pdf",
            public_id="ticket-public-id",
        )


class StubTicketEventPublisher:
    def __init__(self):
        self.uploaded_events = []

    def publish_ticket_uploaded(self, **kwargs):
        self.uploaded_events.append(kwargs)


def build_booking():
    return TicketBookingRecord(
        id=BOOKING_ID,
        pnr="PNR123",
        user_id=USER_ID,
        user_email="traveler@example.com",
    )


def build_use_case(*, booking: TicketBookingRecord | None):
    repository = StubTicketBookingRepository(booking)
    storage = StubTicketFileStorage()
    publisher = StubTicketEventPublisher()
    use_case = UploadTicket(
        ticket_booking_repository=repository,
        ticket_file_storage=storage,
        ticket_event_publisher=publisher,
    )
    return use_case, repository, storage, publisher


def test_upload_ticket_stores_file_updates_booking_and_publishes_event():
    use_case, repository, storage, publisher = build_use_case(booking=build_booking())
    file = object()

    result = use_case.execute(
        command=UploadTicketCommand(
            booking_id=BOOKING_ID,
            file=file,
        )
    )

    assert result == UploadedTicket(
        message="Ticket uploaded successfully",
        ticket_url="https://tickets.example.com/ticket.pdf",
        booking_id=str(BOOKING_ID),
        public_id="ticket-public-id",
    )
    assert repository.lookup_calls == [BOOKING_ID]
    assert storage.calls == [file]
    assert repository.update_calls == [
        {
            "booking_id": BOOKING_ID,
            "ticket_url": "https://tickets.example.com/ticket.pdf",
        }
    ]
    assert publisher.uploaded_events == [
        {
            "pnr": "PNR123",
            "booking_id": BOOKING_ID,
            "user_id": USER_ID,
            "user_email": "traveler@example.com",
        }
    ]


def test_upload_ticket_rejects_missing_booking():
    use_case, repository, storage, publisher = build_use_case(booking=None)

    with pytest.raises(TicketBookingNotFound):
        use_case.execute(
            command=UploadTicketCommand(
                booking_id=BOOKING_ID,
                file=object(),
            )
        )

    assert repository.lookup_calls == [BOOKING_ID]
    assert storage.calls == []
    assert publisher.uploaded_events == []


def test_upload_ticket_rejects_failed_booking_update():
    use_case, repository, _storage, publisher = build_use_case(booking=build_booking())
    repository.update_succeeds = False

    with pytest.raises(TicketBookingUpdateFailed):
        use_case.execute(
            command=UploadTicketCommand(
                booking_id=BOOKING_ID,
                file=object(),
            )
        )

    assert publisher.uploaded_events == []
