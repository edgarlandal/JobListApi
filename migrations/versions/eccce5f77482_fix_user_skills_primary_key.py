"""fix_user_skills_primary_key

Revision ID: eccce5f77482
Revises: 19159a8b19b5
Create Date: 2026-10-17 06:21:48.442624

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "eccce5f77482"
down_revision: Union[str, Sequence[str], None] = "19159a8b19b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        op.f("user_skills_pkey"),
        "user_skills",
        type_="primary",
    )

    op.create_primary_key(
        op.f("user_skills_pkey"),
        "user_skills",
        ["user_id", "skill_id"],
    )


def downgrade() -> None:
    repeated_skill = (
        op.get_bind()
        .execute(
            sa.text("""
            SELECT EXISTS (
                SELECT 1
                FROM user_skills
                GROUP BY skill_id
                HAVING COUNT(*) > 1
            )
        """)
        )
        .scalar_one()
    )

    if repeated_skill:
        raise RuntimeError(
            "No se puede revertir: hay habilidades asignadas a varios usuarios."
        )

    op.drop_constraint(
        op.f("user_skills_pkey"),
        "user_skills",
        type_="primary",
    )

    op.create_primary_key(
        op.f("user_skills_pkey"),
        "user_skills",
        ["skill_id"],
    )
