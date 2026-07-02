from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base
from datetime import datetime

class InventarioAbcf(Base):
    __tablename__ = "inventario_abcf"

    id = Column(Integer, primary_key=True, index=True)
    nombre_centro = Column(String, index=True)
    almacen = Column(String)
    numero_proveedor = Column(String)
    nombre_proveedor = Column(String)
    abc_f = Column(String, index=True)
    codigo_material = Column(String, index=True)
    descripcion_material = Column(String)
    cantidad_propia = Column(Float)
    existencia_consignacion = Column(Float)
    entregas_pendientes = Column(Float)
    existencia_transito = Column(Float)
    existencia_bloqueada = Column(Float)
    existencia_control_calidad = Column(Float)
    umb = Column(String)
    costo_promedio_unitario = Column(Float)
    importe_inventario_propio = Column(Float)
    valor_consignacion_proveedor = Column(Float)
    ubicacion = Column(String)
    grupo_materiales = Column(String)
    descrip_gpo_materiales = Column(String)
    codigo_anterior_material = Column(String)
    abc = Column(String)
    fecha_ultimo_inventario = Column(String) # as string to avoid parsing issues, or DateTime

    def to_dict(self):
        return {
            "id": self.id,
            "nombre_centro": self.nombre_centro,
            "almacen": self.almacen,
            "numero_proveedor": self.numero_proveedor,
            "nombre_proveedor": self.nombre_proveedor,
            "abc_f": self.abc_f,
            "codigo_material": self.codigo_material,
            "descripcion_material": self.descripcion_material,
            "cantidad_propia": self.cantidad_propia,
            "existencia_consignacion": self.existencia_consignacion,
            "entregas_pendientes": self.entregas_pendientes,
            "existencia_transito": self.existencia_transito,
            "existencia_bloqueada": self.existencia_bloqueada,
            "existencia_control_calidad": self.existencia_control_calidad,
            "umb": self.umb,
            "costo_promedio_unitario": self.costo_promedio_unitario,
            "importe_inventario_propio": self.importe_inventario_propio,
            "valor_consignacion_proveedor": self.valor_consignacion_proveedor,
            "ubicacion": self.ubicacion,
            "grupo_materiales": self.grupo_materiales,
            "descrip_gpo_materiales": self.descrip_gpo_materiales,
            "codigo_anterior_material": self.codigo_anterior_material,
            "abc": self.abc,
            "fecha_ultimo_inventario": self.fecha_ultimo_inventario
        }
