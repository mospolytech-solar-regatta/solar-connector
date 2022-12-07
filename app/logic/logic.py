from asyncio import Queue, QueueEmpty, QueueFull

from app.base import BaseModule
from app.payloads import Payload, PayloadType
from app.remote.config import Config as RemoteConfig


class AppLogic(BaseModule):
    module_name = "logic"

    def __init__(self, remoteCfg: RemoteConfig, q: Queue):
        super().__init__(remoteCfg)
        self.queue = q

    async def step(self) -> None:
        try:
            payload = self.queue.get_nowait()
        except QueueEmpty:
            return
        self.logger.debug(f'received payload: {payload}')
        payload: Payload
        self.handle_payload(payload)

    def handle_payload(self, payload: Payload):
        if payload.type == PayloadType.telemetry:
            pass
