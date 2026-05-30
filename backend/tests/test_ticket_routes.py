from uuid import uuid4

from sqlmodel import Session

from backend.application.tickets.upload_ticket import UploadedTicket
from backend.crud.users import create_user
from backend.routers.tickets import get_upload_ticket_use_case
from backend.utils.security import get_current_user
from tests.conftest import API_V1_PREFIX


class StubUploadTicketUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, *, command):
        self.calls.append(command)
        return UploadedTicket(
            message="Ticket uploaded successfully",
            ticket_url="https://tickets.example.com/ticket.pdf",
            booking_id=str(command.booking_id),
            public_id="ticket-public-id",
        )


def test_upload_ticket_route_uses_upload_ticket_use_case(client, session: Session):
    admin_user = create_user(session, "ticket-admin@example.com", "password")
    admin_user.is_superuser = True
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)

    use_case = StubUploadTicketUseCase()
    booking_id = uuid4()
    client.app.dependency_overrides[get_current_user] = lambda: admin_user
    client.app.dependency_overrides[get_upload_ticket_use_case] = lambda: use_case

    try:
        response = client.post(
            f"{API_V1_PREFIX}/tickets/upload/{booking_id}",
            files={"file": ("ticket.pdf", b"ticket-data", "application/pdf")},
        )
    finally:
        client.app.dependency_overrides.pop(get_current_user, None)
        client.app.dependency_overrides.pop(get_upload_ticket_use_case, None)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Ticket uploaded successfully",
        "ticket_url": "https://tickets.example.com/ticket.pdf",
        "booking_id": str(booking_id),
        "public_id": "ticket-public-id",
    }
    assert len(use_case.calls) == 1
    assert use_case.calls[0].booking_id == booking_id
    assert use_case.calls[0].file is not None
