from typing import Optional

import serial
from pydantic import BaseSettings


class Config(BaseSettings):
    port: str
    baudrate: Optional[int] = 115200
    bytesize: Optional[int] = 8
    parity: Optional[str] = serial.PARITY_NONE
    stopbits: Optional[int] = 1
    timeout: Optional[int] = 0
