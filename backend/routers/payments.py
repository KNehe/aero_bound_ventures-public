"""Payment endpoints for Pesapal integration"""

import os
from fastapi import APIRouter, HTTPException, Depends, status

from sqlmodel import Session

from backend.crud.database import get_session
from backend.external_services.pesapal import pesapal_client
from backend.models.bookings import BookingStatus
from backend.schemas.payments import (
    PesapalPaymentRequest,
    PesapalPaymentResponse,
    PesapalTransactionStatus,
)
from backend.crud.bookings import get_booking_by_id, update_booking_status
from backend.utils.security import get_current_user
from backend.models.users import UserInDB

from backend.utils.log_manager import get_app_logger
from backend.utils.kafka import kafka_producer

from backend.utils.constants import KafkaTopics, KafkaEventTypes


logger = get_app_logger(__name__)


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/pesapal/initiate", response_model=PesapalPaymentResponse)
async def initiate_pesapal_payment(
    payment_request: PesapalPaymentRequest,
    session: Session = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Initiate a Pesapal payment for a booking (USD only)

    This endpoint:
    1. Validates the booking exists and belongs to the user
    2. Creates a payment order with Pesapal (USD currency only)
    3. Returns the redirect URL for customer to complete payment

    Note: Only USD payments are accepted
    """
    print("Initiating Pesapal payment for booking:", payment_request.booking_id)
    # 1. Get the booking from database
    booking = get_booking_by_id(session, payment_request.booking_id)

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )

    # 2. Verify booking belongs to current user
    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to pay for this booking",
        )

    # 3. Check if booking is already paid
    if booking.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This booking has already been paid",
        )

    print("Pesapal IPN ID:", pesapal_client.ipn_id)
    # 4. Validate IPN ID is configured
    if not pesapal_client.ipn_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment system not configured. Please contact support.",
        )

    # 5. Use billing address from request (already contains traveler info from frontend)
    # Fill in any missing fields with empty strings for Pesapal

    billing_address = {
        "email_address": payment_request.billing_address.email_address,
        "phone_number": payment_request.billing_address.phone_number or "",
        "country_code": payment_request.billing_address.country_code or "",
        "first_name": payment_request.billing_address.first_name or "",
        "middle_name": getattr(payment_request.billing_address, "middle_name", None)
        or "",
        "last_name": payment_request.billing_address.last_name or "",
        "line_1": payment_request.billing_address.line_1 or "",
        "line_2": payment_request.billing_address.line_2 or "",
        "city": payment_request.billing_address.city or "",
        "state": payment_request.billing_address.state or "",
        "postal_code": payment_request.billing_address.postal_code or "",
        "zip_code": payment_request.billing_address.zip_code or "",
    }

    # 6. Prepare callback URL (frontend will handle this)
    callback_url = (
        payment_request.callback_url
        or f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/booking/payment/callback"
    )

    try:
        # 7. Submit order to Pesapal
        result = await pesapal_client.submit_order_request(
            merchant_reference=str(booking.id),
            amount=payment_request.amount,
            currency=payment_request.currency,
            description=f"Flight booking payment - {booking.id}",
            callback_url=callback_url,
            notification_id=pesapal_client.ipn_id,
            billing_address=billing_address,
        )

        # 8. Return payment response
        return PesapalPaymentResponse(
            order_tracking_id=result["order_tracking_id"],
            merchant_reference=result["merchant_reference"],
            redirect_url=result["redirect_url"],
            status=result.get("status", "200"),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate payment: {str(e)}",
        )


@router.get("/pesapal/callback")
async def pesapal_payment_callback(
    OrderTrackingId: str,
    OrderMerchantReference: str,
    session: Session = Depends(get_session),
):
    """
    Handle Pesapal payment callback (user redirect after payment)

    Pesapal redirects users here after payment completion.

    Query Parameters:
    - OrderTrackingId: Pesapal's unique order ID
    - OrderMerchantReference: Your booking ID
    - OrderNotificationType: Always "CALLBACKURL" for callback

    This endpoint:
    1. Fetches transaction status from Pesapal
    2. Updates booking payment status
    3. Redirects user to appropriate page
    """
    try:
        # Extract original booking ID from merchant reference (format: booking_id-timestamp)
        original_booking_id = (
            OrderMerchantReference.rsplit("-", 1)[0]
            if "-" in OrderMerchantReference
            else OrderMerchantReference
        )

        # 1. Get booking to update
        booking = get_booking_by_id(session, original_booking_id)

        if not booking:
            logger.error(f"Booking not found for ID: {original_booking_id}")
            return {
                "status": "error",
                "message": "Booking not found",
                "order_tracking_id": OrderTrackingId,
            }

        pnr = booking.amadeus_order_response.get("associatedRecords", [{}])[0].get(
            "reference", "N/A"
        )
        # 2. Fetch transaction status from Pesapal
        try:
            transaction_status = await pesapal_client.get_transaction_status(
                OrderTrackingId
            )
        except ValueError as e:
            # If it's a "Pending Payment" error that slipped through, handle it gracefully
            if "Pending Payment" in str(e):
                return {
                    "status": "pending",
                    "message": "Payment is pending. Please complete the payment or try again.",
                    "order_tracking_id": OrderTrackingId,
                }
            # Otherwise, re-raise
            raise

        # 3. Check payment status
        payment_status_code = transaction_status.get("status_code")
        payment_status_description = transaction_status.get(
            "payment_status_description", ""
        )

        if payment_status_code == 1:  # COMPLETED
            update_booking_status(session, str(booking.id), BookingStatus.PAID)

            kafka_producer.send(
                KafkaTopics.PAYMENT_EVENTS,
                {
                    "event_type": KafkaEventTypes.PAYMENT_SUCCESSFUL,
                    "booking_id": str(booking.id),
                    "pnr": pnr,
                    "user_email": booking.user.email,
                    "user_id": str(booking.user_id),
                },
            )

            return {
                "status": "success",
                "message": "Payment completed successfully",
                "order_tracking_id": OrderTrackingId,
                "payment_method": transaction_status.get("payment_method"),
                "amount": transaction_status.get("amount"),
                "confirmation_code": transaction_status.get("confirmation_code"),
            }

        elif payment_status_code == 2:  # FAILED
            update_booking_status(session, str(booking.id), BookingStatus.FAILED)

            kafka_producer.send(
                KafkaTopics.PAYMENT_EVENTS,
                {
                    "event_type": KafkaEventTypes.PAYMENT_FAILED,
                    "booking_id": str(booking.id),
                    "pnr": pnr,
                    "user_id": str(booking.user_id),
                    "reason": transaction_status.get("description", "Unknown error"),
                },
            )

            return {
                "status": "failed",
                "message": f"Payment failed: {transaction_status.get('description', 'Unknown error')}",
                "order_tracking_id": OrderTrackingId,
            }

        elif payment_status_code == 3:  # REVERSED
            update_booking_status(session, str(booking.id), BookingStatus.REVERSED)
            return {
                "status": "reversed",
                "message": "Payment was reversed",
                "order_tracking_id": OrderTrackingId,
            }

        else:  # INVALID, PENDING, or unknown (status_code = 0)
            update_booking_status(session, str(booking.id), BookingStatus.PENDING)
            error = transaction_status.get("error", {})
            if error and error.get("code") == "payment_details_not_found":
                return {
                    "status": "pending",
                    "message": "Payment is pending. Please complete the payment or try again.",
                    "order_tracking_id": OrderTrackingId,
                }

            # Otherwise it's invalid
            return {
                "status": "invalid",
                "message": f"Invalid payment status: {payment_status_description}",
                "order_tracking_id": OrderTrackingId,
            }

    except Exception as e:
        update_booking_status(session, str(booking.id), BookingStatus.CANCELLED)
        print("Error processing Pesapal callback:", str(e))
        logger.error(f"Error processing Pesapal callback: {str(e)}")
        return {
            "status": "error",
            "message": f"Error processing callback: {str(e)}",
            "order_tracking_id": OrderTrackingId,
        }


@router.get("/pesapal/ipn")
async def pesapal_ipn_notification(
    OrderTrackingId: str | None = None,
    OrderMerchantReference: str | None = None,
    OrderNotificationType: str | None = None,
    session: Session = Depends(get_session),
):
    """
    Handle Pesapal IPN (Instant Payment Notification)

    Pesapal sends IPN notifications when payment status changes.
    Can be GET or POST (depending on IPN registration).

    Query/Body Parameters:
    - OrderTrackingId: Pesapal's unique order ID
    - OrderMerchantReference: Your booking ID
    - OrderNotificationType: "IPNCHANGE" for IPN calls

    Response Format (Required):
    {"orderNotificationType":"IPNCHANGE","orderTrackingId":"...","orderMerchantReference":"...","status":200}
    """
    try:
        # Validate we have required parameters
        if not all([OrderTrackingId, OrderMerchantReference]):
            return {
                "orderNotificationType": "IPNCHANGE",
                "orderTrackingId": OrderTrackingId or "",
                "orderMerchantReference": OrderMerchantReference or "",
                "status": 500,
            }

        # Extract original booking ID from merchant reference (format: booking_id-timestamp)
        original_booking_id = (
            OrderMerchantReference.rsplit("-", 1)[0]
            if "-" in OrderMerchantReference
            else OrderMerchantReference
        )

        # Fetch transaction status from Pesapal
        transaction_status = await pesapal_client.get_transaction_status(
            OrderTrackingId
        )

        booking = get_booking_by_id(session, original_booking_id)

        if not booking:
            return {
                "orderNotificationType": "IPNCHANGE",
                "orderTrackingId": OrderTrackingId,
                "orderMerchantReference": OrderMerchantReference,
                "status": 500,
            }

        # 3. Update booking based on payment status
        payment_status_code = transaction_status.get("status_code")

        if payment_status_code == 1:  # COMPLETED
            update_booking_status(session, str(booking.id), BookingStatus.PAID)
            kafka_producer.send(
                KafkaTopics.PAYMENT_EVENTS,
                {
                    "event_type": KafkaEventTypes.PAYMENT_SUCCESSFUL,
                    "booking_id": str(booking.id),
                    "pnr": booking.amadeus_order_response.get(
                        "associatedRecords", [{}]
                    )[0].get("reference", "N/A"),
                    "user_email": booking.user.email,
                    "user_id": str(booking.user_id),
                },
            )

        elif payment_status_code == 2:  # FAILED
            update_booking_status(
                session,
                str(booking.id),
                BookingStatus.FAILED,
            )
        elif payment_status_code == 3:  # REVERSED
            update_booking_status(
                session,
                str(booking.id),
                BookingStatus.REVERSED,
            )
        else:
            update_booking_status(
                session,
                str(booking.id),
                BookingStatus.PENDING,
            )

        return {
            "orderNotificationType": "IPNCHANGE",
            "orderTrackingId": OrderTrackingId,
            "orderMerchantReference": OrderMerchantReference,
            "status": 200,
        }

    except Exception:
        update_booking_status(
            session,
            str(booking.id),
            BookingStatus.CANCELLED,
        )
        return {
            "orderNotificationType": "IPNCHANGE",
            "orderTrackingId": OrderTrackingId or "",
            "orderMerchantReference": OrderMerchantReference or "",
            "status": 500,
        }


@router.get(
    "/pesapal/status/{order_tracking_id}", response_model=PesapalTransactionStatus
)
async def get_payment_status(
    order_tracking_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get the current status of a Pesapal transaction

    This endpoint allows frontend to poll payment status.
    Useful for showing real-time status updates.

    Args:
        order_tracking_id: Pesapal's order tracking ID
        current_user: Authenticated user (any authenticated user can check)

    Returns:
        Transaction status details
    """
    try:
        transaction_status = await pesapal_client.get_transaction_status(
            order_tracking_id
        )

        return PesapalTransactionStatus(
            payment_status_description=transaction_status.get(
                "payment_status_description", ""
            ),
            payment_method=transaction_status.get("payment_method", ""),
            amount=transaction_status.get("amount", 0),
            confirmation_code=transaction_status.get("confirmation_code", ""),
            created_date=transaction_status.get("created_date", ""),
            status_code=transaction_status.get("status_code", 0),
            merchant_reference=transaction_status.get("merchant_reference", ""),
            currency=transaction_status.get("currency", "USD"),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch payment status: {str(e)}",
        )
