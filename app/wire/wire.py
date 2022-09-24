import datetime
import json
import traceback
from typing import Optional, List

import pydantic

from app.status import AppStatus
from app.wire.connection import Connection
from app.remote.models import Telemetry
from app.payloads import PayloadType, Payload, ConfigUpdated, UpdateStatus, LogPayload
from app.wire.config import Config
from app.errors import SerialReadError


class WireConnection:
    allowed_payload_types = [PayloadType.config]

    def __init__(self, config: Config):
        self.conn = Connection(config)

    def step(self):
        return self.read()

    def read(self) -> List[Payload]:
        payloads = []
        try:
            data = self.conn.read()
            if data:
                payloads.append(self.get_telemetry_payload(data))
        except SerialReadError:
            payloads.append(self.get_new_status_payload(AppStatus.Failing))
        payloads.append(self.get_config_update_payload())
        return payloads

    def get_telemetry_payload(self, data) -> Optional[Payload]:
        try:
            data = json.loads(data)
            data = Telemetry(**data)
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

    def get_config_update_payload(self) -> Optional[Payload]:
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
