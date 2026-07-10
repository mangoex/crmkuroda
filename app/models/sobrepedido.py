from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base
from datetime import datetime

class Sobrepedido(Base):
    __tablename__ = "sobrepedidos"

    id = Column(Integer, primary_key=True, index=True)
    id_pedido_erp = Column(Integer, index=True)
    factura = Column(String, index=True)
    fecha_venta = Column(String, index=True)
    numero_cliente = Column(String, index=True)
    cliente_nombre = Column(String)
    vendedor_codigo = Column(String, index=True)
    vendedor_nombre = Column(String, index=True)
    producto_sku = Column(String, index=True)
    producto_desc = Column(String)
    indicador = Column(String, index=True)
    grupo = Column(String, index=True)
    cantidad_pendiente = Column(Float)
    fecha_pedido = Column(String)  # Stored as YYYY-MM-DD
    estatus_compras = Column(String)
    proveedor = Column(String, index=True)
    disponibilidad_vl06o = Column(String)
    cantidad_disponible = Column(Float, default=0.0)
    fecha_disponibilidad = Column(String)
    dias_disponible = Column(Integer)
    motivo_estado = Column(String)
    estado_crm = Column(String, index=True)
    fecha_carga = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "id_pedido_erp": self.id_pedido_erp,
            "factura": self.factura,
            "fecha_venta": self.fecha_venta,
            "numero_cliente": self.numero_cliente,
            "cliente_nombre": self.cliente_nombre,
            "vendedor_codigo": self.vendedor_codigo,
            "vendedor_nombre": self.vendedor_nombre,
            "producto_sku": self.producto_sku,
            "producto_desc": self.producto_desc,
            "indicador": self.indicador,
            "grupo": self.grupo,
            "cantidad_pendiente": self.cantidad_pendiente,
            "fecha_pedido": self.fecha_pedido,
            "estatus_compras": self.estatus_compras,
            "proveedor": self.proveedor,
            "disponibilidad_vl06o": self.disponibilidad_vl06o,
            "cantidad_disponible": self.cantidad_disponible,
            "fecha_disponibilidad": self.fecha_disponibilidad,
            "dias_disponible": self.dias_disponible,
            "motivo_estado": self.motivo_estado,
            "estado_crm": self.estado_crm,
            "fecha_carga": self.fecha_carga.strftime("%Y-%m-%d %H:%M:%S") if self.fecha_carga else None
        }
