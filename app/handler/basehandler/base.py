import asyncio
import logging


class BaseHandler:
    handler_name = "base"

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.logger.info("module initialized")

    async def init(self):
        pass

    async def step(self) -> None:
        pass

    async def run(self) -> None:
        await self.step()
        await asyncio.sleep(0.001)