"""preset images table, presets JSON -> JSONB, optimistic-lock version

Revision ID: d4e7b2a60f13
Revises: c1a9e0d47b52
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d4e7b2a60f13"
down_revision = "c1a9e0d47b52"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "preset_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content_type", sa.String(length=30), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    for col in ("elements", "margins"):
        op.alter_column(
            "presets", col, existing_type=sa.JSON(), type_=postgresql.JSONB(),
            existing_nullable=True, postgresql_using=f"{col}::jsonb",
        )
    op.add_column("presets", sa.Column("version", sa.Integer(), server_default="1", nullable=False))


def downgrade() -> None:
    op.drop_column("presets", "version")
    for col in ("elements", "margins"):
        op.alter_column(
            "presets", col, existing_type=postgresql.JSONB(), type_=sa.JSON(),
            existing_nullable=True, postgresql_using=f"{col}::json",
        )
    op.drop_table("preset_images")