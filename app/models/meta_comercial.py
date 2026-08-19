import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class MetaComercial(Base):
    """Meta mensual auditable para empresa, vendedor o sucursal comercial."""

    __tablename__ = "metas_comerciales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo = Column(String, nullable=False)  # general | vendedor | sucursal
    vendedor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    sucursal = Column(String, nullable=True, index=True)
    canal = Column(String, nullable=True, index=True)
    mes = Column(Date, nullable=False, index=True)  # Siempre el primer día del mes.
    monto_objetivo = Column(Numeric(precision=14, scale=2), nullable=False)
    descripcion = Column(Text, nullable=True)
    creado_por_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
