import uuid

from sqlalchemy import Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RegistroAcceso(Base):
    """Registra una sesion iniciada para el tablero operativo."""

    __tablename__ = "registros_acceso"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    entrada = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    salida = Column(DateTime(timezone=True), nullable=True)

    usuario = relationship("Usuario")
