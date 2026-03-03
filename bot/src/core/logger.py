from pathlib import Path
import logging
from logging import Logger
from logging.handlers import RotatingFileHandler

from .config import settings

def setup_logger(
    lvl: int = settings.logger.log_lvl,
    logger_path: Path = settings.logger.logger_path,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
    default_fmt: str = "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
) -> Logger:
    logger_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(__name__)
    logger.setLevel(level=lvl)
    formatter = logging.Formatter(fmt=default_fmt)

    file_handler = RotatingFileHandler(
        logger_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()