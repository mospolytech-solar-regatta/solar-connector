from pydantic import BaseSettings, RedisDsn


class Config(BaseSettings):
    dsn: RedisDsn
    config_channel: str
    telemetry_channel: str
    config_apply_channel: str
    status_update_channel: str
