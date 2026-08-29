"""Test fixtures.

Every test runs against a fresh temp data directory. HOMELAB_DATA_DIR must be
set before app.config is imported, because the module resolves its paths at
import time.
"""
import importlib
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture()
def client(monkeypatch):
    from fastapi.testclient import TestClient

    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    for sub in ("services", "categories", "pages"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("HOMELAB_DATA_DIR", str(root))

    # config/storage cache their paths at import, so reload after the env change
    for mod in ("app.config", "app.storage", "app.aggregates", "app.search",
                "app.routers.api", "app.routers.pages", "app.routers.editing",
                "app.main"):
        if mod in sys.modules:
            importlib.reload(sys.modules[mod])
    import app.main
    importlib.reload(app.main)

    with TestClient(app.main.app) as c:
        c.data_dir = root
        yield c
    tmp.cleanup()


def svc(**over):
    base = {"id": "jellyfin", "name": "Jellyfin", "description": "Media server",
            "category": "media", "tags": ["video"], "favorite": False}
    base.update(over)
    return base
