import typer
import sys
from pathlib import Path

# Add the parent directory to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))


from sqlmodel import Session
from backend.crud.database import engine
from backend.crud.users import get_user_by_email, create_user
from backend.crud.permissions import GroupCRUD, PermissionCRUD, UserPermissionCRUD
from backend.models.permissions import Group
from backend.models.constants import (
    ADMIN_GROUP_NAME,
    ADMIN_GROUP_DESCRIPTION,
    ADMIN_PERMISSIONS,
    MIN_PASSWORD_LENGTH,
)
from getpass import getpass

app = typer.Typer()


def prompt_for_credentials() -> tuple[str, str]:
    """
    Prompt user for email and password with validation.
    
    Returns:
        tuple[str, str]: (email, password)
    
    Raises:
        typer.Exit: If passwords don't match or password is too short
    """
    email = typer.prompt("Enter email")
    
    password = getpass("Enter password: ")
    password_confirm = getpass("Confirm password: ")
    
    if password != password_confirm:
        typer.echo("Error: Passwords do not match", err=True)
        raise typer.Exit(code=1)
    
    if len(password) < MIN_PASSWORD_LENGTH:
        typer.echo(f"Error: Password must be at least {MIN_PASSWORD_LENGTH} characters", err=True)
        raise typer.Exit(code=1)
    
    return email, password


def ensure_admin_group(session: Session) -> Group:
    """
    Ensure the Admin group exists with all required permissions.
    Creates the group and permissions if they don't exist.
    
    Args:
        session: Database session
        
    Returns:
        Group: The Admin group instance
    """
    admin_group = GroupCRUD.get_group_by_name(session, ADMIN_GROUP_NAME)
    if not admin_group:
        typer.echo(f"{ADMIN_GROUP_NAME} group not found. Creating {ADMIN_GROUP_NAME} group...")
        admin_group = GroupCRUD.create_group(
            session, 
            name=ADMIN_GROUP_NAME, 
            description=ADMIN_GROUP_DESCRIPTION
        )
        
        for name, codename, description in ADMIN_PERMISSIONS:
            perm = PermissionCRUD.get_permission_by_codename(session, codename)
            if not perm:
                perm = PermissionCRUD.create_permission(session, name, codename, description)
            
            GroupCRUD.add_permission_to_group(session, admin_group.id, perm.id)
        
        typer.echo(f"{ADMIN_GROUP_NAME} group and permissions created successfully.")
    
    return admin_group


@app.command(name="create-super-user")
def createsuperuser():
    """Create a superuser with full system access."""
    email, password = prompt_for_credentials()
    
    with Session(engine) as session:
        existing_user = get_user_by_email(session, email)
        if existing_user:
            typer.echo(f"Error: User with email {email} already exists", err=True)
            raise typer.Exit(code=1)
        
        user = create_user(session, email, password)
        user.is_superuser = True
        session.add(user)
        session.commit()
        session.refresh(user)
        
        typer.echo(f"Superuser created successfully: {user.email}")
        typer.echo("This user has full access to all system features.")


@app.command(name="create-admin")
def createadminuser():
    """Create an admin user with admin group permissions."""
    email, password = prompt_for_credentials()
    
    with Session(engine) as session:
        existing_user = get_user_by_email(session, email)
        if existing_user:
            typer.echo(f"Error: User with email {email} already exists", err=True)
            raise typer.Exit(code=1)
        
        user = create_user(session, email, password)
        
        admin_group = ensure_admin_group(session)
        
        UserPermissionCRUD.assign_group_to_user(session, user.id, admin_group.id)
        
        typer.echo(f"Admin user created successfully: {user.email}")
        typer.echo(f"User has been assigned to the '{ADMIN_GROUP_NAME}' group.")

if __name__ == "__main__":
    app()