"""fix_user_skills_primary_key

Revision ID: eca70fb784b3
Revises: d1c86fc7d8e7
Create Date: 2026-10-16 23:19:14.135607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eca70fb784b3'
down_revision: Union[str, Sequence[str], None] = 'd1c86fc7d8e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
