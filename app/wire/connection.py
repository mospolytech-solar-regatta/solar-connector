import json
from typing import Optional

import serial

from app.errors import SerialReadError
from app.wire.config import Config


class Connection:
    tmp_config_filename = 'tmp/serial_config'

    def __init__(self, config: Config):
        self.config = config
        self.config = self.discovery_config()
        self.serial = self.create_serial()
        self.__buffer = b""

    def create_serial(self, cfg=None):
        if cfg is None:
            cfg = self.config
        try:
            return serial.Serial(cfg.port, cfg.baudrate, timeout=cfg.timeout,
                                 parity=cfg.parity, rtscts=1, stopbits=cfg.stopbits,
                                 bytesize=cfg.bytesize)
        except:
            return serial.Serial()

    def discovery_config(self):
        cfg = self.get_tmp_config()
        if cfg is not None:
            ser = self.create_serial(cfg)
            if ser.is_open:
                ser.close()
                return cfg
        portname = self.discover_port()
        if portname is not None:
            self.config.port = portname
            return self.config
        return self.config

    def discover_port(self):
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if "Arduino" in p.description:
                return p.name

    def get_tmp_config(self) -> Optional[Config]:
        try:
            with open(self.tmp_config_filename) as f:
                res = f.read()
                return Config(**json.loads(res))
        except:
            pass

    def save_tmp_config(self):
        try:
            with open(self.tmp_config_filename, 'w') as f:
                f.write(self.config.json())
        except:
            pass

    def restart_serial(self):
        print('reopen')
        if self.serial.is_open:
            self.serial.close()
        self.serial = self.create_serial()

        try:
            if not self.serial.is_open:
                self.serial.open()
        except serial.SerialException:
            pass

    def read(self) -> Optional[str]:
        result = None
        self.validate_and_fix_config()
        if not self.check_serial():
            raise SerialReadError()
        data: bytes = self.serial.readline()
        if data:
            is_newline = data.find(b'\n')
            if is_newline != -1:
                self.append_buffer(data[:is_newline])
                result = self.pop_buffer()
            else:
                self.append_buffer(data)
        return result

    def validate_and_fix_config(self):
        if not self.check_serial():
            self.update_config(self.discovery_config())

    def check_serial(self, ser=None) -> bool:
        if ser is None:
            ser = self.serial
        # if not ser.is_open:
        #     ser.open()
        return ser.is_open

    def update_config(self, new_cfg: Config):
        self.config = new_cfg
        self.save_tmp_config()
        self.restart_serial()

    def pop_buffer(self):
        result = self.__buffer[:]
        self.__buffer = b""
        return result

    def append_buffer(self, data: bytes):
        self.__buffer += data
