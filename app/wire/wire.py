import datetime
import json
from asyncio import Queue, QueueEmpty
from typing import Optional

import pydantic

from app.base import BaseModule
from app.errors import SerialReadError
from app.payloads import PayloadType, Payload, ConfigUpdated
from app.remote.config import Config as RemoteConfig
from app.remote.models import Telemetry
from app.wire.config import Config
from app.wire.connection import Connection


class WireConnection(BaseModule):
    module_name = "wire"
    config_propagate_interval = datetime.timedelta(seconds=30)

    def __init__(self, config: Config, remoteCfg: RemoteConfig, logic_queue: Queue, q: Queue):
        super().__init__(remoteCfg)
        self.outbound = logic_queue
        self.inbound = q
        self.conn = Connection(config)
        self.last_config_propagate = datetime.datetime.now() - self.config_propagate_interval

    async def step(self):
        self.process_payloads()
        self.process_serial()
        self.process_config_propagate()

    def process_serial(self):
        try:
            data = self.conn.read()
            if data:
                p = self.get_telemetry_payload(data)
                self.put_in_queue(p, self.outbound)
        except SerialReadError as err:
            self.logger.error(err)

    def process_config_propagate(self):
        if datetime.datetime.now() - self.last_config_propagate < self.config_propagate_interval:
            return

        self.last_config_propagate = datetime.datetime.now()
        self.propagate_config()

    def propagate_config(self):
        p = self.get_config_update_payload()
        self.put_in_queue(p, self.outbound)

    def get_telemetry_payload(self, data) -> Optional[Payload]:
        try:
            data = json.loads(data)
            data = Telemetry.parse_obj(data)
            payload = Payload(data=data, type=PayloadType.telemetry)
            return payload
        except json.JSONDecodeError as err:
            self.logger.error(err)
        except pydantic.ValidationError as err:
            self.logger.error(err)

    def get_config_update_payload(self) -> Payload:
        config_update = ConfigUpdated(timestamp=datetime.datetime.now(), config=self.conn.config)
        payload = Payload(type=PayloadType.config_update, data=config_update)
        return payload

    def handle_payload(self, msg: Payload):
        if msg.type == PayloadType.config:
            self.conn.update_config(msg.data)
            self.propagate_config()

    def process_payloads(self) -> None:
        while True:
            try:
                payload = self.inbound.get_nowait()
            except QueueEmpty:
                return
            self.logger.debug(f'received payload: {payload}')
            payload: Payload
            self.handle_payload(payload)
