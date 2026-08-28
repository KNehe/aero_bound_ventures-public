"""Cloudinary service for file uploads"""

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()


def configure_cloudinary():
    """
    Cloudinary automatically reads CLOUDINARY_URL from environment
    Format: cloudinary://api_key:api_secret@cloud_name
    """
    config = cloudinary.config(secure=True)
    return config


def upload_file(
    file,
    resource_type: str = "auto",
    *,
    asset_folder: str | None = None,
) -> dict:
    """
    Upload a file to Cloudinary

    Args:
        file: File object to upload
        resource_type: Type of resource (auto, image, video, raw)
        asset_folder: Cloudinary Media Library folder for the uploaded asset

    Returns:
        Dictionary containing upload result with public_id, secure_url, etc.
    """
    upload_options = {
        "resource_type": resource_type,
        "unique_filename": True,
        "overwrite": True,
    }
    if asset_folder:
        upload_options["asset_folder"] = asset_folder

    upload_result = cloudinary.uploader.upload(file, **upload_options)
    return upload_result
