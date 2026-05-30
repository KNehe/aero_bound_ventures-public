from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from backend.application.oauth.oauth_login import OAuthGroupRecord, OAuthUserRecord
from backend.models.users import UserInDB


class SqlModelOAuthUserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_provider_user_id(self, provider_user_id: str) -> OAuthUserRecord | None:
        user = self.session.exec(
            select(UserInDB)
            .where(UserInDB.google_id == provider_user_id)
            .options(selectinload(UserInDB.groups))
        ).first()
        if not user:
            return None

        return self._to_record(user)

    def get_by_email(self, email: str) -> OAuthUserRecord | None:
        user = self.session.exec(
            select(UserInDB)
            .where(UserInDB.email == email)
            .options(selectinload(UserInDB.groups))
        ).first()
        if not user:
            return None

        return self._to_record(user)

    def create_provider_user(
        self, *, email: str, provider_user_id: str
    ) -> OAuthUserRecord:
        user = UserInDB(
            email=email,
            google_id=provider_user_id,
            auth_provider="google",
            password=None,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return self._to_record(user)

    def link_provider_account(
        self, *, user_id: UUID, provider_user_id: str
    ) -> OAuthUserRecord:
        user = self.session.exec(
            select(UserInDB)
            .where(UserInDB.id == user_id)
            .options(selectinload(UserInDB.groups))
        ).first()
        if not user:
            raise ValueError("Cannot link provider account to a missing user")

        user.google_id = provider_user_id
        if user.auth_provider == "email":
            user.auth_provider = "google"

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return self._to_record(user)

    @staticmethod
    def _to_record(user: UserInDB) -> OAuthUserRecord:
        return OAuthUserRecord(
            id=user.id,
            email=str(user.email),
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            auth_provider=user.auth_provider,
            groups=tuple(
                OAuthGroupRecord(id=group.id, name=group.name) for group in user.groups
            ),
        )
