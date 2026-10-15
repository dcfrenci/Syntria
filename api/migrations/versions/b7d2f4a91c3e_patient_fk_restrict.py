"""patient foreign keys: CASCADE -> RESTRICT

Revision ID: b7d2f4a91c3e
Revises: edeb179f2afe
"""
from alembic import op

revision = "b7d2f4a91c3e"
down_revision = "edeb179f2afe"
branch_labels = None
depends_on = None


def _recreate(ondelete: str) -> None:
    for table in ("quotes", "reservations"):
        name = f"{table}_patient_id_fkey"  # Postgres default name for the baseline's unnamed FK
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, "persons", ["patient_id"], ["id"], ondelete=ondelete)


def upgrade() -> None:
    _recreate("RESTRICT")


def downgrade() -> None:
    _recreate("CASCADE")