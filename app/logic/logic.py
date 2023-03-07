from asyncio import Queue, QueueEmpty

from app.base import BaseModule
from app.payloads import Payload, PayloadType
from app.remote.config import Config as RemoteConfig


class AppLogic(BaseModule):
    module_name = "logic"

    def __init__(self, remoteCfg: RemoteConfig, q: Queue, wire: Queue, remote: Queue):
        super().__init__(remoteCfg)
        self.queue = q
        self.wire = wire
        self.remote = remote

    async def step(self) -> None:
        while True:
            try:
                payload = self.queue.get_nowait()
            except QueueEmpty:
                return
            self.logger.debug(f'received payload: {payload}')
            payload: Payload
            self.handle_payload(payload)

    def handle_payload(self, payload: Payload):
        if payload is None:
            return
        if payload.type in [PayloadType.telemetry, PayloadType.config_update]:
            self.put_in_queue(payload, self.remote)
        if payload.type in [PayloadType.config, PayloadType.land_data]:
            self.put_in_queue(payload, self.wire)
