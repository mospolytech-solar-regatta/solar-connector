import asyncio
import datetime
import json
import traceback
from asyncio import Queue, QueueFull
from typing import Optional, List

import pydantic

from app.base import BaseModule
from app.status import AppStatus
from app.wire.connection import Connection
from app.remote.models import Telemetry
from app.payloads import PayloadType, Payload, ConfigUpdated, UpdateStatus, LogPayload
from app.wire.config import Config
from app.remote.config import Config as RemoteConfig
from app.errors import SerialReadError


class WireConnection(BaseModule):
    module_name = "wire"
    allowed_payload_types = [PayloadType.config]

    def __init__(self, config: Config, remoteCfg: RemoteConfig, logic_queue: Queue):
        super().__init__(remoteCfg)
        self.outbound = logic_queue
        self.conn = Connection(config)
        self.running = True

    async def step(self):
        try:
            data = self.conn.read()
            if data:
                p = self.get_telemetry_payload(data)
                if p is not None:
                    self.outbound.put_nowait(p)
            self.outbound.put_nowait(self.get_config_update_payload())
        except SerialReadError as err:
            self.logger.error(err)
        except QueueFull as err:
            self.logger.error(err)

    def get_telemetry_payload(self, data) -> Optional[Payload]:
        try:
            data = json.loads(data)
            data = Telemetry.parse_obj(data)
            payload = Payload(data=data, type=PayloadType.telemetry)
            return payload
        except json.JSONDecodeError:
            return self.get_log_payload(traceback.format_exc())
        except pydantic.ValidationError:
            return self.get_log_payload(traceback.format_exc())

    def get_log_payload(self, log: str):
        log = str(log)
        log = LogPayload(timestamp=datetime.datetime.now(), data=log)
        return Payload(type=PayloadType.log, data=log)

    def get_new_status_payload(self, new_status: AppStatus):
        status_update = UpdateStatus(timestamp=datetime.datetime.now(), status=new_status)
        return Payload(type=PayloadType.status_update, data=status_update)

    def get_config_update_payload(self) -> Payload:
        config_update = ConfigUpdated(timestamp=datetime.datetime.now(), config=self.conn.config)
        payload = Payload(type=PayloadType.config_update, data=config_update)
        return payload

    def __process_payload(self, msg: Payload):
        if msg.type == PayloadType.config:
            self.conn.update_config(msg.data)
            return self.get_config_update_payload()

    def process_payloads(self, *payloads) -> List[Payload]:
        res = []
        for i in payloads:
            pay = self.__process_payload(i)
            if pay is not None:
                res.append(pay)
        return res
