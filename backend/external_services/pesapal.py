"""
Pesapal Payment Gateway Integration
Docs: https://developer.pesapal.com/
"""

import os
import httpx
from datetime import datetime, timedelta, timezone
from typing import Any
from dotenv import load_dotenv
from backend.utils.log_manager import get_app_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_app_logger(__name__)


class PesapalClient:
    def __init__(self):
        self.consumer_key = os.getenv("PESAPAL_CONSUMER_KEY")
        self.consumer_secret = os.getenv("PESAPAL_CONSUMER_SECRET")
        self.base_url = os.getenv(
            "PESAPAL_BASE_URL", "https://cybqa.pesapal.com/pesapalv3"
        )
        self.ipn_id = os.getenv("PESAPAL_IPN_ID")  # IPN Notification ID
        self._access_token: str | None = None
        self._token_expiry: datetime | None = None

    async def _get_access_token(self) -> str:
        """
        Get OAuth2 access token from Pesapal

        POST /api/Auth/RequestToken

        Returns:
            Access token string valid for 5 minutes
        """
        if (
            self._access_token
            and self._token_expiry
            and datetime.now(timezone.utc) < self._token_expiry
        ):
            return self._access_token

        payload = {
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret,
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/Auth/RequestToken",
                json=payload,
                headers=headers,
            )

            # Log response for debugging
            logger.info(f"Pesapal Auth Response Status: {response.status_code}")
            logger.debug(f"Pesapal Auth Response Body: {response.text}")

            response.raise_for_status()
            data = response.json()

            if data.get("error"):
                error = data["error"]
                error_msg = (
                    error.get("message", "") if isinstance(error, dict) else str(error)
                )
                logger.error(
                    f"Pesapal authentication error: {error_msg or 'Unknown error from Pesapal'}"
                )
                raise ValueError(
                    f"Authentication failed: {error_msg or 'Unknown error from Pesapal'}"
                )

            if "token" not in data:
                logger.error(f"No token in Pesapal response: {data}")
                raise ValueError(
                    f"Authentication failed: No token in response. Response: {data}"
                )

            self._access_token = data["token"]
            logger.info("Pesapal authentication successful")

            self._token_expiry = datetime.now(timezone.utc) + timedelta(minutes=4)

            return self._access_token

    async def submit_order_request(
        self,
        merchant_reference: str,
        amount: float,
        currency: str,
        description: str,
        callback_url: str,
        notification_id: str,
        billing_address: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Submit a payment order request to Pesapal

        POST /api/Transactions/SubmitOrderRequest

        Args:
            merchant_reference: Unique order reference (booking_id) - max 50 chars
            amount: Payment amount
            currency: Currency code (must be USD)
            description: Payment description - max 100 chars
            callback_url: URL to redirect after payment
            notification_id: IPN notification ID (from PESAPAL_IPN_ID)
            billing_address: Customer billing information

        Returns:
            Dictionary containing:
            - order_tracking_id: Pesapal's unique order ID
            - merchant_reference: Your booking ID
            - redirect_url: URL to redirect customer for payment
            - status: Response status code

        Example Response:
            {
                "order_tracking_id": "b945e4af-80a5-4ec1-8706-e03f8332fb04",
                "merchant_reference": "BOOKING123",
                "redirect_url": "https://cybqa.pesapal.com/pesapaliframe/...",
                "error": null,
                "status": "200"
            }
        """
        # Validate currency is USD
        if currency != "USD":
            logger.error(f"Invalid currency: {currency}. Only USD is supported")
            raise ValueError("Only USD currency is supported")

        token = await self._get_access_token()

        # Create unique request ID using merchant_reference and timestamp
        unique_id = (
            f"{merchant_reference}-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        )

        # Prepare request payload
        payload = {
            "id": unique_id,  # Unique request ID with timestamp
            "currency": currency,
            "amount": float(amount),
            "description": description[:100],
            "callback_url": callback_url,
            "notification_id": notification_id,
            "billing_address": billing_address,
        }

        logger.info(
            f"Submitting order request for merchant_reference: {merchant_reference}, amount: {amount} {currency}"
        )
        logger.debug(f"Order payload: {payload}")
        logger.info(f"Using unique request ID: {unique_id}")

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/Transactions/SubmitOrderRequest",
                json=payload,
                headers=headers,
            )

            logger.info(f"Pesapal Submit Order Response Status: {response.status_code}")
            logger.debug(f"Pesapal Submit Order Response Body: {response.text}")

            response.raise_for_status()
            data = response.json()

            if data.get("error"):
                error = data["error"]
                error_msg = (
                    error.get("message", "Unknown error")
                    if isinstance(error, dict)
                    else str(error)
                )
                logger.error(f"Payment order failed: {error_msg}")
                raise ValueError(f"Payment order failed: {error_msg}")

            logger.info(
                f"Order submitted successfully. Order tracking ID: {data.get('order_tracking_id')}"
            )
            return data

    async def get_transaction_status(self, order_tracking_id: str) -> dict[str, Any]:
        """
        Get the status of a transaction

        GET /api/Transactions/GetTransactionStatus?orderTrackingId={id}

        Args:
            order_tracking_id: Pesapal order tracking ID (from callback or IPN)

        Returns:
            Dictionary containing payment status and details:
            - payment_status_description: COMPLETED, FAILED, REVERSED, INVALID
            - status_code: 1=COMPLETED, 2=FAILED, 3=REVERSED, 0=INVALID
            - payment_method: Visa, M-Pesa, etc.
            - amount: Amount paid
            - confirmation_code: Payment provider confirmation
            - merchant_reference: Your booking ID
            - created_date: Payment timestamp
            - payment_account: Masked card/phone
            - currency: Payment currency

        Example Response:
            {
                "payment_method": "Visa",
                "amount": 100,
                "created_date": "2022-04-30T07:41:09.763",
                "confirmation_code": "6513008693186320103009",
                "payment_status_description": "Completed",
                "message": "Request processed successfully",
                "payment_account": "476173**0010",
                "status_code": 1,
                "merchant_reference": "BOOKING123",
                "currency": "USD",
                "status": "200"
            }
        """
        token = await self._get_access_token()

        logger.info(
            f"Fetching transaction status for order_tracking_id: {order_tracking_id}"
        )

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/Transactions/GetTransactionStatus",
                params={"orderTrackingId": order_tracking_id},
                headers=headers,
            )

            logger.info(f"Transaction Status Response Status: {response.status_code}")
            logger.debug(f"Transaction Status Response Body: {response.text}")

            response.raise_for_status()
            data = response.json()

            # Check for errors, but allow "pending payment" status to pass through
            error = data.get("error")
            if error and error.get("message"):
                error_code = error.get("code", "")
                error_msg = error.get("message", "Unknown error")

                # "payment_details_not_found" means payment is pending - this is normal, not an error
                if error_code == "payment_details_not_found":
                    logger.info(f"Payment is pending (not yet completed): {error_msg}")
                    # Return the data as-is, caller will handle pending status
                    return data

                # For other errors, log and raise
                logger.error(f"Failed to fetch transaction status: {error_msg}")
                raise ValueError(f"Failed to fetch transaction status: {error_msg}")

            logger.info(
                f"Transaction status: {data.get('payment_status_description')} (code: {data.get('status_code')})"
            )
            return data

    async def request_refund(
        self,
        confirmation_code: str,
        amount: float,
        username: str,
        remarks: str,
    ) -> dict[str, Any]:
        token = await self._get_access_token()

        payload = {
            "confirmation_code": confirmation_code,
            "amount": str(amount),
            "username": username,
            "remarks": remarks,
        }

        logger.info(
            f"Submittting refund request for confirmation code: {confirmation_code}",
            f"amount: {amount} initiated by {username} with remarks: {remarks}",
        )

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/Transactions/RefundRequest",
                json=payload,
                headers=headers,
            )
            logger.info(
                f"Pesapal Request Refund Response Status: {response.status_code}"
            )
            logger.debug(f"Pesapal Request Refund Response Body: {response.text}")

            data = response.json()

            if data.get("status") == "500":
                error_message = data.get("message", "Refund  rejected by Pesapal")
                logger.warning(f"Refund request rejected by Pesapal: {error_message}")
                return data
            logger.info(f"Refund request submitted successfully: {data.get('message')}")
            return data


pesapal_client = PesapalClient()
