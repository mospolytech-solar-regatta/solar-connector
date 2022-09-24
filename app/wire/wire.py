import datetime
import json
from typing import Optional, List

import pydantic
from app.wire.connection import Connection
from app.remote.models import Telemetry, PayloadType, Payload, ConfigUpdated
from app.wire.config import Config


class WireConnection:
    allowed_payload_types = [PayloadType.config]

    def __init__(self, config: Config):
        self.conn = Connection(config)

    def step(self):
        return self.read()

    def read(self) -> List[Payload]:
        payloads = []
        data = self.conn.read()
        if data:
            payloads.append(self.get_telemetry_payload(data))
        return payloads

    def get_telemetry_payload(self, data) -> Optional[Payload]:
        try:
            data = json.loads(data)
            data = Telemetry(**data)
            payload = Payload(data=data, type=PayloadType.telemetry)
            return payload
        except json.JSONDecodeError:
            return None
        except pydantic.ValidationError:
            return None

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
