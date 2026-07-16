import asyncio
import signal

from backend.consumers.runtime import (
    start_notification_consumer,
    stop_notification_consumer,
)
from backend.utils.log_manager import get_app_logger

logger = get_app_logger(__name__)


async def run_worker(shutdown_event: asyncio.Event | None = None) -> None:
    loop = asyncio.get_running_loop()
    if shutdown_event is None:
        shutdown_event = asyncio.Event()
        for shutdown_signal in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(shutdown_signal, shutdown_event.set)

    start_notification_consumer(loop)
    logger.info("Notification worker started")

    try:
        await shutdown_event.wait()
    finally:
        stop_notification_consumer()
        logger.info("Notification worker stopped")


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
