from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from backend.application.users.user_accounts import (
    AuthenticatedUserRecord,
    GroupRecord,
    PasswordResetCandidateRecord,
    PermissionRecord,
    UserAccountRecord,
    UserProfileRecord,
    build_user_profile,
)
from backend.models.permissions import Group
from backend.models.users import UserInDB


class SqlModelUserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> UserAccountRecord | None:
        user = self.session.exec(
            select(UserInDB).where(UserInDB.email == email)
        ).first()
        if not user:
            return None

        return self._to_account_record(user)

    def create_email_user(self, *, email: str, password_hash: str) -> UserAccountRecord:
        user = UserInDB(email=email, password=password_hash, auth_provider="email")
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return self._to_account_record(user)

    def get_user_for_authentication(self, email: str) -> AuthenticatedUserRecord | None:
        user = self.session.exec(
            select(UserInDB)
            .where(UserInDB.email == email)
            .options(selectinload(UserInDB.groups).selectinload(Group.permissions))
        ).first()
        if not user:
            return None

        return AuthenticatedUserRecord(
            id=user.id,
            email=str(user.email),
            auth_provider=user.auth_provider or "email",
            password_hash=user.password,
            groups=self._to_group_records(user.groups),
        )

    def store_password_reset_token(
        self, *, email: str, token_hash: str, expires_at: datetime
    ) -> bool:
        user = self.session.exec(
            select(UserInDB).where(UserInDB.email == email)
        ).first()
        if not user:
            return False

        user.reset_token = token_hash
        user.reset_token_expires = expires_at
        self.session.add(user)
        self.session.commit()
        return True

    def get_password_reset_candidates(self) -> list[PasswordResetCandidateRecord]:
        users = self.session.exec(
            select(UserInDB).where(UserInDB.reset_token.is_not(None))
        ).all()

        return [
            PasswordResetCandidateRecord(
                id=user.id,
                email=str(user.email),
                reset_token_hash=user.reset_token,
                reset_token_expires=user.reset_token_expires,
            )
            for user in users
        ]

    def update_password_and_clear_reset_token(
        self, *, user_id: UUID, password_hash: str
    ) -> bool:
        user = self.session.exec(select(UserInDB).where(UserInDB.id == user_id)).first()
        if not user:
            return False

        user.password = password_hash
        user.reset_token = None
        user.reset_token_expires = None
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return True

    def update_user_password(self, *, user_id: UUID, password_hash: str) -> bool:
        user = self.session.exec(select(UserInDB).where(UserInDB.id == user_id)).first()
        if not user:
            return False

        user.password = password_hash
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return True

    @classmethod
    def to_user_profile_record(cls, user: UserInDB) -> UserProfileRecord:
        return build_user_profile(
            user_id=user.id,
            email=str(user.email),
            auth_provider=user.auth_provider,
            groups=cls._to_group_records(user.groups),
        )

    @staticmethod
    def _to_account_record(user: UserInDB) -> UserAccountRecord:
        return UserAccountRecord(
            id=user.id,
            email=str(user.email),
            auth_provider=user.auth_provider or "email",
        )

    @staticmethod
    def _to_group_records(groups: list[Group]) -> tuple[GroupRecord, ...]:
        return tuple(
            GroupRecord(
                name=group.name,
                description=group.description,
                permissions=tuple(
                    PermissionRecord(
                        name=permission.name,
                        codename=permission.codename,
                        description=permission.description,
                    )
                    for permission in group.permissions
                ),
            )
            for group in groups
        )
