"""add google oauth fields

Revision ID: a1b2c3d4e5f6
Revises: a5333a57cf02
Create Date: 2026-01-06

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "6cbffe648b06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add google_id column
    op.add_column("userindb", sa.Column("google_id", sa.String(), nullable=True))
    op.create_unique_constraint("uq_userindb_google_id", "userindb", ["google_id"])
    op.create_index("ix_userindb_google_id", "userindb", ["google_id"], unique=True)

    # Add auth_provider column with default 'email'
    op.add_column(
        "userindb",
        sa.Column("auth_provider", sa.String(), nullable=False, server_default="email"),
    )

    # Make password nullable for OAuth users
    op.alter_column("userindb", "password", nullable=True)


def downgrade() -> None:
    # Revert password to non-nullable
    op.alter_column("userindb", "password", nullable=False)

    # Remove auth_provider column
    op.drop_column("userindb", "auth_provider")

    # Remove google_id column and its constraints
    op.drop_index("ix_userindb_google_id", table_name="userindb")
    op.drop_constraint("uq_userindb_google_id", "userindb", type_="unique")
    op.drop_column("userindb", "google_id")
