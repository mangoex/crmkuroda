from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.core.database import Base


class PorEntregar(Base):
    __tablename__ = "por_entregar"

    id = Column(Integer, primary_key=True, index=True)
    factura = Column(String, index=True)
    producto_sku = Column(String, index=True)
    producto_desc = Column(String)
    cantidad_entregar = Column(Float)
    vendedor_codigo = Column(String, index=True)
    vendedor_nombre = Column(String, index=True)
    numero_cliente = Column(String, index=True)
    cliente_nombre = Column(String)
    fecha_disponibilidad = Column(String, index=True)
    dias_disponible = Column(Integer, index=True)
    estado_crm = Column(String, index=True)
    motivo_estado = Column(String)
    fecha_carga = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "factura": self.factura,
            "producto_sku": self.producto_sku,
            "producto_desc": self.producto_desc,
            "cantidad_entregar": self.cantidad_entregar,
            "vendedor_codigo": self.vendedor_codigo,
            "vendedor_nombre": self.vendedor_nombre,
            "numero_cliente": self.numero_cliente,
            "cliente_nombre": self.cliente_nombre,
            "fecha_disponibilidad": self.fecha_disponibilidad,
            "dias_disponible": self.dias_disponible,
            "estado_crm": self.estado_crm,
            "motivo_estado": self.motivo_estado,
            "fecha_carga": self.fecha_carga.strftime("%Y-%m-%d %H:%M:%S") if self.fecha_carga else None,
        }
