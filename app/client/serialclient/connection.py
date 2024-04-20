import asyncio
import json
from logging import Logger
from typing import Optional

import aioserial
import serial.tools.list_ports

from app.errors import SerialReadError, SerialWriteError
from .config import SerialConfig


class Connection:
    tmp_config_filename = 'tmp/serial_config'

    def __init__(self, logger: Logger, config: SerialConfig):
        self.config = config
        self.logger = logger
        self.config = self.discovery_config()
        self.serial = self.create_serial()
        self.__buffer = b""

    def create_serial(self, cfg=None) -> Optional[aioserial.AioSerial]:
        if cfg is None:
            cfg = self.config
        try:
            return aioserial.AioSerial(port=cfg.port, budrate=cfg.baudrate, timeout=cfg.timeout,
                                       parity=cfg.parity, rtscts=True, stopbits=cfg.stopbits,
                                       bytesize=cfg.bytesize)
        except:
            return None

    def discovery_config(self):
        # if file config correct use file config
        cfg = self.get_tmp_config()
        if cfg is not None:
            ser = self.create_serial(cfg)
            if ser is not None and ser.is_open:
                ser.close()
                return cfg

        # else try to discover port
        portname = self.discover_port()
        if portname is not None:
            self.config.port = portname
        return self.config

    def discover_port(self):
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if "Arduino" in p.description:
                return p.name

    def get_tmp_config(self) -> Optional[SerialConfig]:
        try:
            with open(self.tmp_config_filename) as f:
                res = f.read()
                return SerialConfig(**json.loads(res))
        except:
            pass

    def save_tmp_config(self):
        try:
            with open(self.tmp_config_filename, 'w') as f:
                f.write(self.config.json())
        except:
            pass

    def restart_serial(self):
        if self.serial.is_open:
            self.serial.close()
        self.serial = self.create_serial()
        if self.serial is None:
            return

        try:
            if not self.serial.is_open:
                self.serial.open()
        except serial.SerialException as ex:
            self.logger.info(str(ex))

    async def read(self) -> Optional[str]:
        await self.validate_and_fix_config()
        if not await self.__check_serial():
            raise SerialReadError()

        data: bytes = await self.serial.readline_async()
        if data:
            is_newline = data.find(b'\n')
            if is_newline != -1:
                await self.append_buffer(data[:is_newline])
                return str(self.pop_buffer())

            await self.append_buffer(data)

    async def send(self, data: str) -> None:
        data = data.strip()
        await self.validate_and_fix_config()
        if not await self.__check_serial():
            raise SerialWriteError()
        await self.serial.writelines_async([data.encode('UTF-8')])

    async def validate_and_fix_config(self):
        if not await self.__check_serial():
            self.logger.warning("Serial not reachable, sleeping for 5 sec")
            await asyncio.sleep(5)
            await self.update_config(self.discovery_config())

    async def check_serial(self) -> bool:
        return await self.__check_serial(self.serial)

    async def __check_serial(self, ser=None) -> bool:
        if ser is None:
            ser = self.serial

        if ser is None:
            return False
        return ser.is_open

    async def update_config(self, new_cfg: SerialConfig):
        self.config = new_cfg
        self.save_tmp_config()
        self.restart_serial()

    async def pop_buffer(self):
        result = self.__buffer[:]
        self.__buffer = b""
        return result

    async def append_buffer(self, data: bytes):
        self.__buffer += data
