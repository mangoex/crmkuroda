from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ActualizacionDatos(Base):
    """Marca de tiempo compartida para cada fuente de datos cargada por Excel."""

    __tablename__ = "actualizaciones_datos"

    tipo = Column(String, primary_key=True)
    actualizado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
