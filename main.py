import asyncio
import traceback

from app.app import ConnectorApp
from app.config.config import Config
from app.replacement.logs import setup_logger


def main():
    config = Config()
    logger = setup_logger("main", config)
    app = ConnectorApp(config)
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass
    except asyncio.CancelledError:
        pass
    except Exception as e:
        traceback.print_exc()
        logger.info(str(e))
    logger.info("Shutting down")


if __name__ == '__main__':
    main()
