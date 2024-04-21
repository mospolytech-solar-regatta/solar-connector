import asyncio
import datetime

from redis.asyncio import Redis

from app.client import ConnectionProvider, Connection
from app.client.serialclient import SerialConfig
from app.config.config import Config
from app.controller.configcontroller.configcontroller import ConfigController
from app.controller.landcontroller.landcontroller import LandController
from app.controller.telemetrycontroller.telemetrycontroller import TelemetryController
from app.handler import SerialHandler, RedisHandler
from app.payloads import PayloadType
from app.replacement.logs import setup_logger
from app.status import AppStatus


class ConnectorApp:
    allowed_payload_types = [PayloadType.status_update]

    def __init__(self, config: Config):
        self.config = config
        self.status = AppStatus.Starting
        self.status_time = datetime.datetime.now()

        self.connection = Connection(
            setup_logger("connection", config),
            SerialConfig(),
        )
        self.connection_provider = ConnectionProvider(
            self.connection
        )
        self.redis = Redis().from_url(str(config.redis_dsn))

        self.config_controller = ConfigController(
            setup_logger("config_controller", config),
            self.connection_provider,
            self.redis,
            self.config,
        )
        self.land_controller = LandController(
            setup_logger("land_controller", config),
            self.connection_provider,
        )
        self.telemetry_controller = TelemetryController(
            setup_logger("telemetry_controller", config),
            self.redis,
            self.config,
        )

        self.redis_handler = RedisHandler(
            setup_logger("redis_handler", config),
            self.config_controller,
            self.land_controller,
            self.redis,
            self.config,
        )
        self.serial_handler = SerialHandler(
            setup_logger("serial_handler", config),
            self.connection_provider,
            self.telemetry_controller,
        )

        self.handlers = [
            self.serial_handler,
            self.redis_handler,
        ]

    async def run(self):
        for f in self.handlers:
            await f.init()

        futures = []
        for f in self.handlers:
            futures.append(asyncio.create_task(f.run()))

        await asyncio.gather(*futures, return_exceptions=True)
