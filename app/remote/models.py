from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, Field


class Telemetry(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    controller_watts: int
    time_to_go: int
    controller_volts: float
    MPPT_volts: float
    MPPT_watts: float
    motor_temp: float
    motor_revols: float
    position_lat: float
    position_lng: float


class LandData(BaseModel):
    class Priority(IntEnum):
        low = 0
        high = 1

    priority: Priority
    created_at: datetime
    id: int
    data: str
