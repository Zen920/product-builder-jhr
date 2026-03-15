import atexit
import logging.config
import os
from project_builder_jhr.helpers.utils import get_project_root
from pathlib import Path

project_root = get_project_root()


logger = logging.getLogger("root_logger")

def _is_streamlit_cloud() -> bool:
    return os.environ.get("STREAMLIT_SHARING_MODE") is not None

def _build_logger_config(log_path: Path) -> dict:
    handlers = {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "simple",
            "level": "INFO",
        },
        "queue": {
            "class": "logging.handlers.QueueHandler",
            "handlers": ["stdout"],
            "respect_handler_level": False,
        }
    }

    if not _is_streamlit_cloud():
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "detailed",
            "level": "WARNING",
            "filename": str(log_path),
            "maxBytes": 1000000,
            "backupCount": 3,
            "encoding": "utf-8"
        }
        handlers["queue"]["handlers"].append("file")
    return {
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
        "handlers": handlers,
        "loggers": {
            "": { "level": "DEBUG", "handlers": ["queue"] }
        }
    }
    
def setup_logging():
    log_path = Path(get_project_root()) / "logs" / "logconfig.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.config.dictConfig(_build_logger_config(log_path))
    queue_handler = logging.getHandlerByName("queue")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)