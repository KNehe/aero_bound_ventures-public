"""Payment endpoints for Pesapal integration"""

import os
from fastapi import APIRouter, HTTPException, Depends, status

from sqlmodel import Session

from backend.application.payments.initiate_pesapal_payment import (
    InitiatePesapalPayment,
    InitiatePesapalPaymentCommand,
    PaymentBillingAddress,
    PaymentBookingAccessDenied,
    PaymentBookingAlreadyPaid,
    PaymentBookingNotFound,
    PaymentProviderValidationError,
    PaymentSystemNotConfigured,
)
from backend.application.payments.get_payment_status import (
    GetPaymentStatus,
    InvalidPaymentStatusRequest,
    PaymentStatusProviderError,
)
from backend.application.payments.process_pesapal_callback import (
    ProcessPesapalCallbackCommand,
    ProcessPesapalPaymentCallback,
)
from backend.application.payments.process_pesapal_ipn import (
    ProcessPesapalIpn,
    ProcessPesapalIpnCommand,
)
from backend.crud.database import get_session
from backend.external_services.pesapal import pesapal_client
from backend.infrastructure.bookings.sqlmodel_booking_repository import (
    SqlModelBookingRepository,
)
from backend.infrastructure.payments.kafka_payment_event_publisher import (
    KafkaPaymentEventPublisher,
)
from backend.infrastructure.payments.pesapal_payment_gateway import (
    PesapalPaymentGateway,
)
from backend.schemas.payments import (
    PesapalPaymentRequest,
    PesapalPaymentResponse,
    PesapalTransactionStatus,
    RefundRequest,
    RefundResponse,
)
from backend.utils.security import get_current_user
from backend.models.users import UserInDB

from backend.utils.log_manager import get_app_logger
from backend.utils.kafka import kafka_producer

from backend.utils.constants import KafkaTopics, KafkaEventTypes


logger = get_app_logger(__name__)


router = APIRouter(prefix="/payments", tags=["payments"])


def get_initiate_pesapal_payment_use_case(
    session: Session = Depends(get_session),
) -> InitiatePesapalPayment:
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return InitiatePesapalPayment(
        booking_repository=SqlModelBookingRepository(session),
        payment_provider=PesapalPaymentGateway(pesapal_client),
        default_callback_url=f"{frontend_url}/booking/payment/callback",
    )


def get_process_pesapal_callback_use_case(
    session: Session = Depends(get_session),
) -> ProcessPesapalPaymentCallback:
    return ProcessPesapalPaymentCallback(
        booking_repository=SqlModelBookingRepository(session),
        transaction_provider=PesapalPaymentGateway(pesapal_client),
        event_publisher=KafkaPaymentEventPublisher(kafka_producer),
    )


def get_process_pesapal_ipn_use_case(
    session: Session = Depends(get_session),
) -> ProcessPesapalIpn:
    return ProcessPesapalIpn(
        booking_repository=SqlModelBookingRepository(session),
        transaction_provider=PesapalPaymentGateway(pesapal_client),
        event_publisher=KafkaPaymentEventPublisher(kafka_producer),
    )


def get_payment_status_use_case() -> GetPaymentStatus:
    return GetPaymentStatus(
        payment_status_provider=PesapalPaymentGateway(pesapal_client),
    )


@router.post("/pesapal/initiate", response_model=PesapalPaymentResponse)
async def initiate_pesapal_payment(
    payment_request: PesapalPaymentRequest,
    current_user: UserInDB = Depends(get_current_user),
    initiate_payment_use_case: InitiatePesapalPayment = Depends(
        get_initiate_pesapal_payment_use_case
    ),
):
    """
    Initiate a Pesapal payment for a booking (USD only)

    This endpoint:
    1. Validates the booking exists and belongs to the user
    2. Creates a payment order with Pesapal (USD currency only)
    3. Returns the redirect URL for customer to complete payment

    Note: Only USD payments are accepted
    """
    try:
        billing_address = payment_request.billing_address
        result = await initiate_payment_use_case.execute(
            user_id=current_user.id,
            command=InitiatePesapalPaymentCommand(
                booking_id=payment_request.booking_id,
                amount=payment_request.amount,
                currency=payment_request.currency,
                description=payment_request.description,
                callback_url=payment_request.callback_url,
                billing_address=PaymentBillingAddress(
                    email_address=str(billing_address.email_address),
                    phone_number=billing_address.phone_number,
                    country_code=billing_address.country_code,
                    first_name=billing_address.first_name,
                    last_name=billing_address.last_name,
                    middle_name=billing_address.middle_name,
                    line_1=billing_address.line_1,
                    line_2=billing_address.line_2,
                    city=billing_address.city,
                    state=billing_address.state,
                    postal_code=billing_address.postal_code,
                    zip_code=billing_address.zip_code,
                ),
            ),
        )

        return PesapalPaymentResponse(
            order_tracking_id=result.order_tracking_id,
            merchant_reference=result.merchant_reference,
            redirect_url=result.redirect_url,
        )
    except PaymentBookingNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    except PaymentBookingAccessDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to pay for this booking",
        )
    except PaymentBookingAlreadyPaid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This booking has already been paid",
        )
    except PaymentSystemNotConfigured:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment system not configured. Please contact support.",
        )
    except PaymentProviderValidationError as e:
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
    process_callback_use_case: ProcessPesapalPaymentCallback = Depends(
        get_process_pesapal_callback_use_case
    ),
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
    result = await process_callback_use_case.execute(
        ProcessPesapalCallbackCommand(
            order_tracking_id=OrderTrackingId,
            order_merchant_reference=OrderMerchantReference,
        )
    )
    return result.as_response()


@router.get("/pesapal/ipn")
async def pesapal_ipn_notification(
    OrderTrackingId: str | None = None,
    OrderMerchantReference: str | None = None,
    OrderNotificationType: str | None = None,
    process_ipn_use_case: ProcessPesapalIpn = Depends(get_process_pesapal_ipn_use_case),
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
    result = await process_ipn_use_case.execute(
        ProcessPesapalIpnCommand(
            order_tracking_id=OrderTrackingId,
            order_merchant_reference=OrderMerchantReference,
            order_notification_type=OrderNotificationType,
        )
    )
    return result.as_response()


@router.get(
    "/pesapal/status/{order_tracking_id}", response_model=PesapalTransactionStatus
)
async def get_payment_status(
    order_tracking_id: str,
    current_user: UserInDB = Depends(get_current_user),
    payment_status_use_case: GetPaymentStatus = Depends(get_payment_status_use_case),
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
        result = await payment_status_use_case.execute(order_tracking_id)
        return PesapalTransactionStatus(**result.as_response())
    except InvalidPaymentStatusRequest as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PaymentStatusProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch payment status: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch payment status: {str(e)}",
        )


@router.post("/pesapal/refund", response_model=RefundResponse)
async def request_pesapal_refund(
    refund_request: RefundRequest,
    session: Session = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
):
    logger.info(
        f"Refund request initiated by user {current_user.email}"
        f"for confirmation_code: {refund_request.confirmation_code}"
    )
    try:
        result = await pesapal_client.request_refund(
            confirmation_code=refund_request.confirmation_code,
            amount=refund_request.amount,
            username=current_user.email,
            remarks=refund_request.remarks,
        )

        kafka_producer.send(
            KafkaTopics.PAYMENT_EVENTS,
            {
                "event_type": KafkaEventTypes.REFUND_REQUESTED,
                "confirmation_code": refund_request.confirmation_code,
                "amount": refund_request.amount,
                "remarks": refund_request.remarks,
                "initiated_by": current_user.email,
                "user_id": str(current_user.id),
                "pesapal_status": result.get("status"),
                "pesapal_message": result.get("message"),
            },
        )

        return RefundResponse(
            status=result.get("status"),
            message=result.get("message", "Unknown response from Pesapal"),
            confirmation_code=refund_request.confirmation_code,
        )

    except ValueError as e:
        logger.error(f"Refund request validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Refund request failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process refund request: {str(e)}",
        )
