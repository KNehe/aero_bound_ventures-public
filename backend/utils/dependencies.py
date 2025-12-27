"""
FastAPI dependency classes for RBAC (Role-Based Access Control).

This module provides dependency injection classes for protecting routes with
permissions, groups, and superuser checks in FastAPI applications.
"""

from fastapi import Depends, HTTPException, status
from sqlmodel import Session
from backend.crud.database import get_session
from backend.utils.security import get_current_user
from backend.models.users import UserInDB
from backend.utils.permissions import PermissionChecker
from backend.utils.consumer import EventConsumer
from backend.utils.constants import KAFKA_GROUP_ID

# Create a single global instance for the application lifespan
# This follows the Dependency Injection pattern where we configure it once
# and pass it to the lifespan handler.
notification_consumer = EventConsumer(group_id=KAFKA_GROUP_ID)


# FastAPI dependency classes for route protection
class PermissionDependency:
    """
    Dependency class for checking permissions in FastAPI routes.

    Usage:
        # Option 1: Route-level protection (no access to user in function)
        @router.get("/flights", dependencies=[Depends(PermissionDependency("flights.view_flight"))])
        async def get_flights():
            pass

        # Option 2: Function parameter (access to current_user)
        @router.get("/flights")
        async def get_flights(current_user: UserInDB = Depends(PermissionDependency("flights.view_flight"))):
            # current_user is available here
            pass

        # Option 3: Multiple permissions (require all)
        @router.post("/flights", dependencies=[Depends(PermissionDependency(["flights.add_flight", "flights.change_flight"]))])
        async def create_flight():
            pass

        # Option 4: Multiple permissions (require any)
        @router.post("/flights")
        async def create_flight(
            current_user: UserInDB = Depends(PermissionDependency(["flights.add_flight", "admin.all"], require_all=False))
        ):
            pass
    """

    def __init__(self, permissions: str | list[str], require_all: bool = True):
        self.permissions = (
            [permissions] if isinstance(permissions, str) else permissions
        )
        self.require_all = require_all

    def __call__(
        self,
        current_user: UserInDB = Depends(get_current_user),
        session: Session = Depends(get_session),
    ):
        if self.require_all:
            has_permission = PermissionChecker.has_perms(
                session, current_user, self.permissions
            )
        else:
            has_permission = PermissionChecker.has_any_perm(
                session, current_user, self.permissions
            )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required permissions: {', '.join(self.permissions)}",
            )
        return current_user


class GroupDependency:
    """
    Dependency class for checking group membership in FastAPI routes.

    Usage:
        # Single group
        @router.get("/admin/dashboard", dependencies=[Depends(GroupDependency("Admin"))])
        async def admin_dashboard():
            pass

        # Multiple groups (require all)
        @router.post("/bookings")
        async def create_booking(current_user: UserInDB = Depends(GroupDependency(["Customer", "Verified"]))):
            pass

        # Multiple groups (require any)
        @router.post("/support")
        async def support_action(
            current_user: UserInDB = Depends(GroupDependency(["Admin", "Support"], require_all=False))
        ):
            pass
    """

    def __init__(self, groups: str | list[str], require_all: bool = True):
        self.groups = [groups] if isinstance(groups, str) else groups
        self.require_all = require_all

    def __call__(
        self,
        current_user: UserInDB = Depends(get_current_user),
        session: Session = Depends(get_session),
    ):
        if self.require_all:
            in_group = PermissionChecker.has_groups(session, current_user, self.groups)
        else:
            in_group = PermissionChecker.has_any_group(
                session, current_user, self.groups
            )

        if not in_group:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required groups: {', '.join(self.groups)}",
            )
        return current_user


class SuperuserDependency:
    """
    Dependency class for requiring superuser status.

    Usage:
        @router.delete("/users/{user_id}", dependencies=[Depends(SuperuserDependency())])
        async def delete_user(user_id: str):
            pass
    """

    def __call__(
        self,
        current_user: UserInDB = Depends(get_current_user),
        session: Session = Depends(get_session),
    ):
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superuser access required",
            )
        return current_user
