from datetime import datetime, timezone
from uuid import uuid4

from backend.application.bookings.get_user_bookings import (
    BookingListItemRecord,
    GetUserBookings,
    UserBookingsPage,
)


USER_ID = uuid4()
BOOKING_ID = uuid4()
CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class StubUserBookingsRepository:
    def __init__(self, page: UserBookingsPage):
        self.page = page
        self.calls = []

    def get_user_bookings(
        self,
        *,
        user_id,
        cursor,
        limit,
        include_count,
    ):
        self.calls.append(
            {
                "user_id": user_id,
                "cursor": cursor,
                "limit": limit,
                "include_count": include_count,
            }
        )
        return self.page


class StubUserBookingsCache:
    def __init__(self, cached_page=None):
        self.cached_page = cached_page
        self.calls = []
        self.set_calls = []

    def get(self, cache_key: str):
        self.calls.append(cache_key)
        return self.cached_page

    def set(self, cache_key: str, value: dict) -> None:
        self.set_calls.append({"cache_key": cache_key, "value": value})


def make_page() -> UserBookingsPage:
    return UserBookingsPage(
        items=[
            BookingListItemRecord(
                id=BOOKING_ID,
                pnr="PNR123",
                status="confirmed",
                created_at=CREATED_AT,
                ticket_url="https://tickets.example.com/ticket.pdf",
            )
        ],
        next_cursor="cursor_2",
        has_more=True,
        has_previous=False,
        total_count=1,
        limit=20,
    )


def test_get_user_bookings_reads_from_repository_and_caches_result():
    repository = StubUserBookingsRepository(page=make_page())
    cache = StubUserBookingsCache()
    use_case = GetUserBookings(
        booking_repository=repository,
        cache=cache,
    )

    result = use_case.execute(
        user_id=USER_ID,
        cursor=None,
        limit=20,
        include_count=True,
    )

    assert result == make_page()
    assert repository.calls == [
        {
            "user_id": USER_ID,
            "cursor": None,
            "limit": 20,
            "include_count": True,
        }
    ]
    assert cache.set_calls


def test_get_user_bookings_returns_cached_page_when_available():
    cached_page = make_page().as_cache_payload()
    repository = StubUserBookingsRepository(page=make_page())
    cache = StubUserBookingsCache(cached_page=cached_page)
    use_case = GetUserBookings(
        booking_repository=repository,
        cache=cache,
    )

    result = use_case.execute(
        user_id=USER_ID,
        cursor="cursor_1",
        limit=20,
        include_count=False,
    )

    assert result == make_page()
    assert repository.calls == []
