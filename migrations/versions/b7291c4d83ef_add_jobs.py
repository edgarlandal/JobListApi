"""Add jobs and its PostgreSQL enum types."""
from alembic import op
import sqlalchemy as sa

revision = "b7291c4d83ef"
down_revision = "8a1609544292"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("enterprise", sa.String(255), nullable=False),
        sa.Column("role", sa.String(255), nullable=False),
        sa.Column("salary", sa.Integer(), nullable=True),
        sa.Column("type_salary", sa.Enum("DAILY", "WEEKLY", "MONTHLY", "YEARLY", name="type_salary"), nullable=True),
        sa.Column("mode", sa.Enum("ONSITE", "HYBRID", "REMOTE", name="mode_work"), nullable=False),
        sa.Column("location", sa.String(255), nullable=False),
        sa.Column("status_job", sa.Enum("SEND", "RH", "IN_PROCESS", "TECHNICAL_IN", "OFFER", "REJECTION", "CANCELLED", name="status_job"), nullable=False),
        sa.Column("last_update_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])


def downgrade():
    op.drop_index("ix_jobs_user_id", table_name="jobs")
    op.drop_table("jobs")
    for name in ("status_job", "mode_work", "type_salary"):
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
