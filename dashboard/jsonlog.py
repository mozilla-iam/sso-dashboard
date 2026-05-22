"""JSON log formatter.

Replaces the string-template ``[formatter_json]`` previously declared in
``logging.ini``, which emitted invalid JSON when a message contained a
quote or newline (e.g. tracebacks). Preserves the historical output shape:
{"time": ..., "level": ..., "process_id": ..., "message": ..., "name": ...}.
"""

import json
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "process_id": record.process,
            "message": record.getMessage(),
            "name": f"{record.filename}:{record.name}:{record.funcName}:{record.lineno}",
        }
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            data["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(data)
