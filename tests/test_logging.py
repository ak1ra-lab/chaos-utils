"""Tests for chaos_utils.logging."""

import json
import logging

import pytest


@pytest.fixture(autouse=True)
def reset_root_logger():
    """Reset the global root logger state before and after each test.

    setup_logger / setup_json_logger set ``_setup_root_logger = True`` on the
    root logger to guard against double-initialisation.  This fixture tears
    down that state so tests remain independent.
    """
    root = logging.getLogger()
    yield
    # Remove any handlers added during the test
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)
    # Clear the guard flag so the next test starts fresh
    if hasattr(root, "_setup_root_logger"):
        del root._setup_root_logger
    root.setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# JsonFormatter
# ---------------------------------------------------------------------------


def _make_record(msg="hello", level=logging.INFO, exc_info=None, stack_info=None):
    """Return a minimal LogRecord for testing the formatter."""
    logger = logging.getLogger("test.json")
    record = logger.makeRecord(
        name="test.json",
        level=level,
        fn="test_file.py",
        lno=42,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )
    if stack_info is not None:
        record.stack_info = stack_info
    return record


def test_json_formatter_basic():
    from chaos_utils.logging import JsonFormatter

    formatter = JsonFormatter()
    record = _make_record("test message")
    output = formatter.format(record)
    data = json.loads(output)
    assert data["message"] == "test message"
    assert data["level"] == "INFO"
    assert data["name"] == "test.json"
    assert data["lineno"] == 42
    assert "timestamp" in data
    assert "process" in data
    assert "thread" in data


def test_json_formatter_with_exc_info():
    from chaos_utils.logging import JsonFormatter

    formatter = JsonFormatter()
    try:
        raise ValueError("oops")
    except ValueError:
        import sys

        exc_info = sys.exc_info()

    record = _make_record(exc_info=exc_info)
    output = formatter.format(record)
    data = json.loads(output)
    assert "exc_info" in data
    assert "ValueError" in data["exc_info"]


def test_json_formatter_with_stack_info():
    from chaos_utils.logging import JsonFormatter

    formatter = JsonFormatter()
    record = _make_record(stack_info="Stack trace here")
    output = formatter.format(record)
    data = json.loads(output)
    assert "stack_info" in data
    assert data["stack_info"] == "Stack trace here"


def test_json_formatter_with_extra():
    """Extra fields passed via extra= should appear as top-level JSON keys.

    Python's logging module merges extra= keys directly onto the LogRecord as
    top-level attributes (e.g. record.request_id), not as a nested dict under
    an "extra" key.  Simulate that behaviour by setting attributes directly.
    """
    from chaos_utils.logging import JsonFormatter

    formatter = JsonFormatter()
    record = _make_record("msg")
    # Simulate what logging.Logger.makeRecord does when called with extra=
    record.request_id = "abc123"
    record.user = "alice"
    output = formatter.format(record)
    data = json.loads(output)
    assert data["request_id"] == "abc123"
    assert data["user"] == "alice"


def test_json_formatter_no_extra_fields():
    """Records without any extra fields should format without error."""
    from chaos_utils.logging import JsonFormatter

    formatter = JsonFormatter()
    record = _make_record("no extra")
    output = formatter.format(record)
    data = json.loads(output)
    assert data["message"] == "no extra"


# ---------------------------------------------------------------------------
# setup_logger
# ---------------------------------------------------------------------------


def test_setup_logger_returns_named_logger():
    from chaos_utils.logging import setup_logger

    # First call initialises the root logger and returns logging.getLogger(name).
    # On a fresh root logger (no _setup_root_logger flag) the function returns
    # logging.getLogger(name) after the initial setup.
    logger = setup_logger("mymodule")
    assert isinstance(logger, logging.Logger)
    # After first call the guard is set; a second call must return the named logger.
    logger2 = setup_logger("mymodule")
    assert logger2.name == "mymodule"


def test_setup_logger_sets_level():
    from chaos_utils.logging import setup_logger

    setup_logger("x", level=logging.WARNING)
    root = logging.getLogger()
    assert root.level == logging.WARNING


def test_setup_logger_second_call_returns_early():
    """After first call the guard prevents double-adding handlers."""
    from chaos_utils.logging import setup_logger

    setup_logger("first")
    handler_count = len(logging.getLogger().handlers)

    # Second call should NOT add more handlers
    setup_logger("second")
    assert len(logging.getLogger().handlers) == handler_count


def test_setup_logger_debug_env_var(monkeypatch):
    """When DEBUG is set, root logger level becomes DEBUG."""
    monkeypatch.setenv("DEBUG", "1")
    from chaos_utils.logging import setup_logger

    setup_logger("debug_test")
    assert logging.getLogger().level == logging.DEBUG


def test_setup_logger_file_logging(tmp_path):
    """With file_logging=Path a RotatingFileHandler is added at that path."""
    from logging.handlers import RotatingFileHandler

    from chaos_utils.logging import setup_logger

    log_file = tmp_path / "filetest.log"
    setup_logger("filetest", file_logging=log_file)

    root = logging.getLogger()
    file_handlers = [h for h in root.handlers if isinstance(h, RotatingFileHandler)]
    assert len(file_handlers) == 1
    assert log_file.exists()


# ---------------------------------------------------------------------------
# setup_json_logger
# ---------------------------------------------------------------------------


def test_setup_json_logger_returns_named_logger():
    from chaos_utils.logging import setup_json_logger

    setup_json_logger("json_test")  # initialise
    # Second call through the guard returns the named logger.
    logger = setup_json_logger("json_test")
    assert logger.name == "json_test"


def test_setup_json_logger_second_call_guard():
    from chaos_utils.logging import setup_json_logger

    setup_json_logger("j1")
    handler_count = len(logging.getLogger().handlers)
    setup_json_logger("j2")
    assert len(logging.getLogger().handlers) == handler_count


def test_setup_json_logger_file_logging(tmp_path):
    """With file_logging=Path a RotatingFileHandler with JsonFormatter is added."""
    from logging.handlers import RotatingFileHandler

    from chaos_utils.logging import JsonFormatter, setup_json_logger

    log_file = tmp_path / "jsonfile.jsonl"
    setup_json_logger("jsonfile", file_logging=log_file)

    root = logging.getLogger()
    file_handlers = [h for h in root.handlers if isinstance(h, RotatingFileHandler)]
    assert len(file_handlers) == 1
    assert isinstance(file_handlers[0].formatter, JsonFormatter)
    assert log_file.exists()
