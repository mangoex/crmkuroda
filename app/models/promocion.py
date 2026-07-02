from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base
from datetime import datetime

class Promocion(Base):
    __tablename__ = "promociones"

    id = Column(Integer, primary_key=True, index=True)
    centro = Column(String, index=True)
    descrip_gpo_materiales = Column(String)
    indicador_abc = Column(String)
    codigo_material = Column(String, index=True)
    descripcion_material = Column(String)
    unidad_medida = Column(String)
    costo_promedio = Column(Float)
    costo_promedio_moneda = Column(Float)
    costo_estandar = Column(Float)
    precio_promocion = Column(Float)
    moneda = Column(String)
    valido_hasta = Column(DateTime)
    costo_estandar_promocion = Column(Float)
    margen_promocion = Column(Float)
    proveedor = Column(String)
    inventario_disponible = Column(Float)

    def to_dict(self):
        return {
            "id": self.id,
            "centro": self.centro,
            "descrip_gpo_materiales": self.descrip_gpo_materiales,
            "indicador_abc": self.indicador_abc,
            "codigo_material": self.codigo_material,
            "descripcion_material": self.descripcion_material,
            "precio_promocion": self.precio_promocion,
            "moneda": self.moneda,
            "margen_promocion": self.margen_promocion,
            "proveedor": self.proveedor,
            "inventario_disponible": self.inventario_disponible,
            "valido_hasta": self.valido_hasta.isoformat() if self.valido_hasta else None
        }
