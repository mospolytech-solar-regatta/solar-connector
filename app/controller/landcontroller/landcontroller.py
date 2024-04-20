from logging import Logger

from app.client import ConnectionProvider
from app.controller.telemetrycontroller.models import LandData


class LandController:
    def __init__(self, logger: Logger, conn_provider: ConnectionProvider):
        self.logger = logger
        self.conn_provider = conn_provider
        self.land_low_prior_queue = None

    async def process_land_payload(self, land_data: LandData):
        if land_data.priority == LandData.Priority.low:
            self.land_low_prior_queue = land_data
        else:
            raise NotImplementedError("High priority not implemented")

    async def send_serial(self):  # TODO: implement land low prior queue
        if self.land_low_prior_queue is not None:
            data = self.land_low_prior_queue.json()
            async with self.conn_provider as conn:
                await conn.send(data)

            self.land_low_prior_queue = None
