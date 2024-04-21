import json
import logging

import pydantic
from redis.asyncio import Redis

from app.client.serialclient import SerialConfig
from .. import BaseHandler
from ...config.config import Config
from ...controller.configcontroller.configcontroller import ConfigController
from ...controller.landcontroller.landcontroller import LandController
from ...controller.telemetrycontroller.models import LandData


class RedisHandler(BaseHandler):
    def __init__(
            self,
            logger: logging.Logger,
            config_controller: ConfigController,
            land_controller: LandController,
            redis: Redis,
            config: Config):
        super().__init__(logger)
        self.config_controller = config_controller
        self.land_controller = land_controller
        self.redis = redis
        self.pubsub = self.redis.pubsub()
        self.config_channel = config.redis_config_channel
        self.land_queue_channel = config.redis_land_queue_channel
        self.telemetry_channel = config.redis_telemetry_channel
        self.config_apply_channel = config.redis_config_apply_channel
        self.status_update_channel = config.redis_status_update_channel

    async def subscribe(self):
        try:
            await self.pubsub.subscribe(**{
                self.config_channel: self.config_handler,
                self.land_queue_channel: self.land_data_handler,
            })
        except Exception as ex:
            self.logger.error(str(ex))

    async def config_handler(self, message: dict):
        try:
            data = json.loads(message['data'].decode('UTF-8'))
            config = SerialConfig(**data)
            await self.config_controller.update_config(config)
        except json.JSONDecodeError as err:
            self.logger.error(err)
        except pydantic.ValidationError as err:
            self.logger.error(err)

    async def land_data_handler(self, message: dict):
        try:
            data = json.loads(message['data'].decode('UTF-8'))
            land_data = LandData(**data)
            await self.land_controller.process_land_payload(land_data)
        except json.JSONDecodeError as err:
            self.logger.error(err)
        except pydantic.ValidationError as err:
            self.logger.error(err)

    async def step(self) -> None:
        await self.pubsub.get_message()

    async def init(self):
        await self.subscribe()
