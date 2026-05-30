"""Ticket upload endpoints"""

import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    status,
    UploadFile,
)
from sqlmodel import Session

from backend.application.tickets.upload_ticket import (
    TicketBookingNotFound,
    TicketBookingUpdateFailed,
    UploadTicket,
    UploadTicketCommand,
)
from backend.crud.database import get_session
from backend.infrastructure.tickets.cloudinary_ticket_file_storage import (
    CloudinaryTicketFileStorage,
)
from backend.infrastructure.tickets.kafka_ticket_event_publisher import (
    KafkaTicketEventPublisher,
)
from backend.infrastructure.tickets.sqlmodel_ticket_booking_repository import (
    SqlModelTicketBookingRepository,
)
from backend.models.constants import ADMIN_GROUP_NAME
from backend.schemas.tickets import TicketUploadResponse
from backend.utils.dependencies import GroupDependency
from backend.utils.kafka import kafka_producer


router = APIRouter(prefix="/tickets", tags=["tickets"])


def get_upload_ticket_use_case(
    session: Session = Depends(get_session),
) -> UploadTicket:
    return UploadTicket(
        ticket_booking_repository=SqlModelTicketBookingRepository(session),
        ticket_file_storage=CloudinaryTicketFileStorage(),
        ticket_event_publisher=KafkaTicketEventPublisher(kafka_producer),
    )


@router.post(
    "/upload/{booking_id}",
    response_model=TicketUploadResponse,
    dependencies=[Depends(GroupDependency(ADMIN_GROUP_NAME))],
)
async def upload_ticket(
    booking_id: uuid.UUID,
    file: UploadFile = File(...),
    upload_ticket_use_case: UploadTicket = Depends(get_upload_ticket_use_case),
):
    """
    Upload a ticket file for a specific booking (Admin only)

    Args:
        booking_id: UUID of the booking to attach the ticket to
        file: The ticket file to upload
        current_user: Authenticated admin user from JWT token
        session: Database session

    Returns:
        Dictionary containing the secure URL of the uploaded ticket

    Raises:
        HTTPException 404: If booking not found
        HTTPException 400: If file upload fails
        HTTPException 403: If user is not an admin
    """
    try:
        return upload_ticket_use_case.execute(
            command=UploadTicketCommand(
                booking_id=booking_id,
                file=file.file,
            )
        )
    except TicketBookingNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    except TicketBookingUpdateFailed:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update booking with ticket URL",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload ticket: {str(exc)}",
        )
