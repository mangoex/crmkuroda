import uuid
from datetime import date
from sqlalchemy import Column, Date, Integer, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class SlightEdgeLog(Base):
    __tablename__ = "slight_edge_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, default=date.today, nullable=False, index=True)
    completed_activities = Column(JSON, nullable=False)  # { "activity_name": count }
    total_points = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("Usuario")

    # Composite Unique Constraint: user_id + date
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_slight_edge_logs_user_date'),
    )
