import json
import queue
from typing import Optional, List

import pydantic
import redis

from app.remote.config import Config
from app.remote.models import Telemetry, Payload, PayloadType
from app.wire.config import Config as SerialConfig


class Remote:
    allowed_payload_types = [PayloadType.telemetry, PayloadType.config_update]

    def __init__(self, config: Config):
        self.redis = redis.Redis().from_url(config.dsn)
        self.pubsub = self.redis.pubsub()
        self.config_channel = config.config_channel
        self.telemetry_channel = config.telemetry_channel
        self.config_apply_channel = config.config_apply_channel
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

    def step(self) -> Optional[List[Payload]]:
        self.pubsub.get_message()
        try:
            w = self.__wire_payloads.get(block=False)
            return w  # TODO: add multiple return
        except queue.Empty:
            pass

    def __process_payload(self, payload: Payload):
        if payload is not None:
            self.publish(payload)

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
