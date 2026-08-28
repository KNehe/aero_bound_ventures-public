from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True)
class TicketBookingRecord:
    id: UUID
    pnr: str
    user_id: UUID
    user_email: str


@dataclass(frozen=True)
class StoredTicketFile:
    ticket_url: str
    public_id: str


@dataclass(frozen=True)
class UploadTicketCommand:
    booking_id: UUID
    file: Any


@dataclass(frozen=True)
class UploadedTicket:
    message: str
    ticket_url: str
    booking_id: str
    public_id: str


class UploadTicketError(Exception):
    pass


class TicketBookingNotFound(UploadTicketError):
    pass


class TicketBookingUpdateFailed(UploadTicketError):
    pass


class TicketBookingRepository(Protocol):
    def get_ticket_booking(self, booking_id: UUID) -> TicketBookingRecord | None: ...

    def update_ticket_url(self, *, booking_id: UUID, ticket_url: str) -> bool: ...


class TicketFileStorage(Protocol):
    def store_ticket_file(
        self,
        file: Any,
        *,
        user_email: str,
    ) -> StoredTicketFile: ...


class TicketEventPublisher(Protocol):
    def publish_ticket_uploaded(
        self,
        *,
        pnr: str,
        booking_id: UUID,
        user_id: UUID,
        user_email: str,
    ) -> None: ...


class UploadTicket:
    def __init__(
        self,
        *,
        ticket_booking_repository: TicketBookingRepository,
        ticket_file_storage: TicketFileStorage,
        ticket_event_publisher: TicketEventPublisher,
    ):
        self.ticket_booking_repository = ticket_booking_repository
        self.ticket_file_storage = ticket_file_storage
        self.ticket_event_publisher = ticket_event_publisher

    def execute(self, *, command: UploadTicketCommand) -> UploadedTicket:
        booking = self.ticket_booking_repository.get_ticket_booking(command.booking_id)
        if not booking:
            raise TicketBookingNotFound

        stored_ticket = self.ticket_file_storage.store_ticket_file(
            command.file,
            user_email=booking.user_email,
        )
        updated = self.ticket_booking_repository.update_ticket_url(
            booking_id=booking.id,
            ticket_url=stored_ticket.ticket_url,
        )
        if not updated:
            raise TicketBookingUpdateFailed

        self.ticket_event_publisher.publish_ticket_uploaded(
            pnr=booking.pnr,
            booking_id=booking.id,
            user_id=booking.user_id,
            user_email=booking.user_email,
        )

        return UploadedTicket(
            message="Ticket uploaded successfully",
            ticket_url=stored_ticket.ticket_url,
            booking_id=str(booking.id),
            public_id=stored_ticket.public_id,
        )
