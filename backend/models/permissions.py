from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING, List, Optional
import uuid
from datetime import datetime

if TYPE_CHECKING:
    from .users import UserInDB


# Link table for many-to-many relationship between Group and Permission
class GroupPermission(SQLModel, table=True):
    """Link table for Group-Permission many-to-many relationship"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    group_id: uuid.UUID = Field(foreign_key="group.id", nullable=False)
    permission_id: uuid.UUID = Field(foreign_key="permission.id", nullable=False)
    assigned_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


# Link table for many-to-many relationship between User and Group
class UserGroup(SQLModel, table=True):
    """Link table for User-Group many-to-many relationship"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    user_id: uuid.UUID = Field(foreign_key="userindb.id", nullable=False)
    group_id: uuid.UUID = Field(foreign_key="group.id", nullable=False)
    assigned_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


# Link table for many-to-many relationship between User and Permission (direct permissions)
class UserPermission(SQLModel, table=True):
    """Link table for User-Permission many-to-many relationship (direct permissions)"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    user_id: uuid.UUID = Field(foreign_key="userindb.id", nullable=False)
    permission_id: uuid.UUID = Field(foreign_key="permission.id", nullable=False)
    assigned_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Permission(SQLModel, table=True):
    """Permission model - represents individual permissions like 'view_flight', 'add_booking'"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    name: str = Field(unique=True, nullable=False, index=True)  # e.g., "view_flight"
    codename: str = Field(
        unique=True, nullable=False, index=True
    )  # e.g., "flights.view_flight"
    description: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    groups: List["Group"] = Relationship(
        back_populates="permissions", link_model=GroupPermission
    )
    users: List["UserInDB"] = Relationship(
        back_populates="permissions", link_model=UserPermission
    )


class Group(SQLModel, table=True):
    """Group model - represents role groups like 'admin', 'flight_manager', 'customer'"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    name: str = Field(
        unique=True, nullable=False, index=True
    )  # e.g., "Admin", "Flight Manager"
    description: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    permissions: List["Permission"] = Relationship(
        back_populates="groups", link_model=GroupPermission
    )
    users: List["UserInDB"] = Relationship(
        back_populates="groups", link_model=UserGroup
    )


# Define full link table implementations
GroupPermission.id = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
GroupPermission.group_id = Field(foreign_key="group.id", nullable=False)
GroupPermission.permission_id = Field(foreign_key="permission.id", nullable=False)
GroupPermission.assigned_at = Field(default_factory=datetime.utcnow, nullable=False)

UserGroup.id = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
UserGroup.user_id = Field(foreign_key="userindb.id", nullable=False)
UserGroup.group_id = Field(foreign_key="group.id", nullable=False)
UserGroup.assigned_at = Field(default_factory=datetime.utcnow, nullable=False)

UserPermission.id = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
UserPermission.user_id = Field(foreign_key="userindb.id", nullable=False)
UserPermission.permission_id = Field(foreign_key="permission.id", nullable=False)
UserPermission.assigned_at = Field(default_factory=datetime.utcnow, nullable=False)
