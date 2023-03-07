from pydantic import BaseSettings, RedisDsn


class Config(BaseSettings):
    dsn: RedisDsn
    config_channel: str = 'serial_config'
    telemetry_channel: str = 'telemetry'
    config_apply_channel: str = 'serial_config_apply'
    status_update_channel: str = 'status_update'
    land_queue_channel: str = 'land_queue_channel'
    log_channel: str = 'connector_log'

    class Config:
        env_file = '.env'
        env_prefix = 'redis_'
