"""fix user_skills primary key

Revision ID: d1c86fc7d8e7
Revises: 68cc258717d5
Create Date: 2026-10-17 04:57:57.888062

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1c86fc7d8e7"
down_revision: Union[str, Sequence[str], None] = "68cc258717d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "user_skills_pkey",
        "user_skills",
        type_="primary",
    )

    op.create_primary_key(
        "user_skills_pkey",
        "user_skills",
        ["user_id", "skill_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
