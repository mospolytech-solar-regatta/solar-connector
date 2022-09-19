from app.config.config import Config
from app.remote.config import Config as RemoteCfg
from app.remote.remote import Remote
from app.wire.wire import WireConnection
from app.wire.config import Config as WireCfg


class ConnectorApp:

    def __init__(self, config: Config):
        self.config = config
        self.remote_config = RemoteCfg(dsn=config.redis_dsn, config_channel=config.redis_config_channel,
                                       telemetry_channel=config.redis_telemetry_channel)

        self.wire_config = WireCfg(port=config.serial_port, baudrate=config.serial_baudrate,
                                   parity=config.serial_parity, bytesize=config.serial_bytesize,
                                   timeout=config.serial_timeout, stopbits=config.serial_stopbits)
        self.remote = Remote(self.remote_config)
        self.wire = WireConnection(self.wire_config)

    def run(self):
        self.remote.subscribe()
        self.wire.run(self.remote.iteration)
