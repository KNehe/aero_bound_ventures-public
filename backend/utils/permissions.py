from sqlmodel import Session
from models.users import UserInDB
from crud.permissions import UserPermissionCRUD


class PermissionChecker:
    """Utility class for checking user permissions"""

    @staticmethod
    def has_perm(session: Session, user: UserInDB, permission_codename: str) -> bool:
        """
        Check if user has a specific permission.
        Permission can be assigned directly or through a group.

        Args:
            session: Database session
            user: User instance
            permission_codename: Permission codename (e.g., 'flights.view_flight')

        Returns:
            bool: True if user has the permission, False otherwise
        """
        # Superusers have all permissions
        if user.is_superuser:
            return True

        # Check if user is active
        if not user.is_active:
            return False

        # Get all user permissions (direct + from groups)
        user_permissions = UserPermissionCRUD.get_user_all_permissions(session, user.id)

        # Check if permission codename exists in user's permissions
        return any(perm.codename == permission_codename for perm in user_permissions)

    @staticmethod
    def has_perms(
        session: Session, user: UserInDB, permission_codenames: list[str]
    ) -> bool:
        """
        Check if user has all specified permissions.

        Args:
            session: Database session
            user: User instance
            permission_codenames: List of permission codenames

        Returns:
            bool: True if user has all permissions, False otherwise
        """
        # Superusers have all permissions
        if user.is_superuser:
            return True

        # Check if user is active
        if not user.is_active:
            return False

        # Check all permissions
        return all(
            PermissionChecker.has_perm(session, user, perm_codename)
            for perm_codename in permission_codenames
        )

    @staticmethod
    def has_any_perm(
        session: Session, user: UserInDB, permission_codenames: list[str]
    ) -> bool:
        """
        Check if user has any of the specified permissions.

        Args:
            session: Database session
            user: User instance
            permission_codenames: List of permission codenames

        Returns:
            bool: True if user has at least one permission, False otherwise
        """
        # Superusers have all permissions
        if user.is_superuser:
            return True

        # Check if user is active
        if not user.is_active:
            return False

        # Check if user has at least one permission
        return any(
            PermissionChecker.has_perm(session, user, perm_codename)
            for perm_codename in permission_codenames
        )

    @staticmethod
    def has_group(session: Session, user: UserInDB, group_name: str) -> bool:
        """
        Check if user belongs to a specific group.

        Args:
            session: Database session
            user: User instance
            group_name: Group name (e.g., 'Admin', 'Flight Manager')

        Returns:
            bool: True if user belongs to the group, False otherwise
        """
        # Superusers are considered to be in all groups
        if user.is_superuser:
            return True

        # Check if user is active
        if not user.is_active:
            return False

        # Get user groups
        user_groups = UserPermissionCRUD.get_user_groups(session, user.id)

        # Check if group name exists in user's groups
        return any(group.name == group_name for group in user_groups)

    @staticmethod
    def has_groups(session: Session, user: UserInDB, group_names: list[str]) -> bool:
        """
        Check if user belongs to all specified groups.

        Args:
            session: Database session
            user: User instance
            group_names: List of group names

        Returns:
            bool: True if user belongs to all groups, False otherwise
        """
        # Superusers are considered to be in all groups
        if user.is_superuser:
            return True

        # Check if user is active
        if not user.is_active:
            return False

        # Check all groups
        return all(
            PermissionChecker.has_group(session, user, group_name)
            for group_name in group_names
        )

    @staticmethod
    def has_any_group(session: Session, user: UserInDB, group_names: list[str]) -> bool:
        """
        Check if user belongs to any of the specified groups.

        Args:
            session: Database session
            user: User instance
            group_names: List of group names

        Returns:
            bool: True if user belongs to at least one group, False otherwise
        """
        # Superusers are considered to be in all groups
        if user.is_superuser:
            return True

        # Check if user is active
        if not user.is_active:
            return False

        # Check if user belongs to at least one group
        return any(
            PermissionChecker.has_group(session, user, group_name)
            for group_name in group_names
        )


# Convenience functions for direct use
def user_has_perm(session: Session, user: UserInDB, permission_codename: str) -> bool:
    """Check if user has a specific permission"""
    return PermissionChecker.has_perm(session, user, permission_codename)


def user_has_perms(
    session: Session, user: UserInDB, permission_codenames: list[str]
) -> bool:
    """Check if user has all specified permissions"""
    return PermissionChecker.has_perms(session, user, permission_codenames)


def user_has_any_perm(
    session: Session, user: UserInDB, permission_codenames: list[str]
) -> bool:
    """Check if user has any of the specified permissions"""
    return PermissionChecker.has_any_perm(session, user, permission_codenames)


def user_in_group(session: Session, user: UserInDB, group_name: str) -> bool:
    """Check if user belongs to a specific group"""
    return PermissionChecker.has_group(session, user, group_name)


def user_in_groups(session: Session, user: UserInDB, group_names: list[str]) -> bool:
    """Check if user belongs to all specified groups"""
    return PermissionChecker.has_groups(session, user, group_names)
