"""fix_user_skills_primary_key

Revision ID: 19159a8b19b5
Revises: eca70fb784b3
Create Date: 2026-10-17 06:21:02.262497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19159a8b19b5'
down_revision: Union[str, Sequence[str], None] = 'eca70fb784b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
