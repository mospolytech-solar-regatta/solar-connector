from typing import Optional

import aioserial
from pydantic_settings import BaseSettings, SettingsConfigDict


class SerialConfig(BaseSettings):
    model_config = SettingsConfigDict(extra='ignore', env_file='.env', env_prefix='serial_')

    port: str
    baudrate: Optional[int] = 115200
    bytesize: Optional[int] = 8
    parity: Optional[str] = aioserial.PARITY_NONE
    stopbits: Optional[int] = 1
    timeout: Optional[int] = 0
