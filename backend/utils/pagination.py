"""
Generic cursor-based pagination utilities.

This module provides reusable utilities for implementing cursor-based pagination
across different models, offering O(log n + k) query performance with proper indexing.
"""

import base64
import uuid
from datetime import datetime
from typing import TypeVar, Sequence, Any

from sqlmodel import Session
from sqlalchemy import Select


MAX_PAGINATION_LIMIT = 100


def encode_cursor(fields: dict[str, Any]) -> str:
    """
    Encode pagination cursor from a dictionary of field values.

    Args:
        fields: Dictionary mapping field names to values.
                Supports datetime, UUID, str, int, float types.

    Returns:
        Base64-encoded cursor string

    Example:
        cursor = encode_cursor({"created_at": datetime.now(), "id": uuid.uuid4()})
    """
    parts = []
    for key, value in fields.items():
        if isinstance(value, datetime):
            serialized = f"dt:{value.isoformat()}"
        elif isinstance(value, uuid.UUID):
            serialized = f"uuid:{str(value)}"
        elif isinstance(value, (int, float)):
            serialized = f"num:{value}"
        else:
            serialized = f"str:{value}"
        parts.append(f"{key}={serialized}")

    cursor_str = "&".join(parts)
    return base64.urlsafe_b64encode(cursor_str.encode()).decode()


def decode_cursor(cursor: str) -> dict[str, Any]:
    """
    Decode a cursor string back into field values.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Dictionary mapping field names to their original typed values

    Raises:
        ValueError: If cursor format is invalid
    """
    try:
        cursor_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        fields = {}

        for part in cursor_str.split("&"):
            key, value = part.split("=", 1)
            type_prefix, data = value.split(":", 1)

            if type_prefix == "dt":
                fields[key] = datetime.fromisoformat(data)
            elif type_prefix == "uuid":
                fields[key] = uuid.UUID(data)
            elif type_prefix == "num":
                # Try int first, then float
                fields[key] = int(data) if "." not in data else float(data)
            else:  # str
                fields[key] = data

        return fields
    except Exception as e:
        raise ValueError(f"Invalid cursor format: {e}")


T = TypeVar("T")


class CursorPaginator:
    """
    A helper class for cursor-based pagination.

    This handles the common pattern of:
    1. Applying cursor filter to query
    2. Fetching limit + 1 rows to detect `has_more`
    3. Building the next cursor from the last item

    Example:
        paginator = CursorPaginator(
            cursor=request_cursor,
            limit=20,
            order_fields=["created_at", "id"],
            order_direction="desc"
        )

        query = select(Booking).where(Booking.user_id == user_id)
        query = paginator.apply_cursor_filter(query, Booking, cursor_fields)
        query = paginator.apply_ordering(query, Booking)
        query = paginator.apply_limit(query)

        items = session.exec(query).all()
        result = paginator.build_result(items, cursor_field_extractor)
    """

    def __init__(
        self,
        cursor: str | None,
        limit: int,
        order_fields: list[str],
        order_direction: str = "desc",
    ):
        """
        Initialize the paginator.

        Args:
            cursor: The cursor string (None for first page)
            limit: Maximum items per page (will be capped at MAX_PAGINATION_LIMIT)
            order_fields: List of field names used for ordering (primary, secondary, etc.)
            order_direction: "asc" or "desc"
        """
        self.cursor = cursor
        self.limit = min(limit, MAX_PAGINATION_LIMIT)
        self.order_fields = order_fields
        self.order_direction = order_direction
        self._cursor_values: dict[str, Any] | None = None

        if cursor:
            self._cursor_values = decode_cursor(cursor)

    def apply_cursor_filter(self, query: Select, model: type) -> Select:
        """
        Apply cursor-based WHERE clause to the query.

        For DESC ordering, this filters for items "before" the cursor
        (i.e., older created_at or same created_at with smaller id).

        Args:
            query: The SQLAlchemy Select query
            model: The SQLModel class to filter

        Returns:
            Query with cursor filter applied
        """
        if not self._cursor_values:
            return query

        # Build cursor condition for multi-field cursor (e.g., created_at, id)
        # For DESC: (created_at < cursor_created_at) OR
        #           (created_at == cursor_created_at AND id < cursor_id)
        from sqlalchemy import or_, and_

        conditions = []
        for i, field in enumerate(self.order_fields):
            if field not in self._cursor_values:
                continue

            cursor_val = self._cursor_values[field]
            col = getattr(model, field)

            if i == 0:
                # Primary field: simple less than / greater than
                if self.order_direction == "desc":
                    conditions.append(col < cursor_val)
                else:
                    conditions.append(col > cursor_val)
            else:
                # Secondary fields: equality on all previous + comparison on this
                eq_conditions = []
                for prev_field in self.order_fields[:i]:
                    if prev_field in self._cursor_values:
                        prev_col = getattr(model, prev_field)
                        eq_conditions.append(
                            prev_col == self._cursor_values[prev_field]
                        )

                if self.order_direction == "desc":
                    eq_conditions.append(col < cursor_val)
                else:
                    eq_conditions.append(col > cursor_val)

                conditions.append(and_(*eq_conditions))

        if conditions:
            query = query.where(or_(*conditions))

        return query

    def apply_ordering(self, query: Select, model: type) -> Select:
        """
        Apply ORDER BY clause based on order_fields and direction.

        Args:
            query: The SQLAlchemy Select query
            model: The SQLModel class

        Returns:
            Query with ordering applied
        """
        order_clauses = []
        for field in self.order_fields:
            col = getattr(model, field)
            if self.order_direction == "desc":
                order_clauses.append(col.desc())
            else:
                order_clauses.append(col.asc())

        return query.order_by(*order_clauses)

    def apply_limit(self, query: Select) -> Select:
        """
        Apply LIMIT clause (limit + 1 to detect has_more).

        Args:
            query: The SQLAlchemy Select query

        Returns:
            Query with limit applied
        """
        return query.limit(self.limit + 1)

    def build_result(
        self, items: Sequence[T], cursor_field_extractor: callable
    ) -> tuple[list[T], str | None, bool]:
        """
        Process query results and build pagination metadata.

        Args:
            items: The query results (may include extra item for has_more detection)
            cursor_field_extractor: Function that extracts cursor fields from an item
                                    Should return dict like {"created_at": ..., "id": ...}

        Returns:
            Tuple of (trimmed_items, next_cursor, has_more)
        """
        items_list = list(items)
        has_more = len(items_list) > self.limit

        if has_more:
            items_list = items_list[: self.limit]

        next_cursor = None
        if has_more and items_list:
            last_item = items_list[-1]
            cursor_fields = cursor_field_extractor(last_item)
            next_cursor = encode_cursor(cursor_fields)

        return items_list, next_cursor, has_more


def get_total_count(session: Session, query: Select) -> int:
    """
    Get total count for a query (use sparingly, can be expensive).

    This strips ORDER BY and LIMIT from the query and counts results.

    Args:
        session: Database session
        query: The base query (before limit/offset)

    Returns:
        Total count of matching rows
    """
    from sqlalchemy import func, select as sa_select

    # Create a count query from the subquery
    count_query = sa_select(func.count()).select_from(query.subquery())
    result = session.execute(count_query)
    return result.scalar() or 0
