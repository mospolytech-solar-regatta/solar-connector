import logging

from app.remote.config import Config
from app.replacement.redis_logging_handler import RedisHandler


def setup_logging(name: str, cfg: Config):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    rh = RedisHandler(cfg)
    rh.setLevel(logging.DEBUG)
    logger.addHandler(rh)
    return logger
