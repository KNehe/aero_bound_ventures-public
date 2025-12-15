"""Ticket upload endpoints"""

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
    status,
    BackgroundTasks,
)
from sqlmodel import Session
from backend.crud.database import get_session
from backend.external_services.email import send_email
from backend.models.constants import ADMIN_GROUP_NAME
from backend.external_services.cloudinary_service import (
    configure_cloudinary,
    upload_file,
)
from backend.crud.bookings import get_booking_by_id, update_booking_ticket_url
from backend.utils.dependencies import GroupDependency
import uuid

router = APIRouter(prefix="/tickets", tags=["tickets"])

configure_cloudinary()


@router.post(
    "/upload/{booking_id}", dependencies=[Depends(GroupDependency(ADMIN_GROUP_NAME))]
)
async def upload_ticket(
    background_tasks: BackgroundTasks,
    booking_id: uuid.UUID,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
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
    booking = get_booking_by_id(session, str(booking_id))

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    try:
        upload_result = upload_file(file.file, resource_type="auto")

        secure_url = upload_result["secure_url"]
        updated_booking = update_booking_ticket_url(
            session, str(booking_id), secure_url
        )

        if not updated_booking:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update booking with ticket URL",
            )

        background_tasks.add_task(
            send_email,
            recipients=[booking.user.email],
            subject="Ticket Uploaded Successfully : Aero Bound Ventures",
            template_name="ticket_upload_success.html",
            extra={
                "pnr": booking.amadeus_order_response.get("associatedRecords", [{}])[
                    0
                ].get("reference", "N/A")
            },
        )

        return {
            "message": "Ticket uploaded successfully",
            "ticket_url": secure_url,
            "booking_id": str(booking.id),
            "public_id": upload_result["public_id"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload ticket: {str(e)}",
        )
