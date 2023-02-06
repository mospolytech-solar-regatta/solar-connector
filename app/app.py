import asyncio
import datetime
from asyncio import Queue

from app.config.config import Config
from app.logic.logic import AppLogic
from app.payloads import PayloadType
from app.remote.config import Config as RemoteCfg
from app.remote.remote import Remote
from app.status import AppStatus
from app.wire.config import Config as WireCfg
from app.wire.wire import WireConnection


class ConnectorApp:
    allowed_payload_types = [PayloadType.status_update]

    def __init__(self, config: Config):
        self.config = config
        self.status = AppStatus.Starting
        self.status_time = datetime.datetime.now()
        self.remote_config = RemoteCfg()
        self.wire_config = WireCfg()
        self.logic_queue = Queue()
        self.wire_queue = Queue()
        self.remote_queue = Queue()
        self.logic = AppLogic(self.remote_config, self.logic_queue, self.wire_queue, self.remote_queue)
        self.remote = Remote(self.remote_config, self.remote_queue, self.logic_queue)
        self.wire = WireConnection(self.wire_config, self.remote_config, self.logic_queue, self.wire_queue)
        self.modules = []
        self.init_modules()

    def init_modules(self):
        self.modules.append(self.remote)
        self.modules.append(self.wire)
        self.modules.append(self.logic)

    async def run(self):
        self.remote.subscribe()
        futures = []
        for f in self.modules:
            futures.append(asyncio.create_task(f.run()))

        await asyncio.gather(*futures)
