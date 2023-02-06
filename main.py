import asyncio

from app.app import ConnectorApp
from app.config.config import Config


def main():
    config = Config()
    app = ConnectorApp(config)
    asyncio.run(app.run())


if __name__ == '__main__':
    main()
