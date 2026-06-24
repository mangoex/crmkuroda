import uuid
from sqlalchemy import Column, Float, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class SlightEdgePlan(Base):
    __tablename__ = "slight_edge_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    monthly_income_goal = Column(Float, default=0.0, nullable=False)
    ticket_average = Column(Float, default=0.0, nullable=False)
    conversion_rate = Column(Float, default=0.0, nullable=False)
    funnel_metrics = Column(JSON, nullable=True)  # Desglose: llamadas, citas, cotizaciones, ventas
    activities_config = Column(JSON, nullable=False)  # [{ "activity": "...", "points": N }]
    daily_points_goal = Column(Integer, default=10, nullable=False)

    # Relationships
    user = relationship("Usuario")
