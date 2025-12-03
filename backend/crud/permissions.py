from sqlmodel import Session, select
import uuid
from backend.models.permissions import (
    Permission,
    Group,
    UserPermission,
    UserGroup,
    GroupPermission,
)


class PermissionCRUD:
    """CRUD operations for Permission model"""

    @staticmethod
    def create_permission(
        session: Session, name: str, codename: str, description: str | None = None
    ) -> Permission:
        """Create a new permission"""
        permission = Permission(name=name, codename=codename, description=description)
        session.add(permission)
        session.commit()
        session.refresh(permission)
        return permission

    @staticmethod
    def get_permission_by_id(
        session: Session, permission_id: uuid.UUID
    ) -> Permission | None:
        """Get permission by ID"""
        return session.get(Permission, permission_id)

    @staticmethod
    def get_permission_by_codename(
        session: Session, codename: str
    ) -> Permission | None:
        """Get permission by codename"""
        statement = select(Permission).where(Permission.codename == codename)
        return session.exec(statement).first()

    @staticmethod
    def get_all_permissions(session: Session) -> list[Permission]:
        """Get all permissions"""
        statement = select(Permission)
        return list(session.exec(statement).all())

    @staticmethod
    def update_permission(
        session: Session,
        permission_id: uuid.UUID,
        name: str | None = None,
        codename: str | None = None,
        description: str | None = None,
    ) -> Permission | None:
        """Update permission"""
        permission = session.get(Permission, permission_id)
        if not permission:
            return None

        if name:
            permission.name = name
        if codename:
            permission.codename = codename
        if description is not None:
            permission.description = description

        session.add(permission)
        session.commit()
        session.refresh(permission)
        return permission

    @staticmethod
    def delete_permission(session: Session, permission_id: uuid.UUID) -> bool:
        """Delete permission"""
        permission = session.get(Permission, permission_id)
        if not permission:
            return False

        session.delete(permission)
        session.commit()
        return True


class GroupCRUD:
    """CRUD operations for Group model"""

    @staticmethod
    def create_group(
        session: Session, name: str, description: str | None = None
    ) -> Group:
        """Create a new group"""
        group = Group(name=name, description=description)
        session.add(group)
        session.commit()
        session.refresh(group)
        return group

    @staticmethod
    def get_group_by_id(session: Session, group_id: uuid.UUID) -> Group | None:
        """Get group by ID"""
        return session.get(Group, group_id)

    @staticmethod
    def get_group_by_name(session: Session, name: str) -> Group | None:
        """Get group by name"""
        statement = select(Group).where(Group.name == name)
        return session.exec(statement).first()

    @staticmethod
    def get_all_groups(session: Session) -> list[Group]:
        """Get all groups"""
        statement = select(Group)
        return list(session.exec(statement).all())

    @staticmethod
    def update_group(
        session: Session,
        group_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Group | None:
        """Update group"""
        group = session.get(Group, group_id)
        if not group:
            return None

        if name:
            group.name = name
        if description is not None:
            group.description = description

        session.add(group)
        session.commit()
        session.refresh(group)
        return group

    @staticmethod
    def delete_group(session: Session, group_id: uuid.UUID) -> bool:
        """Delete group"""
        group = session.get(Group, group_id)
        if not group:
            return False

        session.delete(group)
        session.commit()
        return True

    @staticmethod
    def add_permission_to_group(
        session: Session, group_id: uuid.UUID, permission_id: uuid.UUID
    ) -> bool:
        """Add a permission to a group"""
        # Check if relationship already exists
        statement = select(GroupPermission).where(
            GroupPermission.group_id == group_id,
            GroupPermission.permission_id == permission_id,
        )
        existing = session.exec(statement).first()
        if existing:
            return True

        group_permission = GroupPermission(
            group_id=group_id, permission_id=permission_id
        )
        session.add(group_permission)
        session.commit()
        return True

    @staticmethod
    def remove_permission_from_group(
        session: Session, group_id: uuid.UUID, permission_id: uuid.UUID
    ) -> bool:
        """Remove a permission from a group"""
        statement = select(GroupPermission).where(
            GroupPermission.group_id == group_id,
            GroupPermission.permission_id == permission_id,
        )
        group_permission = session.exec(statement).first()
        if not group_permission:
            return False

        session.delete(group_permission)
        session.commit()
        return True

    @staticmethod
    def get_group_permissions(
        session: Session, group_id: uuid.UUID
    ) -> list[Permission]:
        """Get all permissions for a group"""
        statement = (
            select(Permission)
            .join(GroupPermission)
            .where(GroupPermission.group_id == group_id)
        )
        return list(session.exec(statement).all())


class UserPermissionCRUD:
    """CRUD operations for user permissions and groups"""

    @staticmethod
    def assign_permission_to_user(
        session: Session, user_id: uuid.UUID, permission_id: uuid.UUID
    ) -> bool:
        """Assign a permission directly to a user"""
        # Check if relationship already exists
        statement = select(UserPermission).where(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id,
        )
        existing = session.exec(statement).first()
        if existing:
            return True

        user_permission = UserPermission(user_id=user_id, permission_id=permission_id)
        session.add(user_permission)
        session.commit()
        return True

    @staticmethod
    def remove_permission_from_user(
        session: Session, user_id: uuid.UUID, permission_id: uuid.UUID
    ) -> bool:
        """Remove a permission from a user"""
        statement = select(UserPermission).where(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id,
        )
        user_permission = session.exec(statement).first()
        if not user_permission:
            return False

        session.delete(user_permission)
        session.commit()
        return True

    @staticmethod
    def assign_group_to_user(
        session: Session, user_id: uuid.UUID, group_id: uuid.UUID
    ) -> bool:
        """Assign a group to a user"""
        # Check if relationship already exists
        statement = select(UserGroup).where(
            UserGroup.user_id == user_id, UserGroup.group_id == group_id
        )
        existing = session.exec(statement).first()
        if existing:
            return True

        user_group = UserGroup(user_id=user_id, group_id=group_id)
        session.add(user_group)
        session.commit()
        return True

    @staticmethod
    def remove_group_from_user(
        session: Session, user_id: uuid.UUID, group_id: uuid.UUID
    ) -> bool:
        """Remove a group from a user"""
        statement = select(UserGroup).where(
            UserGroup.user_id == user_id, UserGroup.group_id == group_id
        )
        user_group = session.exec(statement).first()
        if not user_group:
            return False

        session.delete(user_group)
        session.commit()
        return True

    @staticmethod
    def get_user_groups(session: Session, user_id: uuid.UUID) -> list[Group]:
        """Get all groups for a user"""
        statement = select(Group).join(UserGroup).where(UserGroup.user_id == user_id)
        return list(session.exec(statement).all())

    @staticmethod
    def get_user_direct_permissions(
        session: Session, user_id: uuid.UUID
    ) -> list[Permission]:
        """Get direct permissions assigned to a user (not through groups)"""
        statement = (
            select(Permission)
            .join(UserPermission)
            .where(UserPermission.user_id == user_id)
        )
        return list(session.exec(statement).all())

    @staticmethod
    def get_user_all_permissions(
        session: Session, user_id: uuid.UUID
    ) -> list[Permission]:
        """Get all permissions for a user (direct + from groups)"""
        # Get direct permissions
        direct_perms = UserPermissionCRUD.get_user_direct_permissions(session, user_id)

        # Get permissions from groups
        statement = (
            select(Permission)
            .join(GroupPermission)
            .join(UserGroup, UserGroup.group_id == GroupPermission.group_id)
            .where(UserGroup.user_id == user_id)
        )
        group_perms = list(session.exec(statement).all())

        # Combine and deduplicate
        all_perms = {perm.id: perm for perm in direct_perms + group_perms}
        return list(all_perms.values())
