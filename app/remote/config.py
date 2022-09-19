from pydantic import BaseSettings, RedisDsn


class Config(BaseSettings):
    dsn: RedisDsn
    config_channel: str
    telemetry_channel: str
