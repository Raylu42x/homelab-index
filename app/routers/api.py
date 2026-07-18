"""JSON CRUD API — the foundation future MCP tools will call into.

Editing endpoints live here. They carry no authentication of their own;
Cloudflare Access in front of the whole app is the only gate, so this
router must never be exposed on a path Access doesn't cover.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import aggregates, search, storage
from app.models import Category, Page, Service, Settings
from app.storage import InvalidIdError, RecordNotFoundError

router = APIRouter(prefix="/api")


def _not_found(exc: Exception) -> HTTPException:
    if isinstance(exc, InvalidIdError):
        return HTTPException(status_code=400, detail=f"invalid id: {exc}")
    return HTTPException(status_code=404, detail=f"not found: {exc}")


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


@router.get("/services", response_model=list[Service])
def api_list_services(q: str | None = None, category: str | None = None, tag: str | None = None):
    services = storage.list_services()
    if q:
        services = search.search_services(services, q)
    if category:
        services = [s for s in services if s.category == category]
    if tag:
        services = [s for s in services if tag in s.tags]
    return services


@router.post("/services", response_model=Service, status_code=201)
def api_create_service(service: Service):
    try:
        storage.get_service(service.id)
        raise HTTPException(status_code=409, detail=f"service '{service.id}' already exists")
    except RecordNotFoundError:
        pass
    return storage.save_service(service)


@router.get("/services/{service_id}", response_model=Service)
def api_get_service(service_id: str):
    try:
        return storage.get_service(service_id)
    except (RecordNotFoundError, InvalidIdError) as exc:
        raise _not_found(exc)


@router.put("/services/{service_id}", response_model=Service)
def api_update_service(service_id: str, service: Service):
    if service.id != service_id:
        raise HTTPException(status_code=400, detail="id in body must match id in path")
    try:
        existing = storage.get_service(service_id)
        service.created = existing.created
    except (RecordNotFoundError, InvalidIdError):
        pass
    return storage.save_service(service)


@router.delete("/services/{service_id}", status_code=204)
def api_delete_service(service_id: str):
    try:
        storage.delete_service(service_id)
    except (RecordNotFoundError, InvalidIdError) as exc:
        raise _not_found(exc)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


@router.get("/categories", response_model=list[Category])
def api_list_categories():
    return storage.list_categories()


@router.post("/categories", response_model=Category, status_code=201)
def api_create_category(category: Category):
    try:
        storage.get_category(category.id)
        raise HTTPException(status_code=409, detail=f"category '{category.id}' already exists")
    except RecordNotFoundError:
        pass
    return storage.save_category(category)


@router.get("/categories/{category_id}", response_model=Category)
def api_get_category(category_id: str):
    try:
        return storage.get_category(category_id)
    except (RecordNotFoundError, InvalidIdError) as exc:
        raise _not_found(exc)


@router.put("/categories/{category_id}", response_model=Category)
def api_update_category(category_id: str, category: Category):
    if category.id != category_id:
        raise HTTPException(status_code=400, detail="id in body must match id in path")
    return storage.save_category(category)


@router.delete("/categories/{category_id}", status_code=204)
def api_delete_category(category_id: str):
    try:
        storage.delete_category(category_id)
    except (RecordNotFoundError, InvalidIdError) as exc:
        raise _not_found(exc)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


@router.get("/pages", response_model=list[Page])
def api_list_pages():
    return storage.list_pages()


@router.post("/pages", response_model=Page, status_code=201)
def api_create_page(page: Page):
    return storage.save_page(page)


@router.get("/pages/{page_id}", response_model=Page)
def api_get_page(page_id: str):
    try:
        return storage.get_page(page_id)
    except (RecordNotFoundError, InvalidIdError) as exc:
        raise _not_found(exc)


@router.put("/pages/{page_id}", response_model=Page)
def api_update_page(page_id: str, page: Page):
    if page.id != page_id:
        raise HTTPException(status_code=400, detail="id in body must match id in path")
    return storage.save_page(page)


@router.delete("/pages/{page_id}", status_code=204)
def api_delete_page(page_id: str):
    try:
        storage.delete_page(page_id)
    except (RecordNotFoundError, InvalidIdError) as exc:
        raise _not_found(exc)


# ---------------------------------------------------------------------------
# Settings & stats
# ---------------------------------------------------------------------------


@router.get("/settings", response_model=Settings)
def api_get_settings():
    return storage.get_settings()


@router.put("/settings", response_model=Settings)
def api_update_settings(settings: Settings):
    return storage.save_settings(settings)


@router.get("/stats")
def api_stats():
    services = storage.list_services()
    categories = storage.list_categories()
    return aggregates.compute_stats(services, categories)
