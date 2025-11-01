import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

logging_dir = Path(f"~/.local/state/{__package__}/log").expanduser()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
            "pathname": record.pathname,
            "lineno": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)

        # Add any extra attributes passed to the log call
        if hasattr(record, "extra"):
            log_record.update(record.extra)

        return json.dumps(log_record, ensure_ascii=False, default=str)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    file_logging: bool = False,
) -> logging.Logger:
    """
    Setup root logger,
    Can only be configured once in program entrypoint

    https://rednafi.com/python/no-hijack-root-logger/
    """
    logger = logging.getLogger()

    if getattr(logger, "_setup_root_logger", False):
        return logging.getLogger(name)

    debug = bool(os.environ.get("DEBUG", False))
    logger.setLevel(logging.DEBUG if debug else level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    if file_logging:
        logging_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=logging_dir / f"{name}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
        )
        file_handler.setFormatter(
            logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s][%(message)s]")
        )
        logger.addHandler(file_handler)

    logger._setup_root_logger = True

    return logger


def setup_json_logger(
    name: str,
    level: int = logging.INFO,
    file_logging: bool = False,
) -> logging.Logger:
    """
    Setup root logger in JSON format,
    Can only be configured once in program entrypoint

    https://rednafi.com/python/no-hijack-root-logger/
    """
    logger = logging.getLogger()

    if getattr(logger, "_setup_root_logger", False):
        return logging.getLogger(name)

    debug = bool(os.environ.get("DEBUG", False))
    logger.setLevel(logging.DEBUG if debug else level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    if file_logging:
        logging_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=logging_dir / f"{name}.jsonl",
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
        )
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    logger._setup_root_logger = True

    return logger
