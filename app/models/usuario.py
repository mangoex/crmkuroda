import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    rol = Column(String, nullable=False)  # 'admin', 'gerente', 'vendedor'
    telefono_whatsapp = Column(String, unique=True, index=True, nullable=True)
    codigo_vendedor = Column(String, unique=True, index=True, nullable=True)  # e.g., 'C01'
    nombre_completo = Column(String, nullable=True)

    # Relationships
    metas = relationship("Meta", back_populates="vendedor", cascade="all, delete-orphan")
    cotizaciones = relationship("Cotizacion", back_populates="vendedor", cascade="all, delete-orphan")
