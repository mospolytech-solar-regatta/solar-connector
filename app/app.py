from app.config.config import Config
from app.remote.config import Config as RemoteCfg
from app.remote.models import Payload
from app.remote.remote import Remote
from app.wire.wire import WireConnection
from app.wire.config import Config as WireCfg


class ConnectorApp:

    def __init__(self, config: Config):
        self.config = config
        self.remote_config = RemoteCfg(dsn=config.redis_dsn, config_channel=config.redis_config_channel,
                                       telemetry_channel=config.redis_telemetry_channel,
                                       config_apply_channel=config.redis_config_apply_channel)

        self.wire_config = WireCfg(port=config.serial_port, baudrate=config.serial_baudrate,
                                   parity=config.serial_parity, bytesize=config.serial_bytesize,
                                   timeout=config.serial_timeout, stopbits=config.serial_stopbits)
        self.remote = Remote(self.remote_config)
        self.wire = WireConnection(self.wire_config)
        self.payloads = []

    def run(self):
        self.remote.subscribe()
        while True:
            self.step()
            self.process_payloads()

    def step(self):
        self.add_payloads(self.remote.step(), self.wire.step())

    def process_payloads(self):
        wire_payloads = self.get_wire_payloads()
        remote_payloads = self.get_remote_payloads()
        self.payloads.clear()

        res = self.wire.process_payloads(*wire_payloads)
        if res is not None:
            self.add_payloads(*res)
        res = self.remote.process_payloads(*remote_payloads)
        if res is not None:
            self.add_payloads(*res)

    def add_payloads(self, *payloads):
        for i in payloads:
            if i is not None:
                self.payloads.append(i)

    def get_remote_payloads(self):
        res = []
        for i in self.payloads:
            i: Payload
            if i.type in self.remote.allowed_payload_types:
                res.append(i)
        return res

    def get_wire_payloads(self):
        res = []
        for i in self.payloads:
            i: Payload
            if i.type in self.wire.allowed_payload_types:
                res.append(i)
        return res
