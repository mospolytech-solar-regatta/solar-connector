from asyncio import Lock

from .. import Connection


class ConnectionProvider:
    def __init__(self, conn: Connection):
        self.mutex = Lock()
        self.conn = conn

    async def __aenter__(self):
        await self.mutex.acquire()
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.mutex.release()
