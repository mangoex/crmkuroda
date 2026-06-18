import uuid
from sqlalchemy import Column, String, Numeric, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Meta(Base):
    __tablename__ = "metas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendedor_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    descripcion = Column(String, nullable=False)
    monto_objetivo = Column(Numeric(precision=12, scale=2), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_limite = Column(Date, nullable=False)
    estado = Column(String, nullable=False, default="pendiente")  # 'pendiente', 'en_progreso', 'completada'

    # Relationships
    vendedor = relationship("Usuario", back_populates="metas")
