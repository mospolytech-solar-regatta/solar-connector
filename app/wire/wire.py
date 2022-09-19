import datetime
import json
from typing import Optional

import pydantic
import serial

from app.remote.models import Telemetry, PayloadType, Payload, ConfigUpdated
from app.wire.config import Config


class WireConnection:
    allowed_payload_types = [PayloadType.config]

    def __init__(self, config: Config):
        self.config = config
        self.serial = self.create_serial()
        self.buffer = b""

    def create_serial(self):
        try:
            return serial.Serial(self.config.port, self.config.baudrate, timeout=self.config.timeout,
                                 parity=self.config.parity, rtscts=1, stopbits=self.config.stopbits,
                                 bytesize=self.config.bytesize)
        except:
            return serial.Serial()

    def restart_serial(self):
        if self.serial.is_open:
            self.serial.close()
        self.serial = self.create_serial()

        try:
            if not self.serial.is_open:
                self.serial.open()
        except serial.SerialException:
            pass

    def step(self):
        if self.serial.is_open:
            return self.read()  # TODO: add multiple return

    def read(self):
        payload = None
        data: bytes = self.serial.read()
        if data:
            is_newline = data.find(b'\n')
            if is_newline != -1:
                self.buffer += data[:is_newline]
                payload = self.get_telemetry_payload()
                self.buffer = data[is_newline:].strip()
            else:
                self.buffer += data
        return payload

    def get_telemetry_payload(self) -> Optional[Payload]:
        try:
            data = json.loads(self.buffer.decode('UTF-8'))
            data = Telemetry(**data)
            payload = Payload(data=data, type=PayloadType.telemetry)
            return payload
        except json.JSONDecodeError:
            return None
        except pydantic.ValidationError:
            return None

    def get_config_update_payload(self) -> Optional[Payload]:
        config_update = ConfigUpdated(timestamp=datetime.datetime.now(), config=self.config)
        payload = Payload(type=PayloadType.config_update, data=config_update)
        return payload

    def __process_payload(self, msg: Payload):
        if msg.type == PayloadType.config:
            self.config = msg.data
            self.restart_serial()
            return self.get_config_update_payload()

    def process_payloads(self, *payloads):
        res = []
        for i in payloads:
            res.append(self.__process_payload(i))
        return res
