"""add monthly commercial goals

Revision ID: n4o5p6q7r8s
Revises: m3n4o5p6q7r8
Create Date: 2026-08-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "n4o5p6q7r8s"
down_revision = "m3n4o5p6q7r8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "metas_comerciales",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("vendedor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sucursal", sa.String(), nullable=True),
        sa.Column("mes", sa.Date(), nullable=False),
        sa.Column("monto_objetivo", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("creado_por_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("tipo IN ('general', 'vendedor', 'sucursal')", name="ck_metas_comerciales_tipo"),
        sa.CheckConstraint(
            "(tipo = 'general' AND vendedor_id IS NULL AND sucursal IS NULL) OR "
            "(tipo = 'vendedor' AND vendedor_id IS NOT NULL AND sucursal IS NULL) OR "
            "(tipo = 'sucursal' AND vendedor_id IS NULL AND sucursal IS NOT NULL)",
            name="ck_metas_comerciales_alcance",
        ),
        sa.ForeignKeyConstraint(["vendedor_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creado_por_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_metas_comerciales_mes", "metas_comerciales", ["mes"])
    op.create_index("ix_metas_comerciales_vendedor_id", "metas_comerciales", ["vendedor_id"])
    op.create_index("ix_metas_comerciales_sucursal", "metas_comerciales", ["sucursal"])
    op.create_index("ix_metas_comerciales_tipo_mes", "metas_comerciales", ["tipo", "mes"])
    op.create_index(
        "uq_metas_comerciales_general_mes",
        "metas_comerciales",
        ["mes"],
        unique=True,
        postgresql_where=sa.text("tipo = 'general'"),
    )
    op.create_index(
        "uq_metas_comerciales_vendedor_mes",
        "metas_comerciales",
        ["mes", "vendedor_id"],
        unique=True,
        postgresql_where=sa.text("tipo = 'vendedor'"),
    )
    op.create_index(
        "uq_metas_comerciales_sucursal_mes",
        "metas_comerciales",
        ["mes", "sucursal"],
        unique=True,
        postgresql_where=sa.text("tipo = 'sucursal'"),
    )


def downgrade() -> None:
    op.drop_index("uq_metas_comerciales_sucursal_mes", table_name="metas_comerciales")
    op.drop_index("uq_metas_comerciales_vendedor_mes", table_name="metas_comerciales")
    op.drop_index("uq_metas_comerciales_general_mes", table_name="metas_comerciales")
    op.drop_index("ix_metas_comerciales_tipo_mes", table_name="metas_comerciales")
    op.drop_index("ix_metas_comerciales_sucursal", table_name="metas_comerciales")
    op.drop_index("ix_metas_comerciales_vendedor_id", table_name="metas_comerciales")
    op.drop_index("ix_metas_comerciales_mes", table_name="metas_comerciales")
    op.drop_table("metas_comerciales")
