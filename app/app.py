import datetime
from typing import List, Optional

from app.config.config import Config
from app.remote.config import Config as RemoteCfg
from app.payloads import Payload, PayloadType, UpdateStatus
from app.remote.remote import Remote
from app.wire.wire import WireConnection
from app.wire.config import Config as WireCfg
from app.status import AppStatus


class ConnectorApp:
    allowed_payload_types = [PayloadType.status_update]

    def __init__(self, config: Config):
        self.config = config
        self.status = AppStatus.Starting
        self.status_time = datetime.datetime.now()
        self.remote_config = RemoteCfg(dsn=config.redis_dsn, config_channel=config.redis_config_channel,
                                       telemetry_channel=config.redis_telemetry_channel,
                                       config_apply_channel=config.redis_config_apply_channel,
                                       status_update_channel=config.redis_status_update_channel,
                                       log_channel=config.redis_log_channel)

        self.wire_config = WireCfg(port=config.serial_port, baudrate=config.serial_baudrate,
                                   parity=config.serial_parity, bytesize=config.serial_bytesize,
                                   timeout=config.serial_timeout, stopbits=config.serial_stopbits)

        self.remote = Remote(self.remote_config)
        self.wire = WireConnection(self.wire_config)
        self.payloads = []

    def run(self):
        self.remote.subscribe()
        while True:
            self.step()
            self.process_payloads()

    def step(self):
        self.add_payloads(*self.remote.step(), *self.wire.step())

    def process_status_update(self, new_status: UpdateStatus):
        self.status = new_status.status
        self.status_time = new_status.timestamp

    def __process_payload(self, payload: Payload) -> Optional[Payload]:
        if payload.type == PayloadType.status_update:
            self.process_status_update(payload.data)
        return None

    def process_app_payloads(self, *payloads: Payload):
        res = []
        for i in payloads:
            r = self.__process_payload(i)
            if r is not None:
                res.append(r)
        return res

    def process_payloads(self):
        wire_payloads = self.get_wire_payloads()
        remote_payloads = self.get_remote_payloads()
        app_payloads = self.get_app_payloads()
        self.payloads.clear()

        res = self.process_app_payloads(*app_payloads)
        self.add_payloads(*res)

        res = self.wire.process_payloads(*wire_payloads)
        self.add_payloads(*res)

        res = self.remote.process_payloads(*remote_payloads)
        self.add_payloads(*res)

    def add_payloads(self, *payloads):
        for i in payloads:
            if i is not None:
                self.payloads.append(i)

    def get_remote_payloads(self):
        res = []
        for i in self.payloads:
            i: Payload
            if i.type in self.remote.allowed_payload_types:
                res.append(i)
        return res

    def get_wire_payloads(self):
        res = []
        for i in self.payloads:
            i: Payload
            if i.type in self.wire.allowed_payload_types:
                res.append(i)
        return res

    def get_app_payloads(self):
        res = []
        for i in self.payloads:
            i: Payload
            if i.type in self.allowed_payload_types:
                res.append(i)
        return res
