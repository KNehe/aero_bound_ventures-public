import re
from typing import Any

from backend.application.tickets.upload_ticket import StoredTicketFile
from backend.external_services.cloudinary_service import (
    configure_cloudinary,
    upload_file,
)


class CloudinaryTicketFileStorage:
    def __init__(self):
        configure_cloudinary()

    def store_ticket_file(
        self,
        file: Any,
        *,
        user_email: str,
    ) -> StoredTicketFile:
        email_folder = re.sub(
            r"[^a-z0-9@._-]+",
            "_",
            user_email.strip().lower(),
        )
        upload_result = upload_file(
            file,
            resource_type="auto",
            asset_folder=f"tickets/{email_folder}",
        )
        return StoredTicketFile(
            ticket_url=upload_result["secure_url"],
            public_id=upload_result["public_id"],
        )
