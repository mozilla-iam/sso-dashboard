import json
import logging

from dashboard.jsonlog import JsonFormatter


def test_format_produces_valid_json_with_quotes_and_newlines():
    # The previous string-template formatter emitted invalid JSON whenever
    # a message contained quotes or newlines (e.g. tracebacks).
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.ERROR,
        pathname="/path/test_module.py",
        lineno=42,
        msg='oops "quoted" and\nmulti-line',
        args=(),
        exc_info=None,
        func="some_func",
    )

    out = formatter.format(record)
    data = json.loads(out)  # would have raised under the old formatter

    assert data["message"] == 'oops "quoted" and\nmulti-line'
    assert data["level"] == "ERROR"
    assert data["name"] == "test_module.py:test.logger:some_func:42"
