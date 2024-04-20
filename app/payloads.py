from datetime import datetime
from enum import IntEnum
from typing import Any

from pydantic import BaseModel

from app.client.serialclient import SerialConfig
from app.status import AppStatus


class PayloadType(IntEnum):
    telemetry = 1
    config = 2
    config_update = 3
    status_update = 4
    land_data = 5


class ConfigUpdated(BaseModel):
    timestamp: datetime
    config: SerialConfig


class UpdateStatus(BaseModel):
    timestamp: datetime
    status: AppStatus


class Payload(BaseModel):
    type: PayloadType
    data: Any
