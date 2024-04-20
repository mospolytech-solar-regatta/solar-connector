from typing import Optional

import serial
from pydantic import RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    redis_dsn: RedisDsn = 'redis://localhost:6379/1'
    redis_config_channel: str
    redis_config_apply_channel: str
    redis_status_update_channel: str
    redis_telemetry_channel: str
    redis_log_channel: str
    redis_land_queue_channel: str = 'land_queue_channel'
    serial_port: str
    serial_baudrate: Optional[int] = 115200
    serial_bytesize: Optional[int] = 8
    serial_parity: Optional[str] = serial.PARITY_NONE
    serial_stopbits: Optional[int] = 1
    serial_timeout: Optional[int] = None
