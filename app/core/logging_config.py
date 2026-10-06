import logging
import sys

from pythonjsonlogger.jsonlogger import JsonFormatter

from app.core.settings import settings


def setup_logging() -> None:
    """
    Настраивает структурированное JSON-логирование.
    Автоматически подхватывает все поля, переданные через extra={...}
    """
    log_level_str = getattr(settings, "LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    if log_level > logging.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
