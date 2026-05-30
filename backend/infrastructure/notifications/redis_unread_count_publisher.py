from uuid import UUID

from sqlmodel import Session

from backend.utils.notification_service import get_and_publish_unread_count


class RedisUnreadCountPublisher:
    def __init__(self, session: Session):
        self.session = session

    async def publish_for_user(self, user_id: UUID) -> int:
        return await get_and_publish_unread_count(self.session, user_id)
