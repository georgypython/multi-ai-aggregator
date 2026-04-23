"""add plan generation limits

Revision ID: 5d3a3c7e8b21
Revises: 330f7a84a903
Create Date: 2026-04-23 14:53:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5d3a3c7e8b21"
down_revision: Union[str, Sequence[str], None] = "330f7a84a903"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "plans",
        sa.Column("llm_max_limit", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "plans",
        sa.Column("image_max_limit", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "plans",
        sa.Column("video_max_limit", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("plans", "video_max_limit")
    op.drop_column("plans", "image_max_limit")
    op.drop_column("plans", "llm_max_limit")
