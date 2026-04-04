"""add is_whitelist to users

Revision ID: b7f3e2a1c9d4
Revises: abd82bf7015f
Create Date: 2026-04-04 23:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b7f3e2a1c9d4"
down_revision: Union[str, Sequence[str], None] = "abd82bf7015f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("is_whitelist", sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "is_whitelist")
