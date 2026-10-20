"""presets: at most one active row

Revision ID: c1a9e0d47b52
Revises: b7d2f4a91c3e
"""
from alembic import op
import sqlalchemy as sa

revision = "c1a9e0d47b52"
down_revision = "b7d2f4a91c3e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE presets SET is_active = false "
        "WHERE is_active AND id <> (SELECT max(id) FROM presets WHERE is_active)"
    )
    op.create_index(
        "uq_presets_one_active", "presets", ["is_active"],
        unique=True, postgresql_where=sa.text("is_active"),
    )


def downgrade() -> None:
    op.drop_index("uq_presets_one_active", table_name="presets")