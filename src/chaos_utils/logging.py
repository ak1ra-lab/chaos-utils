import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Standard LogRecord attributes — anything else on the record came from `extra=`
_LOG_RECORD_ATTRIBUTES = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "taskName",
    }
)


def _resolve_logging_dir(name: str) -> Path:
    """Return the XDG-compliant log directory for *name*.

    The directory is ``$XDG_STATE_HOME/<app>/log`` where *app* is the
    top-level package component of *name* (everything before the first
    ``'.'``).  ``XDG_STATE_HOME`` defaults to ``~/.local/state`` when not
    set, as specified by the XDG Base Directory Specification.

    Args:
        name: A logger name, typically the ``__name__`` of the caller module.

    Returns:
        A :class:`~pathlib.Path` for the resolved log directory.
    """
    xdg_state_home = Path(
        os.environ.get("XDG_STATE_HOME", "~/.local/state")
    ).expanduser()
    app_name = name.split(".")[0]
    return xdg_state_home / app_name / "log"


class TextFormatter(logging.Formatter):
    """A plain-text formatter that appends any ``extra=`` fields to the log line.

    The base :class:`logging.Formatter` is applied first (using the *fmt* and
    *datefmt* arguments passed to the constructor), then any extra attributes
    supplied via ``extra=`` are appended as ``key=value`` pairs separated by
    spaces.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format *record* as plain text, appending any ``extra=`` fields.

        Args:
            record: The :class:`logging.LogRecord` to format.

        Returns:
            A formatted string with extra fields appended when present.
        """
        message = super().format(record)
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _LOG_RECORD_ATTRIBUTES
        }
        if extras:
            extra_str = " ".join(f"{k}={v}" for k, v in extras.items())
            return f"{message} {extra_str}"
        return message


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        """Format a LogRecord as a JSON string.

        The returned value is a JSON-encoded object containing the timestamp,
        level, message and common record metadata. If exception information is
        present it will be included as a string under ``exc_info``. Any extra
        attributes supplied to the logging call (commonly passed via the
        ``extra`` parameter) are merged into the produced JSON object.

        Args:
            record: The :class:`logging.LogRecord` to format.

        Returns:
            A JSON string representing the log record.
        """

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

        # Python merges extra= keys directly onto the LogRecord as top-level
        # attributes, so collect anything that isn't a standard field.
        for key, value in record.__dict__.items():
            if key not in _LOG_RECORD_ATTRIBUTES:
                log_record[key] = value

        return json.dumps(log_record, ensure_ascii=False, default=str)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    file_logging: bool | Path = False,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 10,
) -> logging.Logger:
    """
    Configure and return the root logger for the process.

    Args:
        name: The name of the logger to return (usually ``__name__`` of the
            caller module).
        level: The default logging level to set on the root logger if not in
            debug mode. Default is ``logging.INFO``.
        file_logging: Controls rotating file logging.

            * ``False`` (default) — no file logging.
            * ``True`` — write to
              ``$XDG_STATE_HOME/<app>/log/<name>.log`` where *app* is the
              top-level package component of *name*.
            * :class:`~pathlib.Path` — write to the given file path
              directly (the parent directory is created if necessary).
        max_bytes: Maximum size in bytes of each log file before rotation.
            Default is 10 MiB.
        backup_count: Number of rotated backup files to keep. Default is 10.

    Returns:
        A configured :class:`logging.Logger` instance for ``name``.
    """
    logger = logging.getLogger()

    if getattr(logger, "_setup_root_logger", False):
        return logging.getLogger(name)

    debug = bool(os.environ.get("DEBUG", False))
    logger.setLevel(logging.DEBUG if debug else level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(TextFormatter("%(message)s"))
    logger.addHandler(console_handler)

    if file_logging is not False:
        if isinstance(file_logging, Path):
            log_path = file_logging
        else:
            log_dir = _resolve_logging_dir(name)
            log_path = log_dir / f"{name}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(
            TextFormatter("[%(asctime)s][%(name)s][%(levelname)s][%(message)s]")
        )
        logger.addHandler(file_handler)

    logger._setup_root_logger = True

    return logger


def setup_json_logger(
    name: str,
    level: int = logging.INFO,
    file_logging: bool | Path = False,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 10,
) -> logging.Logger:
    """Configure and return the root logger that emits JSON-formatted logs.

    This is identical to :func:`setup_logger` except that any file handler
    created will use :class:`JsonFormatter` so persisted logs are JSON lines
    (``.jsonl``). A console handler is still attached which emits JSON for
    structured log consumers.

    Args:
        name: The name of the logger to return (usually ``__name__`` of the
            caller module).
        level: The default logging level to set on the root logger if not in
            debug mode. Default is ``logging.INFO``.
        file_logging: Controls rotating file logging.

            * ``False`` (default) — no file logging.
            * ``True`` — write to
              ``$XDG_STATE_HOME/<app>/log/<name>.jsonl`` where *app* is the
              top-level package component of *name*.
            * :class:`~pathlib.Path` — write to the given file path
              directly (the parent directory is created if necessary).
        max_bytes: Maximum size in bytes of each log file before rotation.
            Default is 10 MiB.
        backup_count: Number of rotated backup files to keep. Default is 10.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger()

    if getattr(logger, "_setup_root_logger", False):
        return logging.getLogger(name)

    debug = bool(os.environ.get("DEBUG", False))
    logger.setLevel(logging.DEBUG if debug else level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)

    if file_logging is not False:
        if isinstance(file_logging, Path):
            log_path = file_logging
        else:
            log_dir = _resolve_logging_dir(name)
            log_path = log_dir / f"{name}.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    logger._setup_root_logger = True

    return logger
