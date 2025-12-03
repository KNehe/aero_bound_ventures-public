from functools import wraps
from typing import List, Union, Callable
from fastapi import Depends, HTTPException, status
from sqlmodel import Session
from backend.crud.database import get_session
from backend.utils.security import get_current_user
from backend.models.users import UserInDB
from backend.utils.permissions import PermissionChecker


def require_permissions(permissions: Union[str, List[str]], require_all: bool = True):
    """
    Decorator to require specific permissions for a route.

    Args:
        permissions: Single permission codename or list of permission codenames
        require_all: If True, user must have ALL permissions. If False, user needs ANY permission.

    Usage:
        @router.get("/flights")
        @require_permissions("flights.view_flight")
        async def get_flights(...):
            pass

        @router.post("/flights")
        @require_permissions(["flights.add_flight", "flights.manage_flights"], require_all=False)
        async def create_flight(...):
            pass
    """
    # Normalize to list
    perm_list = [permissions] if isinstance(permissions, str) else permissions

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: UserInDB = Depends(get_current_user),
            session: Session = Depends(get_session),
            **kwargs,
        ):
            # Check if user has required permissions
            if require_all:
                has_permission = PermissionChecker.has_perms(
                    session, current_user, perm_list
                )
            else:
                has_permission = PermissionChecker.has_any_perm(
                    session, current_user, perm_list
                )

            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required permissions: {', '.join(perm_list)}",
                )

            return await func(
                *args, current_user=current_user, session=session, **kwargs
            )

        return wrapper

    return decorator


def require_groups(groups: Union[str, List[str]], require_all: bool = True):
    """
    Decorator to require specific groups for a route.

    Args:
        groups: Single group name or list of group names
        require_all: If True, user must be in ALL groups. If False, user needs to be in ANY group.

    Usage:
        @router.get("/admin/dashboard")
        @require_groups("Admin")
        async def admin_dashboard(...):
            pass

        @router.post("/bookings")
        @require_groups(["Customer", "Agent"], require_all=False)
        async def create_booking(...):
            pass
    """
    # Normalize to list
    group_list = [groups] if isinstance(groups, str) else groups

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: UserInDB = Depends(get_current_user),
            session: Session = Depends(get_session),
            **kwargs,
        ):
            # Check if user belongs to required groups
            if require_all:
                in_group = PermissionChecker.has_groups(
                    session, current_user, group_list
                )
            else:
                in_group = PermissionChecker.has_any_group(
                    session, current_user, group_list
                )

            if not in_group:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required groups: {', '.join(group_list)}",
                )

            return await func(
                *args, current_user=current_user, session=session, **kwargs
            )

        return wrapper

    return decorator


def require_superuser():
    """
    Decorator to require superuser status for a route.

    Usage:
        @router.delete("/users/{user_id}")
        @require_superuser()
        async def delete_user(...):
            pass
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: UserInDB = Depends(get_current_user),
            session: Session = Depends(get_session),
            **kwargs,
        ):
            if not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Superuser access required",
                )

            return await func(
                *args, current_user=current_user, session=session, **kwargs
            )

        return wrapper

    return decorator


# FastAPI dependencies for direct use (alternative to decorators)
class PermissionDependency:
    """
    Dependency class for checking permissions in FastAPI routes.

    Usage:
        @router.get("/flights", dependencies=[Depends(PermissionDependency(["flights.view_flight"]))])
        async def get_flights():
            pass
    """

    def __init__(self, permissions: Union[str, List[str]], require_all: bool = True):
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
        @router.get("/admin/dashboard", dependencies=[Depends(GroupDependency("Admin"))])
        async def admin_dashboard():
            pass
    """

    def __init__(self, groups: Union[str, List[str]], require_all: bool = True):
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
