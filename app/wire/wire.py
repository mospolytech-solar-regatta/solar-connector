import datetime
import json
from asyncio import Queue, QueueEmpty
from typing import Optional

import pydantic

from app.base import BaseModule
from app.errors import SerialReadError
from app.payloads import PayloadType, Payload, ConfigUpdated
from app.remote.config import Config as RemoteConfig
from app.remote.models import Telemetry, LandData
from app.wire.config import Config
from app.wire.connection import Connection
from .models import ControllerStatus


class WireConnection(BaseModule):
    module_name = "wire"
    config_propagate_interval = datetime.timedelta(seconds=30)
    PAYLOAD_REQUEST = "Waiting for a new Payload"
    PAYLOAD_RECEIVED = "Got a new Payload"

    def __init__(self, config: Config, remote_cfg: RemoteConfig, logic_queue: Queue, q: Queue):
        super().__init__(remote_cfg)
        self.outbound = logic_queue
        self.inbound = q
        self.controller_status = ControllerStatus.waiting_for_payload
        self.land_low_prior_queue = None
        self.conn = Connection(config, self.logger)
        self.last_config_propagate = datetime.datetime.now() - self.config_propagate_interval

    async def step(self):
        self.process_payloads()
        self.process_serial()
        self.process_config_propagate()
        self.send_serial()

    def send_serial(self):
        if self.land_low_prior_queue is not None and self.controller_status.waiting_for_payload:
            data = self.land_low_prior_queue.json()
            self.conn.send(data)
            self.land_low_prior_queue = None
            self.controller_status = ControllerStatus.connector_sent

    def process_serial(self):
        try:
            data = self.conn.read()
            if data:
                signal_processed = self.process_signals(data)
                if signal_processed:
                    return
                p = self.get_telemetry_payload(data)
                if p is not None:
                    self.put_in_queue(p, self.outbound)
        except SerialReadError as err:
            self.logger.error(err)

    def process_signals(self, data: str) -> bool:
        if data == self.PAYLOAD_REQUEST:
            self.controller_status = ControllerStatus.waiting_for_payload
            return True
        if data == self.PAYLOAD_RECEIVED:
            self.controller_status = ControllerStatus.controller_sending
            return True
        return False

    def process_config_propagate(self):
        if datetime.datetime.now() - self.last_config_propagate < self.config_propagate_interval:
            return

        self.last_config_propagate = datetime.datetime.now()
        self.propagate_config()

    def propagate_config(self):
        p = self.get_config_update_payload()
        self.put_in_queue(p, self.outbound)

    def get_telemetry_payload(self, data: str) -> Optional[Payload]:
        try:
            data = json.loads(data)
            # TODO: fix created_at validation
            self.logger.debug(f'telemetry payload {data}')
            data['created_at'] = datetime.datetime.now().isoformat()
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

    def process_land_payload(self, land_data: LandData):
        if land_data.priority == LandData.Priority.low:
            self.land_low_prior_queue = land_data
        else:
            raise NotImplementedError("High priority not implemented")

    def handle_payload(self, msg: Payload):
        if msg.type == PayloadType.config:
            self.conn.update_config(msg.data)
            self.propagate_config()
        elif msg.type == PayloadType.land_data:
            self.process_land_payload(msg.data)

    def process_payloads(self) -> None:
        while True:
            try:
                payload = self.inbound.get_nowait()
            except QueueEmpty:
                return
            self.logger.debug(f'received payload: {payload}')
            payload: Payload
            self.handle_payload(payload)
