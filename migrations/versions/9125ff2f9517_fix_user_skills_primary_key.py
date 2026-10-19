"""fix_user_skills_primary_key

Revision ID: 9125ff2f9517
Revises: eccce5f77482
Create Date: 2026-10-17 06:24:27.848026

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9125ff2f9517"
down_revision: Union[str, Sequence[str], None] = "eccce5f77482"
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
