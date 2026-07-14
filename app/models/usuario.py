import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from app.core.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    rol = Column(String, nullable=False)  # 'admin', 'gerente', 'vendedor', 'soporte'
    telefono_whatsapp = Column(String, unique=False, index=True, nullable=True)
    codigo_vendedor = Column(String, unique=True, index=True, nullable=True)  # e.g., 'C01'
    nombre_completo = Column(String, nullable=True)
    avatar = Column(String, nullable=True)
    # Jerarquia padre->hijos (1 nivel, solo entre vendedores).
    # NULL = sin padre (ver solo sus datos). SET NULL si se borra al padre.
    vendedor_padre_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    metas = relationship("Meta", back_populates="vendedor", cascade="all, delete-orphan")
    cotizaciones = relationship("Cotizacion", back_populates="vendedor", cascade="all, delete-orphan")
    # Self-FK: hijos que apuntan a este usuario como padre.
    # remote_side=[id] hace que 'vendedores_hijos' sea la lista de hijos
    # (usuarios cuyo vendedor_padre_id == este id).
    vendedores_hijos = relationship(
        "Usuario",
        backref=backref("vendedor_padre_obj", remote_side=[id]),
        foreign_keys=[vendedor_padre_id],
    )
