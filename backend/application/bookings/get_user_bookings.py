from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class BookingListItemRecord:
    id: UUID
    pnr: str | None
    status: str
    created_at: datetime
    ticket_url: str | None


@dataclass(frozen=True)
class UserBookingsPage:
    items: list[BookingListItemRecord]
    next_cursor: str | None
    has_more: bool
    has_previous: bool
    total_count: int | None
    limit: int

    def as_cache_payload(self) -> dict:
        return {
            "items": [
                {**asdict(item), "created_at": item.created_at.isoformat()}
                for item in self.items
            ],
            "next_cursor": self.next_cursor,
            "has_more": self.has_more,
            "has_previous": self.has_previous,
            "total_count": self.total_count,
            "limit": self.limit,
        }

    @classmethod
    def from_cache_payload(cls, payload: dict) -> "UserBookingsPage":
        return cls(
            items=[
                BookingListItemRecord(
                    id=item["id"] if isinstance(item["id"], UUID) else UUID(item["id"]),
                    pnr=item["pnr"],
                    status=item["status"],
                    created_at=datetime.fromisoformat(
                        item["created_at"].replace("Z", "+00:00")
                    ),
                    ticket_url=item["ticket_url"],
                )
                for item in payload.get("items", [])
            ],
            next_cursor=payload.get("next_cursor"),
            has_more=payload.get("has_more", False),
            has_previous=payload.get("has_previous", False),
            total_count=payload.get("total_count"),
            limit=payload.get("limit", 20),
        )


class UserBookingsRepository(Protocol):
    def get_user_bookings(
        self,
        *,
        user_id: UUID,
        cursor: str | None,
        limit: int,
        include_count: bool,
    ) -> UserBookingsPage: ...


class UserBookingsCache(Protocol):
    def get(self, cache_key: str) -> dict | None: ...

    def set(self, cache_key: str, value: dict) -> None: ...


class GetUserBookings:
    def __init__(
        self,
        *,
        booking_repository: UserBookingsRepository,
        cache: UserBookingsCache,
    ):
        self.booking_repository = booking_repository
        self.cache = cache

    def execute(
        self,
        *,
        user_id: UUID,
        cursor: str | None,
        limit: int,
        include_count: bool,
    ) -> UserBookingsPage:
        cache_key = self._cache_key(
            user_id=user_id,
            cursor=cursor,
            limit=limit,
            include_count=include_count,
        )

        cached_page = self.cache.get(cache_key)
        if cached_page:
            return UserBookingsPage.from_cache_payload(cached_page)

        page = self.booking_repository.get_user_bookings(
            user_id=user_id,
            cursor=cursor,
            limit=limit,
            include_count=include_count,
        )
        self.cache.set(cache_key, page.as_cache_payload())
        return page

    @staticmethod
    def _cache_key(
        *,
        user_id: UUID,
        cursor: str | None,
        limit: int,
        include_count: bool,
    ) -> str:
        return (
            f"user_bookings:{str(user_id)}:"
            f"{cursor or 'first'}:{limit}:{int(include_count)}"
        )
