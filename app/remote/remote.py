import json
from asyncio import Queue, QueueFull, QueueEmpty

import pydantic
import redis

from app.base import BaseModule
from app.payloads import Payload, PayloadType
from app.remote.config import Config
from app.wire.config import Config as SerialConfig


class Remote(BaseModule):
    module_name = "remote"

    def __init__(self, config: Config, q: Queue, logic_queue: Queue):
        super().__init__(config)
        self.inbound = q
        self.outbound = logic_queue
        self.redis = redis.Redis().from_url(config.dsn)
        self.pubsub = self.redis.pubsub()
        self.config_channel = config.config_channel
        self.telemetry_channel = config.telemetry_channel
        self.config_apply_channel = config.config_apply_channel
        self.status_update_channel = config.status_update_channel
        self.log_channel = config.log_channel

    def subscribe(self):
        self.pubsub.subscribe(**{self.config_channel: self.config_handler})

    def config_handler(self, message):
        try:
            data = json.loads(message['data'].decode('UTF-8'))
            data = SerialConfig(**data)
            payload = Payload(type=PayloadType.config, data=data)
            self.outbound.put_nowait(payload)
        except json.JSONDecodeError as err:
            self.logger.error(err)
        except pydantic.ValidationError as err:
            self.logger.error(err)
        except QueueFull as err:
            self.logger.error(err)

    async def step(self) -> None:
        self.process_payloads()
        self.pubsub.get_message()

    def handle_payload(self, payload: Payload):
        if payload is not None:
            self.publish(payload)

    def process_payloads(self):
        while True:
            try:
                payload = self.inbound.get_nowait()
            except QueueEmpty:
                return
            self.logger.debug(f'received payload: {payload}')
            payload: Payload
            self.handle_payload(payload)

    def publish(self, payload: Payload):
        if payload.type == PayloadType.telemetry:
            self.redis.publish(self.telemetry_channel, payload.data.json())
        if payload.type == PayloadType.config_update:
            self.redis.publish(self.config_apply_channel, payload.data.json())
        if payload.type == PayloadType.status_update:
            self.redis.publish(self.status_update_channel, payload.data.json())
