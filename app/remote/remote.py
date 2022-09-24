import json
import queue
from typing import Optional, List

import pydantic
import redis

from app.remote.config import Config
from app.remote.models import Telemetry
from app.payloads import Payload, PayloadType
from app.wire.config import Config as SerialConfig


class Remote:
    allowed_payload_types = [PayloadType.telemetry, PayloadType.log, PayloadType.config_update,
                             PayloadType.status_update]

    def __init__(self, config: Config):
        self.redis = redis.Redis().from_url(config.dsn)
        self.pubsub = self.redis.pubsub()
        self.config_channel = config.config_channel
        self.telemetry_channel = config.telemetry_channel
        self.config_apply_channel = config.config_apply_channel
        self.status_update_channel = config.status_update_channel
        self.log_channel = config.log_channel
        self.__wire_payloads = queue.Queue()

    def subscribe(self):
        self.pubsub.subscribe(**{self.config_channel: self.config_handler})

    def config_handler(self, message):
        try:
            data = json.loads(message['data'].decode('UTF-8'))
            data = SerialConfig(**data)
            payload = Payload(type=PayloadType.config, data=data)
            self.__wire_payloads.put(payload)
        except json.JSONDecodeError:
            return None
        except pydantic.ValidationError:
            return None

    def step(self) -> List[Payload]:
        self.pubsub.get_message()
        return self.get_wire_queue()

    def __process_payload(self, payload: Payload):
        if payload is not None:
            self.publish(payload)

    def get_wire_queue(self) -> List[Payload]:
        res = []
        while not self.__wire_payloads.empty():
            try:
                res.append(self.__wire_payloads.get_nowait())
            except queue.Empty:
                break
        return res

    def process_payloads(self, *payloads):
        res = []
        for i in payloads:
            res.append(self.__process_payload(i))
        return res

    def publish(self, payload: Payload):
        if payload.type == PayloadType.telemetry:
            self.redis.publish(self.telemetry_channel, payload.data.json())
        if payload.type == PayloadType.config_update:
            self.redis.publish(self.config_apply_channel, payload.data.json())
        if payload.type == PayloadType.status_update:
            self.redis.publish(self.status_update_channel, payload.data.json())
        if payload.type == PayloadType.log:
            self.redis.publish(self.log_channel, payload.data.data)

