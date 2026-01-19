"""Tests for cursor-based pagination utilities."""

import uuid
from datetime import datetime, timezone, timedelta

import pytest
from backend.utils.pagination import (
    encode_cursor,
    decode_cursor,
    CursorPaginator,
    MAX_PAGINATION_LIMIT,
)


class TestCursorEncoding:
    """Tests for cursor encoding/decoding functions."""

    def test_encode_decode_roundtrip_datetime_uuid(self):
        """Test that encoding and decoding round-trips correctly."""
        original = {
            "created_at": datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc),
            "id": uuid.UUID("12345678-1234-5678-1234-567812345678"),
        }

        encoded = encode_cursor(original)
        decoded = decode_cursor(encoded)

        assert decoded["created_at"] == original["created_at"]
        assert decoded["id"] == original["id"]

    def test_encode_decode_with_string(self):
        """Test encoding with string values."""
        original = {"name": "test_value"}

        encoded = encode_cursor(original)
        decoded = decode_cursor(encoded)

        assert decoded["name"] == "test_value"

    def test_encode_decode_with_numbers(self):
        """Test encoding with numeric values."""
        original = {"count": 42, "price": 19.99}

        encoded = encode_cursor(original)
        decoded = decode_cursor(encoded)

        assert decoded["count"] == 42
        assert decoded["price"] == pytest.approx(19.99)

    def test_decode_invalid_cursor_raises_error(self):
        """Test that invalid cursor raises ValueError."""
        with pytest.raises(ValueError, match="Invalid cursor format"):
            decode_cursor("not_valid_base64!!!")

    def test_cursor_is_url_safe(self):
        """Test that encoded cursor is URL-safe."""
        original = {"created_at": datetime.now(timezone.utc), "id": uuid.uuid4()}
        encoded = encode_cursor(original)

        # URL-safe base64 should not contain +, /, or =
        assert "+" not in encoded
        assert "/" not in encoded


class TestCursorPaginator:
    """Tests for CursorPaginator class."""

    def test_limit_capped_at_max(self):
        """Test that limit is capped at MAX_PAGINATION_LIMIT."""
        paginator = CursorPaginator(
            cursor=None,
            limit=500,  # Way above max
            order_fields=["created_at", "id"],
        )

        assert paginator.limit == MAX_PAGINATION_LIMIT

    def test_limit_preserved_when_valid(self):
        """Test that valid limit is preserved."""
        paginator = CursorPaginator(
            cursor=None,
            limit=25,
            order_fields=["created_at", "id"],
        )

        assert paginator.limit == 25

    def test_build_result_detects_has_more(self):
        """Test that build_result correctly detects has_more."""
        paginator = CursorPaginator(
            cursor=None,
            limit=2,
            order_fields=["created_at", "id"],
        )

        # Simulate 3 items returned (limit + 1)
        class MockItem:
            def __init__(self, i):
                self.created_at = datetime.now(timezone.utc) - timedelta(hours=i)
                self.id = uuid.uuid4()

        items = [MockItem(i) for i in range(3)]

        result_items, next_cursor, has_more = paginator.build_result(
            items, lambda x: {"created_at": x.created_at, "id": x.id}
        )

        assert len(result_items) == 2
        assert has_more is True
        assert next_cursor is not None

    def test_build_result_no_more_items(self):
        """Test that build_result detects when no more items."""
        paginator = CursorPaginator(
            cursor=None,
            limit=5,
            order_fields=["created_at", "id"],
        )

        class MockItem:
            def __init__(self, i):
                self.created_at = datetime.now(timezone.utc) - timedelta(hours=i)
                self.id = uuid.uuid4()

        # Only 3 items, less than limit
        items = [MockItem(i) for i in range(3)]

        result_items, next_cursor, has_more = paginator.build_result(
            items, lambda x: {"created_at": x.created_at, "id": x.id}
        )

        assert len(result_items) == 3
        assert has_more is False
        assert next_cursor is None

    def test_build_result_empty_list(self):
        """Test that build_result handles empty list."""
        paginator = CursorPaginator(
            cursor=None,
            limit=10,
            order_fields=["created_at", "id"],
        )

        result_items, next_cursor, has_more = paginator.build_result(
            [], lambda x: {"created_at": x.created_at, "id": x.id}
        )

        assert len(result_items) == 0
        assert has_more is False
        assert next_cursor is None

    def test_cursor_values_decoded_correctly(self):
        """Test that cursor is decoded when provided."""
        cursor_data = {
            "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "id": uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        }
        cursor = encode_cursor(cursor_data)

        paginator = CursorPaginator(
            cursor=cursor,
            limit=10,
            order_fields=["created_at", "id"],
        )

        assert paginator._cursor_values is not None
        assert paginator._cursor_values["created_at"] == cursor_data["created_at"]
        assert paginator._cursor_values["id"] == cursor_data["id"]
