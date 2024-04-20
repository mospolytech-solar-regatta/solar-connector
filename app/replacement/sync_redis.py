import redis

from app.config.config import Config


class SyncRedis:
    def __init__(self, cfg: Config):
        self.pool = redis.ConnectionPool.from_url(str(cfg.redis_dsn))

    def get_pool(self):
        return self.pool

    def get_redis(self):
        return redis.Redis(connection_pool=self.pool)
