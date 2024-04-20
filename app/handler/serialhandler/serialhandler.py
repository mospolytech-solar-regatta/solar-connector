import datetime
import json
from logging import Logger
from typing import Optional

import pydantic

from app.controller.telemetrycontroller.models import Telemetry
from app.errors import SerialReadError
from .. import BaseHandler
from ...client import ConnectionProvider
from ...controller.telemetrycontroller.telemetrycontroller import TelemetryController


class SerialHandler(BaseHandler):
    module_name = "wire"
    config_propagate_interval = datetime.timedelta(seconds=30)
    PAYLOAD_REQUEST = "Waiting for a new Payload"
    PAYLOAD_RECEIVED = "Got a new Payload"

    def __init__(self, logger: Logger, conn_provider: ConnectionProvider, telemetry_controller: TelemetryController):
        super().__init__(logger)
        self.conn_provider = conn_provider
        self.telemetry_controller = telemetry_controller

    async def step(self):
        await self.process_serial()

    async def process_serial(self):
        async with self.conn_provider as conn:
            try:
                data = await conn.read()
                if data:
                    # signal_processed = await self.process_signals(data)
                    # if signal_processed:
                    #     return

                    telemetry = await self.get_telemetry_payload(data)
                    if telemetry is not None:
                        await self.telemetry_controller.send_telemetry(telemetry)
            except SerialReadError as err:
                self.logger.error(err)

    async def get_telemetry_payload(self, data: str) -> Optional[Telemetry]:
        try:
            data = json.loads(data)
            # TODO: fix created_at validation
            self.logger.debug(f'telemetry payload {data}')
            data['created_at'] = datetime.datetime.now().isoformat()
            data = Telemetry.parse_obj(data)
            return data
        except json.JSONDecodeError as err:
            self.logger.error(err)
        except pydantic.ValidationError as err:
            self.logger.error(err)

    async def init(self):
        async with self.conn_provider as conn:
            res = await conn.check_serial()
            if not res:
                self.logger.warning("Serial not available")

    # async def process_signals(self, data: str) -> bool:  # TODO: think about it
    #     if data == self.PAYLOAD_REQUEST:
    #         await self.telemetry_controller.set_controller_status(ControllerStatus.waiting_for_payload)
    #         return True
    #     if data == self.PAYLOAD_RECEIVED:
    #         await self.telemetry_controller.set_controller_status(ControllerStatus.controller_sending)
    #         return True
    #     return False
