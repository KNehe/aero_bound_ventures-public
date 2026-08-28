from backend.application.tickets.upload_ticket import StoredTicketFile
from backend.external_services import cloudinary_service
from backend.infrastructure.tickets import cloudinary_ticket_file_storage


def test_ticket_storage_uses_nested_folder_for_normalized_user_email(monkeypatch):
    upload_calls = []

    monkeypatch.setattr(
        cloudinary_ticket_file_storage,
        "configure_cloudinary",
        lambda: None,
    )

    def fake_upload_file(file, *, resource_type: str, asset_folder: str):
        upload_calls.append(
            {
                "file": file,
                "resource_type": resource_type,
                "asset_folder": asset_folder,
            }
        )
        return {
            "secure_url": "https://tickets.example.com/ticket.pdf",
            "public_id": "ticket-public-id",
        }

    monkeypatch.setattr(
        cloudinary_ticket_file_storage,
        "upload_file",
        fake_upload_file,
    )

    storage = cloudinary_ticket_file_storage.CloudinaryTicketFileStorage()
    file = object()

    result = storage.store_ticket_file(
        file,
        user_email="Customer+Deals@Example.COM",
    )

    assert result == StoredTicketFile(
        ticket_url="https://tickets.example.com/ticket.pdf",
        public_id="ticket-public-id",
    )
    assert upload_calls == [
        {
            "file": file,
            "resource_type": "auto",
            "asset_folder": "tickets/customer_deals@example.com",
        }
    ]


def test_upload_file_forwards_asset_folder_to_cloudinary(monkeypatch):
    upload_calls = []

    def fake_cloudinary_upload(file, **options):
        upload_calls.append({"file": file, **options})
        return {"public_id": "ticket-public-id"}

    monkeypatch.setattr(
        cloudinary_service.cloudinary.uploader,
        "upload",
        fake_cloudinary_upload,
    )
    file = object()

    cloudinary_service.upload_file(
        file,
        resource_type="auto",
        asset_folder="tickets/customer@example.com",
    )

    assert upload_calls == [
        {
            "file": file,
            "resource_type": "auto",
            "asset_folder": "tickets/customer@example.com",
            "unique_filename": True,
            "overwrite": True,
        }
    ]
