from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ActivityConfigItem(BaseModel):
    activity: str = Field(..., description="Nombre de la actividad/disciplina.")
    points: int = Field(..., ge=1, description="Peso en puntos asignados a la actividad.")

class SlightEdgePlanCreate(BaseModel):
    monthly_income_goal: float = Field(..., ge=0.0)
    ticket_average: float = Field(..., ge=0.0)
    conversion_rate: float = Field(..., ge=0.0, le=100.0)
    activities_config: List[ActivityConfigItem]
    daily_points_goal: int = Field(default=10, ge=1)

class SlightEdgeLogCreate(BaseModel):
    date_str: Optional[str] = None  # YYYY-MM-DD
    completed_activities: Dict[str, int]  # { "activity_name": count }

class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str

class ChatPayload(BaseModel):
    messages: List[ChatMessage]
