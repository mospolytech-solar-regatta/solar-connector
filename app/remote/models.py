from datetime import datetime
from typing import Optional

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
