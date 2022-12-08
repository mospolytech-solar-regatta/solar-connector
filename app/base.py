import asyncio
import logging
from asyncio import Queue, QueueFull

import app.replacement.logs as logs
from app.remote.config import Config


class BaseModule:
    module_name = "base"

    def __init__(self, remoteCfg: Config):
        self.running = True
        self.remoteCfg = remoteCfg
        self.setup_logger()
        self.logger = self.get_logger()
        self.logger.info("module initialized")

    async def step(self) -> None:
        pass

    async def run(self) -> None:
        while self.running:
            await self.step()
            await asyncio.sleep(0.001)

    def setup_logger(self):
        logs.setup_logging(self.module_name, self.remoteCfg)

    def get_logger(self):
        return logging.getLogger(self.module_name)

    def put_in_queue(self, payload: any, q: Queue):
        try:
            q.put_nowait(payload)
        except QueueFull as err:
            self.logger.error(err)
