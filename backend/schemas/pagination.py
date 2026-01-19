"""
Generic pagination response schemas.

Provides type-safe, reusable pagination response models using generics.
"""

from typing import TypeVar, Generic
from pydantic import BaseModel, Field


T = TypeVar("T")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """
    Generic cursor-based paginated response.

    This provides a consistent structure for all paginated endpoints.

    Attributes:
        items: List of items for the current page
        next_cursor: Encoded cursor for the next page (None if last page)
        prev_cursor: Encoded cursor for the previous page (None if first page)
        has_more: Whether there are more items after this page
        has_previous: Whether there are items before this page
        total_count: Total number of items (optional, may be None if expensive to compute)
        limit: The limit that was applied
    """

    items: list[T]
    next_cursor: str | None = Field(
        default=None, description="Cursor for the next page, null if no more pages"
    )
    prev_cursor: str | None = Field(
        default=None, description="Cursor for the previous page, null if first page"
    )
    has_more: bool = Field(description="Whether there are more items after this page")
    has_previous: bool = Field(
        default=False, description="Whether there are items before this page"
    )
    total_count: int | None = Field(
        default=None,
        description="Total count of items (may be null if expensive to compute)",
    )
    limit: int = Field(description="Maximum number of items returned per page")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [],
                "next_cursor": "eyJjcmVhdGVkX2F0IjoiMjAyNC0wMS0wMVQxMjowMDowMCIsImlkIjoiMTIzIn0=",
                "prev_cursor": None,
                "has_more": True,
                "has_previous": False,
                "total_count": 100,
                "limit": 20,
            }
        }
    }


class PaginationParams(BaseModel):
    """
    Common pagination parameters for reuse in endpoints.
    """

    cursor: str | None = Field(
        default=None, description="Cursor for pagination (None for first page)"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of records to return (1-100)",
    )
    include_count: bool = Field(
        default=False,
        description="Whether to include total_count in response (may be slower)",
    )
