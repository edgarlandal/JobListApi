"""Recovered baseline matching the existing Docker database.

The original revision files were missing. This baseline preserves the revision
already recorded in that database and creates its schema on fresh databases.
It does not reconstruct the original intermediate migration history.
"""
from alembic import op
import sqlalchemy as sa

revision = "8a1609544292"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("firstname", sa.String(255), nullable=False),
        sa.Column("lastname", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("ADMIN", "USER", name="user_role_enum"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_firstname", "users", ["firstname"])
    op.create_index("ix_users_lastname", "users", ["lastname"])
    op.create_index("idx_users_email_is_active", "users", ["email", "is_active"])
    op.create_table(
        "refresh_token",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("family_id", sa.String(36), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_token_token_hash", "refresh_token", ["token_hash"])
    op.create_index("ix_refresh_token_family_id", "refresh_token", ["family_id"])


def downgrade():
    op.drop_table("refresh_token")
    op.drop_table("users")
    sa.Enum(name="user_role_enum").drop(op.get_bind(), checkfirst=True)
