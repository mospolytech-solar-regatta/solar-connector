from datetime import datetime
from typing import Any

from pydantic import BaseModel
from enum import IntEnum
from app.wire.config import Config as SerialConfig


class Telemetry(BaseModel):
    created_at: datetime
    controller_watts: int
    time_to_go: int
    controller_volts: float
    MPPT_volts: float
    MPPT_watts: float
    motor_temp: float
    motor_revols: float
    position_lat: float
    position_lng: float

