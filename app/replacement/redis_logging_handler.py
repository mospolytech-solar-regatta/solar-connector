from logging import StreamHandler, LogRecord
from app.remote.config import Config
from app.replacement.sync_redis import SyncRedis


class RedisHandler(StreamHandler):
    def __init__(self, cfg: Config) -> None:
        super().__init__()
        r = SyncRedis(cfg)
        self.redis = r.get_redis()
        self.channel = cfg.log_channel

    def emit(self, record: LogRecord) -> None:
        msg = self.format(record)
        self.redis.publish(self.channel, msg)
