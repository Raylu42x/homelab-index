"""YAML-backed storage for services, categories, and settings.

Every service and category lives in its own YAML file so the data directory
stays easy to diff and git-friendly. Writes are atomic (write to a temp file,
then rename) so a crash mid-write can't corrupt a record.
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml
from pydantic import ValidationError

from app.config import CATEGORIES_DIR, PAGES_DIR, SERVICES_DIR, SETTINGS_FILE
from app.models import Category, Page, Service, Settings


class RecordNotFoundError(Exception):
    pass


class InvalidIdError(Exception):
    pass


def _is_safe_id(record_id: str) -> bool:
    return bool(record_id) and all(c.isalnum() or c in "-_" for c in record_id)


def _atomic_write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _load_yaml(path: Path) -> dict:
    with path.open("r") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


def list_services() -> list[Service]:
    services = []
    if not SERVICES_DIR.exists():
        return services
    for path in sorted(SERVICES_DIR.glob("*.yaml")):
        try:
            services.append(Service.model_validate(_load_yaml(path)))
        except ValidationError:
            continue
    return services


def get_service(service_id: str) -> Service:
    if not _is_safe_id(service_id):
        raise InvalidIdError(service_id)
    path = SERVICES_DIR / f"{service_id}.yaml"
    if not path.exists():
        raise RecordNotFoundError(service_id)
    return Service.model_validate(_load_yaml(path))


def save_service(service: Service) -> Service:
    if not _is_safe_id(service.id):
        raise InvalidIdError(service.id)
    now = datetime.now(timezone.utc)
    if service.created is None:
        service.created = now
    service.updated = now
    path = SERVICES_DIR / f"{service.id}.yaml"
    data = service.model_dump(mode="json", exclude_none=True)
    _atomic_write_yaml(path, data)
    return service


def delete_service(service_id: str) -> None:
    if not _is_safe_id(service_id):
        raise InvalidIdError(service_id)
    path = SERVICES_DIR / f"{service_id}.yaml"
    if not path.exists():
        raise RecordNotFoundError(service_id)
    path.unlink()


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


def list_categories() -> list[Category]:
    categories = []
    if not CATEGORIES_DIR.exists():
        return categories
    for path in sorted(CATEGORIES_DIR.glob("*.yaml")):
        try:
            categories.append(Category.model_validate(_load_yaml(path)))
        except ValidationError:
            continue
    return sorted(categories, key=lambda c: (c.order, c.name))


def get_category(category_id: str) -> Category:
    if not _is_safe_id(category_id):
        raise InvalidIdError(category_id)
    path = CATEGORIES_DIR / f"{category_id}.yaml"
    if not path.exists():
        raise RecordNotFoundError(category_id)
    return Category.model_validate(_load_yaml(path))


def save_category(category: Category) -> Category:
    if not _is_safe_id(category.id):
        raise InvalidIdError(category.id)
    path = CATEGORIES_DIR / f"{category.id}.yaml"
    data = category.model_dump(mode="json", exclude_none=True)
    _atomic_write_yaml(path, data)
    return category


def delete_category(category_id: str) -> None:
    if not _is_safe_id(category_id):
        raise InvalidIdError(category_id)
    path = CATEGORIES_DIR / f"{category_id}.yaml"
    if not path.exists():
        raise RecordNotFoundError(category_id)
    path.unlink()


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


def list_pages() -> list[Page]:
    pages = []
    if not PAGES_DIR.exists():
        return pages
    for path in sorted(PAGES_DIR.glob("*.yaml")):
        try:
            pages.append(Page.model_validate(_load_yaml(path)))
        except ValidationError:
            continue
    return sorted(pages, key=lambda p: (p.order, p.title))


def get_page(page_id: str) -> Page:
    if not _is_safe_id(page_id):
        raise InvalidIdError(page_id)
    path = PAGES_DIR / f"{page_id}.yaml"
    if not path.exists():
        raise RecordNotFoundError(page_id)
    return Page.model_validate(_load_yaml(path))


def save_page(page: Page) -> Page:
    if not _is_safe_id(page.id):
        raise InvalidIdError(page.id)
    path = PAGES_DIR / f"{page.id}.yaml"
    _atomic_write_yaml(path, page.model_dump(mode="json", exclude_none=True))
    return page


def delete_page(page_id: str) -> None:
    if not _is_safe_id(page_id):
        raise InvalidIdError(page_id)
    path = PAGES_DIR / f"{page_id}.yaml"
    if not path.exists():
        raise RecordNotFoundError(page_id)
    path.unlink()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def get_settings() -> Settings:
    if not SETTINGS_FILE.exists():
        return Settings()
    return Settings.model_validate(_load_yaml(SETTINGS_FILE))


def save_settings(settings: Settings) -> Settings:
    _atomic_write_yaml(SETTINGS_FILE, settings.model_dump(mode="json", exclude_none=True))
    return settings
