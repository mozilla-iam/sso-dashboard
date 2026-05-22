import json
import logging

from dashboard.jsonlog import JsonFormatter


def test_format_produces_valid_json_with_quotes_and_newlines():
    # The previous string-template formatter emitted invalid JSON whenever
    # a message contained quotes or newlines (e.g. tracebacks). Args are
    # interpolated into msg via record.getMessage(); use real args here so
    # the test covers the args path alongside the literal-message path.
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.ERROR,
        pathname="/path/test_module.py",
        lineno=42,
        msg="oops %s and\n%s",
        args=('"quoted"', "multi-line"),
        exc_info=None,
        func="some_func",
    )

    out = formatter.format(record)
    data = json.loads(out)  # would have raised under the old formatter

    assert data["message"] == 'oops "quoted" and\nmulti-line'
    assert data["level"] == "ERROR"
    assert data["name"] == "test_module.py:test.logger:some_func:42"


def test_format_includes_exc_info_when_record_has_traceback():
    # logger.exception(...) populates record.exc_info; the formatter must
    # surface the traceback as a separate JSON field instead of dropping it
    # or appending it (which would break JSON validity).
    import sys

    formatter = JsonFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        exc_info = sys.exc_info()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.ERROR,
        pathname="/path/test_module.py",
        lineno=42,
        msg="something went wrong",
        args=(),
        exc_info=exc_info,
        func="some_func",
    )

    out = formatter.format(record)
    data = json.loads(out)

    assert data["message"] == "something went wrong"
    assert "ValueError: boom" in data["exc_info"]
    assert "Traceback" in data["exc_info"]
