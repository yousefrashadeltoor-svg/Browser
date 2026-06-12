"""
JO Browser — Utilities
Shared helpers: logging setup, path resolution, data-dir bootstrap.
"""

import logging
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"


def setup_logging():
    log_file = DATA_DIR / "jo_browser.log"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def ensure_data_dirs():
    for sub in ["downloads", "profiles", "themes", "backups"]:
        (DATA_DIR / sub).mkdir(parents=True, exist_ok=True)


def data_path(*parts) -> Path:
    return DATA_DIR.joinpath(*parts)


def asset_path(*parts) -> Path:
    return (ROOT / "assets").joinpath(*parts)
