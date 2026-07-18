"""Runtime configuration for the homelab index."""

import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("HOMELAB_DATA_DIR", "./data")).resolve()
SERVICES_DIR = DATA_DIR / "services"
CATEGORIES_DIR = DATA_DIR / "categories"
PAGES_DIR = DATA_DIR / "pages"
SETTINGS_FILE = DATA_DIR / "settings.yaml"


def ensure_data_dirs() -> None:
    for d in (SERVICES_DIR, CATEGORIES_DIR, PAGES_DIR):
        d.mkdir(parents=True, exist_ok=True)
