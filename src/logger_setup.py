"""
Centralised logging configuration.

Call setup_logging() once at startup. All modules that do
`logging.getLogger(__name__)` will inherit these settings automatically.
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "curator.log"

FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    LOG_DIR.mkdir(exist_ok=True)

    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    root.setLevel(level)

    # File handler — full detail, always INFO+
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(FMT, DATE_FMT))

    # Console handler — INFO+ only, no timestamps (cleaner UX)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    root.addHandler(fh)
    root.addHandler(ch)
