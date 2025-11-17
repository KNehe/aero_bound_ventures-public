"""add created_at to booking

Revision ID: 001
Revises:
Create Date: 2025-11-16

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add created_at column to booking table
    op.add_column(
        "booking",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    # Remove created_at column from booking table
    op.drop_column("booking", "created_at")
