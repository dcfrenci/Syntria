"""patient foreign keys: CASCADE -> RESTRICT

Revision ID: b7d2f4a91c3e
Revises: edeb179f2afe
"""
from alembic import op
import sqlalchemy as sa

revision = "b7d2f4a91c3e"
down_revision = "edeb179f2afe"
branch_labels = None
depends_on = None


def _recreate(ondelete: str) -> None:
    insp = sa.inspect(op.get_bind())
    for table in ("quotes", "reservations"):
        for fk in insp.get_foreign_keys(table):
            if fk["constrained_columns"] == ["patient_id"]:
                op.drop_constraint(fk["name"], table, type_="foreignkey")
        op.create_foreign_key(
            f"{table}_patient_id_fkey", table, "persons", ["patient_id"], ["id"], ondelete=ondelete
        )


def upgrade() -> None:
    _recreate("RESTRICT")


def downgrade() -> None:
    _recreate("CASCADE")