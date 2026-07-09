from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base
from datetime import datetime

class Sobrepedido(Base):
    __tablename__ = "sobrepedidos"

    id = Column(Integer, primary_key=True, index=True)
    id_pedido_erp = Column(Integer, index=True)
    cliente_nombre = Column(String)
    vendedor_codigo = Column(String, index=True)
    vendedor_nombre = Column(String, index=True)
    producto_sku = Column(String, index=True)
    producto_desc = Column(String)
    cantidad_pendiente = Column(Float)
    fecha_pedido = Column(String)  # Stored as YYYY-MM-DD
    estatus_compras = Column(String)
    proveedor = Column(String, index=True)
    estado_crm = Column(String, index=True)
    fecha_carga = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "id_pedido_erp": self.id_pedido_erp,
            "cliente_nombre": self.cliente_nombre,
            "vendedor_codigo": self.vendedor_codigo,
            "vendedor_nombre": self.vendedor_nombre,
            "producto_sku": self.producto_sku,
            "producto_desc": self.producto_desc,
            "cantidad_pendiente": self.cantidad_pendiente,
            "fecha_pedido": self.fecha_pedido,
            "estatus_compras": self.estatus_compras,
            "proveedor": self.proveedor,
            "estado_crm": self.estado_crm,
            "fecha_carga": self.fecha_carga.strftime("%Y-%m-%d %H:%M:%S") if self.fecha_carga else None
        }
