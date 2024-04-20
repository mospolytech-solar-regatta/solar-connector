from logging import Logger

from redis.asyncio import Redis

from app.config.config import Config
from app.controller.telemetrycontroller.models import Telemetry


class TelemetryController:
    def __init__(self, logger: Logger, redis: Redis, config: Config):
        self.logger = logger
        self.redis = redis
        self.config = config

    async def send_telemetry(self, telemetry: Telemetry):
        await self.redis.publish(self.config.redis_telemetry_channel, telemetry.json())
