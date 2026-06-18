import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class LogAgente(Base):
    __tablename__ = "logs_agentes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agente_nombre = Column(String, index=True, nullable=False) # e.g., 'Metas', 'Seguimiento', 'Analista'
    prompt_enviado = Column(Text, nullable=False)
    respuesta_recibida = Column(Text, nullable=False)
    fecha_ejecucion = Column(DateTime, default=datetime.utcnow, index=True)
