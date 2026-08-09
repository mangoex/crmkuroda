from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base
from datetime import datetime

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    sociedad = Column(String(50), nullable=True)
    numero_cliente = Column(String(50), nullable=True, index=True)
    nombre = Column(String(255), nullable=False, index=True)
    nombre_contacto = Column(String(255), nullable=True)
    rfc = Column(String(20), nullable=True, index=True)
    tipo_persona = Column(String(50), nullable=True, index=True)
    calle = Column(String(255), nullable=True)
    numero_exterior = Column(String(50), nullable=True)
    colonia = Column(String(150), nullable=True, index=True)
    codigo_postal = Column(String(20), nullable=True)
    poblacion = Column(String(150), nullable=True, index=True)
    estado = Column(String(100), nullable=True)
    telefono = Column(String(50), nullable=True)
    celular = Column(String(50), nullable=True)
    fax = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "sociedad": self.sociedad or "",
            "numero_cliente": self.numero_cliente or "",
            "nombre": self.nombre or "",
            "nombre_contacto": self.nombre_contacto or "",
            "rfc": self.rfc or "",
            "tipo_persona": self.tipo_persona or "",
            "calle": self.calle or "",
            "numero_exterior": self.numero_exterior or "",
            "colonia": self.colonia or "",
            "codigo_postal": self.codigo_postal or "",
            "poblacion": self.poblacion or "",
            "estado": self.estado or "",
            "telefono": self.telefono or "",
            "celular": self.celular or "",
            "fax": self.fax or "",
            "email": self.email or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
