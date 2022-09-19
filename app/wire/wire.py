import json

import pydantic
import serial
from app.wire.config import Config
from app.remote.models import Telemetry, PayloadType, Payload


class WireConnection:
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

    def run(self, remote_iter):
        while True:
            payload = None
            if self.serial.is_open:
                payload = self.read()

            msg = remote_iter(payload)
            if msg is not None:
                self.process_msg(msg)

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

    def get_telemetry_payload(self):
        try:
            data = json.loads(self.buffer.decode('UTF-8'))
            data = Telemetry(**data)
            payload = Payload(data=data, type=PayloadType.telemetry)
            return payload
        except json.JSONDecodeError:
            return None
        except pydantic.ValidationError:
            return None

    def process_msg(self, msg: Payload):
        if msg.type == PayloadType.config:
            self.config = msg.data
            self.restart_serial()
            print('restarted')
