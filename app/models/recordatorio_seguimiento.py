import uuid
from datetime import date, datetime
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class RecordatorioSeguimiento(Base):
    __tablename__ = "recordatorios_seguimiento"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cotizacion_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cotizaciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vendedor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fecha_programada = Column(Date, nullable=False, index=True)
    nota = Column(Text, nullable=True)
    completado = Column(Boolean, nullable=False, default=False)
    completado_en = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    cotizacion = relationship("Cotizacion")
    vendedor = relationship("Usuario")
