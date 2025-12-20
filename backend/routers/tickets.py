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
from backend.models.notifications import NotificationType
from backend.external_services.cloudinary_service import (
    configure_cloudinary,
    upload_file,
)
from backend.crud.bookings import get_booking_by_id, update_booking_ticket_url
from backend.utils.dependencies import GroupDependency
from backend.utils.notification_service import create_and_publish_notification
import uuid
from backend.crud.users import get_admin_users

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
   
    pnr = booking.amadeus_order_response.get("associatedRecords", [{}])[0].get("reference", "N/A")

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

        # Send email notification
        background_tasks.add_task(
            send_email,
            recipients=[booking.user.email],
            subject="Ticket Uploaded Successfully : Aero Bound Ventures",
            template_name="ticket_upload_success.html",
            extra={
                "pnr":pnr,
                "booking_id": str(booking.id),
            },
        )

        # Send in-app notification to the user (persisted to DB + real-time via SSE)
        await create_and_publish_notification(
            db=session,
            user_id=booking.user.id,
            message=f"Your ticket for flight with PNR: {pnr} has been uploaded successfully.",
            notification_type=NotificationType.TICKET_UPLOADED,
        )

        # Send in-app notifications to all admins
        admin_users = get_admin_users(session)
        for admin in admin_users:
            await create_and_publish_notification(
                db=session,
                user_id=admin.id,
                message=f"Ticket uploaded for flight with PNR: {pnr}.",
                notification_type=NotificationType.TICKET_UPLOADED,
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

