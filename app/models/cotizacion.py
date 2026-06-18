import uuid
from sqlalchemy import Column, String, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendedor_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    cliente_nombre = Column(String, nullable=False)
    datos_contacto = Column(JSONB, nullable=False)  # e.g., {"email": "...", "telefono": "..."}
    items = Column(JSONB, nullable=False)  # e.g., [{"producto": "...", "cantidad": 2, "precio_unitario": 100}]
    total = Column(Numeric(precision=12, scale=2), nullable=False)
    texto_propuesta = Column(Text, nullable=True)

    # Relationships
    vendedor = relationship("Usuario", back_populates="cotizaciones")
