import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class ClienteDisponible(Base):
    __tablename__ = "clientes_disponibles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, nullable=False)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    comentarios = Column(Text, nullable=True)
    estado = Column(String, default="disponible", nullable=False)  # disponible, en_subasta, asignado
    asignado_a = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    vendedores_permitidos = Column(JSON, nullable=True)  # List of UUID strings
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    asignado_vendedor = relationship("Usuario", foreign_keys=[asignado_a])
    pujas = relationship("PujaCliente", back_populates="cliente", cascade="all, delete-orphan")

class PujaCliente(Base):
    __tablename__ = "pujas_clientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes_disponibles.id", ondelete="CASCADE"), nullable=False)
    vendedor_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    razon = Column(Text, nullable=False)
    estado = Column(String, default="pendiente", nullable=False)  # pendiente, aprobada, rechazada
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    cliente = relationship("ClienteDisponible", back_populates="pujas")
    vendedor = relationship("Usuario")
