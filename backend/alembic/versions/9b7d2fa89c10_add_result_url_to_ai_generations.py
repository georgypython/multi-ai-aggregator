"""add result url to ai generations

Revision ID: 9b7d2fa89c10
Revises: be8fc3627462
Create Date: 2026-03-06 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9b7d2fa89c10"
down_revision: Union[str, Sequence[str], None] = "be8fc3627462"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ai_generations", sa.Column("result_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_generations", "result_url")
