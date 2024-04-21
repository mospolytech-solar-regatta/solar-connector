from datetime import datetime, timedelta
from logging import Logger

from redis.asyncio import Redis

from app.client import ConnectionProvider
from app.client.serialclient import SerialConfig
from app.config.config import Config
from app.payloads import ConfigUpdated


class ConfigController:
    config_propagate_interval = timedelta(seconds=30)

    def __init__(self,
                 logger: Logger,
                 connection_provider: ConnectionProvider,
                 redis: Redis,
                 config: Config,
                 ):
        self.logger = logger
        self.redis = redis
        self.config_apply_channel = config.redis_config_apply_channel
        self.pubsub = redis.pubsub()
        self.conn_provider = connection_provider
        self.last_config_propagate = datetime.now() - self.config_propagate_interval

    async def process_config_propagate(self):
        if datetime.now() - self.last_config_propagate < self.config_propagate_interval:
            return

        self.last_config_propagate = datetime.now()
        await self.propagate_config()

    async def propagate_config(self):
        cfg = await self.get_config_update_payload()
        await self.redis.publish(self.config_apply_channel, cfg.json())

    async def update_config(self, config: SerialConfig):
        async with self.conn_provider as conn:
            conn.update_config(config)
        await self.propagate_config()

    async def get_config_update_payload(self) -> ConfigUpdated:
        async with self.conn_provider as conn:
            config_update = ConfigUpdated(timestamp=datetime.now(), config=conn.config)
            return config_update
