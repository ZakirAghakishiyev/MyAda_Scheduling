"""Application logging: console + daily rotated .txt files; keep last N days."""

from __future__ import annotations

import logging.config
import os
from pathlib import Path

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_setup_done = False


def setup_logging() -> None:
    """
    Console (stdout) + daily rotated text log under LOG_DIR.
    TimedRotatingFileHandler with backupCount removes the oldest file when more than N
    rotated dailies exist (midnight rollover).
    Idempotent for uvicorn --reload.
    """
    global _setup_done
    if _setup_done:
        return

    log_dir = Path(os.getenv("LOG_DIR", "logs")).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    filename = os.getenv("LOG_FILENAME", "scheduling.txt")
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "7"))
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = str(log_dir / filename)

    def _clear_handlers(name: str) -> None:
        lg = logging.getLogger(name)
        for h in lg.handlers[:]:
            lg.removeHandler(h)
            try:
                h.close()
            except Exception:
                pass

    for logger_name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
        _clear_handlers(logger_name)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": _LOG_FORMAT,
                    "datefmt": _DATE_FORMAT,
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                },
                "file_rotating": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "formatter": "standard",
                    "filename": log_file,
                    "when": "midnight",
                    "interval": 1,
                    "backupCount": backup_count,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "level": level,
                "handlers": ["console", "file_rotating"],
            },
            "loggers": {
                "uvicorn": {
                    "level": level,
                    "handlers": ["console", "file_rotating"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": level,
                    "handlers": ["console", "file_rotating"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": level,
                    "handlers": ["console", "file_rotating"],
                    "propagate": False,
                },
            },
        }
    )

    # Filename pattern for rotated files (not always accepted via dictConfig constructor)
    for lg_name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
        for h in logging.getLogger(lg_name).handlers:
            if isinstance(h, logging.handlers.TimedRotatingFileHandler):
                h.suffix = "%Y-%m-%d"

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    _setup_done = True
