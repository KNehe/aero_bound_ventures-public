import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

DEFAULT_LOG_FILE = "backend.log"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(lineno)d |%(message)s"


class LogManager:
    """ "
    Singleton class to manage and configure application logging.
    """

    _instance: Optional["LogManager"] = None
    _loggers: dict[str, logging.Logger] = {}

    def __new__(cls, *args, **kwargs) -> "LogManager":
        """
        Controls object creation to ensure singleton behavior.
        """
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._configure_root_logger()
        return cls._instance

    def _configure_root_logger(self) -> None:
        """
        Initializes and configures the main global settings for all loggers
        """
        root_logger = logging.getLogger()
        root_logger.setLevel(DEFAULT_LOG_LEVEL)

        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

        # Have one console handler
        if not any(
            isinstance(handler, logging.StreamHandler)
            for handler in root_logger.handlers
        ):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)

            root_logger.addHandler(console_handler)

        # Have one file handler
        if not any(
            isinstance(handler, TimedRotatingFileHandler)
            for handler in root_logger.handlers
        ):
            file_handler = TimedRotatingFileHandler(
                DEFAULT_LOG_FILE,
                when="midnight",
                interval=1,
                backupCount=7,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)

            root_logger.addHandler(file_handler)

        root_logger.info("Root logger configured successfully")

    def get_logger(self, name: str) -> logging.Logger:
        """
        Retrieves a module-specific logger by name, creating it if it doesn't exist.
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(DEFAULT_LOG_LEVEL)
            self._loggers[name] = logger

        return self._loggers[name]


log_manager = LogManager()


def get_app_logger(name: str = __name__) -> logging.Logger:
    """
    Public convenience function. All other files call this to get their logger
    """
    return log_manager.get_logger(name)
