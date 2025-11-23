"""Payment schemas for Pesapal integration"""

from pydantic import BaseModel, EmailStr, Field, field_validator


class BillingAddress(BaseModel):
    """Customer billing address"""

    email_address: EmailStr
    phone_number: str | None = None
    country_code: str | None = None  # e.g., "UG" for Uganda
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    line_1: str | None = None
    line_2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    zip_code: str | None = None


class PesapalPaymentRequest(BaseModel):
    """Request to initiate Pesapal payment (USD only)"""

    booking_id: str
    amount: float
    currency: str = Field(default="USD", description="Currency code (USD only)")
    description: str
    callback_url: str
    billing_address: BillingAddress

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Ensure only USD is accepted"""
        if v != "USD":
            raise ValueError("Only USD currency is supported")
        return v


class PesapalPaymentResponse(BaseModel):
    """Response from Pesapal payment initiation"""

    order_tracking_id: str
    merchant_reference: str
    redirect_url: str


class PesapalCallbackRequest(BaseModel):
    """Pesapal payment callback parameters"""

    OrderTrackingId: str
    OrderMerchantReference: str


class PesapalTransactionStatus(BaseModel):
    """Transaction status from Pesapal"""

    payment_method: str
    amount: float
    created_date: str
    confirmation_code: str
    payment_status_description: str
    description: str
    message: str
    payment_account: str
    call_back_url: str
    status_code: int
    merchant_reference: str
    payment_status_code: str
    currency: str
    error: dict | None = None
