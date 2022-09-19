from ctypes import Union
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from enum import IntEnum


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


class PayloadType(IntEnum):
    telemetry = 1
    config = 2


class Payload(BaseModel):
    type: PayloadType
    data: Any