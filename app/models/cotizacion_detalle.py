import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CotizacionItem(Base):
    __tablename__ = "cotizacion_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cotizacion_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cotizaciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    codigo_material = Column(String, nullable=False, index=True)
    descripcion = Column(String, nullable=True)
    indicador_abcf = Column(String, nullable=True, index=True)
    unidad_medida = Column(String, nullable=True)
    precio_venta = Column(Numeric(precision=14, scale=2), nullable=False, default=0)
    familia = Column(String, nullable=True, index=True)
    grupo_materiales = Column(String, nullable=True, index=True)
    cantidad_cotizada = Column(Numeric(precision=14, scale=3), nullable=False, default=1)
    importe_cotizado = Column(Numeric(precision=14, scale=2), nullable=False, default=0)
    cantidad_facturada = Column(Numeric(precision=14, scale=3), nullable=False, default=0)
    importe_facturado = Column(Numeric(precision=14, scale=2), nullable=False, default=0)
    es_promocion = Column(Boolean, nullable=False, default=False, index=True)
    precio_promocion = Column(Numeric(precision=14, scale=2), nullable=True)

    cotizacion = relationship("Cotizacion", back_populates="items_detalle")


class CotizacionComentario(Base):
    __tablename__ = "cotizacion_comentarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cotizacion_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cotizaciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    autor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    comentario = Column(Text, nullable=False)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    editado_en = Column(DateTime, nullable=True)

    cotizacion = relationship("Cotizacion", back_populates="comentarios_seguimiento")
    autor = relationship("Usuario")


class CanalVenta(Base):
    __tablename__ = "canales_venta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_origen = Column(String, nullable=False, unique=True, index=True)
    nombre_normalizado = Column(String, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
