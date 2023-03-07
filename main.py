import asyncio
import traceback

from app.app import ConnectorApp
from app.config.config import Config


def main():
    config = Config()
    app = ConnectorApp(config)
    while True:
        try:
            asyncio.run(app.run())
        except KeyboardInterrupt:
            break
        except asyncio.CancelledError:
            break
        except Exception as e:
            traceback.print_exc()
            app.logic.logger.info(str(e))
    app.logic.logger.info("Shutting down")


if __name__ == '__main__':
    main()
