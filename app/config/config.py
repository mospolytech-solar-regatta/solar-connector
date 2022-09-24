from typing import Optional

import serial
from pydantic import BaseSettings, RedisDsn


class Config(BaseSettings):
    redis_dsn: RedisDsn = 'redis://localhost:6379/1'
    redis_config_channel: str
    redis_config_apply_channel: str
    redis_status_update_channel: str
    redis_telemetry_channel: str
    serial_port: str
    serial_baudrate: Optional[int] = 115200
    serial_bytesize: Optional[int] = 8
    serial_parity: Optional[str] = serial.PARITY_NONE
    serial_stopbits: Optional[int] = 1
    serial_timeout: Optional[int] = None

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
