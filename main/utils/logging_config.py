"""Logging configuration for the CSFloat bot.

Creates a daily rotating file named `csfloat_bot` and rotates to
`csfloat_bot_YYYY-MM-DD.log` at midnight.
"""
import logging
import os
from datetime import datetime, timedelta
import threading
import time
import glob
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

log_path = os.getenv("LOG_DIR")
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_base_name = os.getenv("LOG_FILE_NAME", "csfloat_bot.log")


def setup_logging(log_dir: Optional[str] = log_path) -> logging.Logger:
    """
    Sets up logging with daily rotation and cleanup of old logs.
    Logs are written to both a file and the console. The log file rotates at midnight
    and old log files are cleaned up after 30 days.
    """
    logger = logging.getLogger("CSFloatBot")
    logger.setLevel(getattr(logging, log_level))
    logger.propagate = False

    if log_dir is None:
        log_dir = os.path.abspath(os.path.dirname(__file__))
    os.makedirs(log_dir, exist_ok=True)

    base_name_no_ext = os.path.splitext(log_base_name)[0]

    def current_log_path(dt: Optional[datetime] = None) -> str:
        if dt is None:
            dt = datetime.now()
        date_str = dt.strftime("%Y-%m-%d")
        return os.path.join(log_dir, f"{base_name_no_ext}_{date_str}.log")

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Clear existing handlers to avoid duplicate logs on reconfigure
    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(current_log_path(), encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Background thread to swap handlers at midnight and cleanup old logs
    def _seconds_until_midnight() -> float:
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return (tomorrow - now).total_seconds()

    def _cleanup_old_logs(keep: int = 30) -> None:
        pattern = os.path.join(log_dir, f"{base_name_no_ext}_*.log")
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        for old in files[keep:]:
            try:
                os.remove(old)
            except OSError:
                pass

    def _rotate_loop() -> None:
        nonlocal file_handler
        while True:
            secs = _seconds_until_midnight()
            time.sleep(secs + 1)
            try:
                new_handler = logging.FileHandler(current_log_path(), encoding="utf-8")
                new_handler.setFormatter(formatter)

                # swap handlers
                logger.addHandler(new_handler)
                logger.removeHandler(file_handler)
                try:
                    file_handler.close()
                except Exception:
                    pass
                file_handler = new_handler

                # cleanup old files
                _cleanup_old_logs(keep=30)
            except Exception:
                # If rotation fails, log to existing handlers (avoid crashing thread)
                logger.exception("Failed to rotate log file")

    rotate_thread = threading.Thread(target=_rotate_loop, daemon=True)
    rotate_thread.start()

    return logger