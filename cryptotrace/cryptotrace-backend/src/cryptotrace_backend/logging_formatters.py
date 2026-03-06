"""
Formateador de logs en JSON para criterios de calidad (trazabilidad, análisis).
Cada línea del archivo es un objeto JSON.
"""
import json
import logging
from django.utils import timezone as django_tz


class JsonFormatter(logging.Formatter):
    """
    Formatea cada registro como una línea JSON con campos estructurados.
    """

    def format(self, record):
        log_obj = {
            "timestamp": django_tz.now().isoformat() if hasattr(django_tz, "now") else self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": getattr(record, "funcName", ""),
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        # Incluir extras pasados con logger.info(..., extra={...})
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName", "levelname", "levelno",
                "lineno", "module", "msecs", "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName", "message", "taskName",
            ):
                try:
                    json.dumps(value)
                    log_obj[key] = value
                except (TypeError, ValueError):
                    log_obj[key] = str(value)
        return json.dumps(log_obj, ensure_ascii=False)
