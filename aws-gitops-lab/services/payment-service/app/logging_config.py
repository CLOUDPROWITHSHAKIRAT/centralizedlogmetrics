import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "payment-service",
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_fields"):
            log.update(record.extra_fields)

        return json.dumps(log)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    logger = logging.getLogger("payment-service")
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]
    logger.propagate = False

    return logger
