import atexit
import logging.config

from project_builder_jhr.helpers.utils import get_project_root

project_root = get_project_root()


logger = logging.getLogger("root_logger")

logger_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S%z",
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "simple",
            "level": "INFO",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "detailed",
            "level": "WARNING",
            "filename": f"{project_root}/logs/logconfig.log",
            "maxBytes": 1000000,
            "backupCount": 3,
            "encoding": "utf-8"
        },
        "queue": {
            "class": "logging.handlers.QueueHandler",
            "handlers": ["file", "stdout"],
            "respect_handler_level": False,
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG", "handlers": ["queue"]
        }
    },
}
def setup_logging():
    logging.config.dictConfig(logger_config)
    queue_handler = logging.getHandlerByName("queue")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)
