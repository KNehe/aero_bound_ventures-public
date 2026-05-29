import json
from typing import Any


ERROR_MESSAGES = {
    477: (
        "Invalid data format. Please check that all fields are correctly formatted "
        "(dates: YYYY-MM-DD, airport codes: 3-letter IATA codes)."
    ),
    1304: "The provided credit card is not accepted. Please try a different payment method.",
    2781: "Invalid data length. One or more fields exceed the maximum allowed length.",
    4926: "Invalid data received. Please verify all required fields are filled correctly.",
    9112: "Ticketing error occurred. Please contact support for assistance.",
    2668: "Invalid parameter combination. Please adjust your search criteria.",
    32171: "Missing required information. Please ensure all mandatory fields are provided.",
    34107: "The selected fare is not applicable. Please search for new flights.",
    34651: (
        "Flight is no longer available for booking. Flight offers expire within minutes. "
        "Please search for flights again and complete the entire booking process quickly."
    ),
    34733: "Payment processing failed. Please try again or use a different payment method.",
    36870: "Booking failed. The reservation could not be completed. Please search for flights again.",
    37200: "Price discrepancy detected. The flight price has changed. Please review the updated pricing.",
    38034: "One or more requested services are not available. Please review your selections.",
    141: "A system error occurred. Please try again in a few moments.",
}

DEFAULT_MESSAGE = (
    "Unable to process your booking request. Please verify your information and try again."
)


def parse_amadeus_client_error(error: Any) -> str:
    if not hasattr(error, "response") or not hasattr(error.response, "body"):
        return DEFAULT_MESSAGE

    try:
        body = error.response.body
        error_body = json.loads(body) if isinstance(body, str) else body

        errors = error_body.get("errors", [])
        if not errors:
            return f"Booking service error: {body}"

        first_error = errors[0]
        error_code = _normalize_error_code(first_error.get("code"))
        error_title = first_error.get("title", "Unknown error")
        error_detail = first_error.get("detail", "")
        error_source = first_error.get("source", {})

        if error_code in ERROR_MESSAGES:
            return ERROR_MESSAGES[error_code]

        message = error_title
        if error_detail:
            message = f"{error_title}: {error_detail}"

        if error_source and "parameter" in error_source:
            param = error_source.get("parameter")
            example = error_source.get("example", "")
            if example:
                message += f" (Parameter: {param}, Example: {example})"
            else:
                message += f" (Parameter: {param})"

        return message if message != "Unknown error" else DEFAULT_MESSAGE

    except Exception:
        return DEFAULT_MESSAGE


def _normalize_error_code(error_code: Any) -> int | None:
    if isinstance(error_code, int):
        return error_code
    if isinstance(error_code, str) and error_code.isdigit():
        return int(error_code)
    return None
