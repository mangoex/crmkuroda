"""merge quote performance and client feature heads

Revision ID: m3n4o5p6q7r8
Revises: k1e5f6a7b8c9, l2m3n4o5p6q7
Create Date: 2026-08-06
"""


revision = "m3n4o5p6q7r8"
down_revision = ("k1e5f6a7b8c9", "l2m3n4o5p6q7")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Unifica las dos ramas ya aplicables; no modifica tablas."""


def downgrade() -> None:
    """La bifurcación se restaura automáticamente al bajar de la unión."""
