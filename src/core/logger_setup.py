import logging
from logging import Logger
from pathlib import Path

from logging.handlers import RotatingFileHandler

from .config import settings


def setup_logger(
    lvl: int,
    logs_path: Path,
    log_format: str,
    max_bytes: int,
    backup_count: int,
) -> Logger:
    logs_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(__name__)
    logger.setLevel(level=lvl)
    formatter = logging.Formatter(log_format)

    file_handler = RotatingFileHandler(
        settings.logger_config.logger_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger(
    lvl=settings.logger.lvl,
    logs_path=settings.logger.logs_path,
    log_format=settings.logger.log_format,
    max_bytes=settings.logger.max_bytes,
    backup_count=settings.logger.backup_count,
)
