import uuid
from sqlalchemy import Column, String, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, index=True, nullable=False)  # e.g., 'kuroda'
    name = Column(String, nullable=False)
    global_sales_target = Column(Float, default=0.0, nullable=False)
    global_goals = Column(Text, nullable=True)
    csv_drive_url = Column(String, nullable=True)
