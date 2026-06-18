import uuid
from datetime import date, datetime
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class SeguimientoDiario(Base):
    __tablename__ = "seguimientos_diarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendedor_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    fecha = Column(Date, default=date.today, index=True, nullable=False)
    mensaje_generado = Column(Text, nullable=False)
    enlace_whatsapp = Column(String, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)

    # Relationship
    vendedor = relationship("Usuario")
