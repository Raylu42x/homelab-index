"""HTML create/edit/delete forms for services, categories, and pages.

This is what makes the site editable from itself, not just via hand-edited
YAML or the JSON API. Same trust model as the rest of the app: no auth of
its own, relies entirely on whatever sits in front (see docs/docker-deployment.md).
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app import storage
from app.models import Category, Page, Service, Subcategory
from app.storage import InvalidIdError, RecordNotFoundError

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, active_nav: str, **extra) -> dict:
    return {
        "request": request,
        "settings": storage.get_settings(),
        "active_nav": active_nav,
        **extra,
    }


def _opt(raw: str | None) -> str | None:
    return raw.strip() or None if raw else None


def _list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


async def _form(request: Request) -> dict:
    return dict(await request.form())


def _service_view(obj: Service | dict | None) -> dict:
    """Normalize a Service or a raw resubmitted form dict for the template."""
    if obj is None:
        return {}
    if isinstance(obj, Service):
        view = obj.model_dump(mode="json")
        view["tags"] = ", ".join(obj.tags)
        view["dependencies"] = ", ".join(obj.dependencies)
        return view
    return dict(obj)


def _category_view(obj: Category | dict | None) -> dict:
    if obj is None:
        return {}
    if isinstance(obj, Category):
        view = obj.model_dump(mode="json")
        view["subcategories"] = "\n".join(f"{s.id} | {s.name}" for s in obj.subcategories)
        return view
    return dict(obj)


def _page_view(obj: Page | dict | None) -> dict:
    if obj is None:
        return {}
    if isinstance(obj, Page):
        return obj.model_dump(mode="json")
    return dict(obj)


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

_SERVICE_TEXT_FIELDS = [
    "description", "category", "subcategory", "icon", "public_url",
    "tailscale_url", "home_url", "localhost_url", "docker_address",
    "hostname", "ip", "server", "docker_container", "docker_compose_project",
    "github_repository", "documentation", "notes", "owner",
]


def _service_from_form(form: dict, service_id: str, existing: Service | None) -> Service:
    data = {
        "id": service_id,
        "name": (form.get("name") or "").strip(),
        "favorite": "favorite" in form,
        "status": form.get("status") or "unknown",
        "tags": _list(form.get("tags")),
        "dependencies": _list(form.get("dependencies")),
    }
    for field in _SERVICE_TEXT_FIELDS:
        data[field] = _opt(form.get(field))
    if existing is not None:
        data["created"] = existing.created
    return Service.model_validate(data)


@router.get("/services/new", response_class=HTMLResponse)
def new_service_form(request: Request):
    context = _ctx(
        request, "services",
        service=None, categories=storage.list_categories(), mode="create", error=None,
    )
    return templates.TemplateResponse("service_form.html", context)


@router.post("/services/new", response_class=HTMLResponse)
async def create_service(request: Request):
    form = await _form(request)
    service_id = (form.get("id") or "").strip()

    error = None
    if service_id:
        try:
            storage.get_service(service_id)
            error = f"A service with id \"{service_id}\" already exists."
        except RecordNotFoundError:
            pass
        except InvalidIdError:
            error = "id must be letters, numbers, '-', or '_' only."

    if not error:
        try:
            service = _service_from_form(form, service_id, existing=None)
            storage.save_service(service)
            return RedirectResponse(url=f"/services/{service.id}", status_code=303)
        except ValidationError as exc:
            error = exc.errors()[0]["msg"] if exc.errors() else str(exc)

    context = _ctx(
        request, "services",
        service=_service_view(form), categories=storage.list_categories(), mode="create", error=error,
    )
    return templates.TemplateResponse("service_form.html", context, status_code=400)


@router.get("/services/{service_id}/edit", response_class=HTMLResponse)
def edit_service_form(request: Request, service_id: str):
    try:
        service = storage.get_service(service_id)
    except (RecordNotFoundError, InvalidIdError):
        return templates.TemplateResponse("404.html", _ctx(request, ""), status_code=404)
    context = _ctx(
        request, "services",
        service=_service_view(service), categories=storage.list_categories(), mode="edit", error=None,
    )
    return templates.TemplateResponse("service_form.html", context)


@router.post("/services/{service_id}/edit", response_class=HTMLResponse)
async def update_service(request: Request, service_id: str):
    try:
        existing = storage.get_service(service_id)
    except (RecordNotFoundError, InvalidIdError):
        return templates.TemplateResponse("404.html", _ctx(request, ""), status_code=404)

    form = await _form(request)
    try:
        service = _service_from_form(form, service_id, existing=existing)
        storage.save_service(service)
        return RedirectResponse(url=f"/services/{service.id}", status_code=303)
    except ValidationError as exc:
        error = exc.errors()[0]["msg"] if exc.errors() else str(exc)

    context = _ctx(
        request, "services",
        service=_service_view(form), categories=storage.list_categories(), mode="edit", error=error,
    )
    return templates.TemplateResponse("service_form.html", context, status_code=400)


@router.post("/services/{service_id}/delete")
def delete_service(service_id: str):
    try:
        storage.delete_service(service_id)
    except (RecordNotFoundError, InvalidIdError):
        pass
    return RedirectResponse(url="/services", status_code=303)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


def _subcategories_from_form(raw: str | None) -> list[Subcategory]:
    subs = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            sub_id, name = line.split("|", 1)
        else:
            sub_id, name = line, line
        sub_id, name = sub_id.strip(), name.strip()
        if sub_id:
            subs.append(Subcategory(id=sub_id, name=name or sub_id))
    return subs


def _category_from_form(form: dict, category_id: str) -> Category:
    return Category.model_validate({
        "id": category_id,
        "name": (form.get("name") or "").strip(),
        "description": _opt(form.get("description")),
        "icon": _opt(form.get("icon")),
        "order": int(form.get("order") or 100),
        "subcategories": _subcategories_from_form(form.get("subcategories")),
    })


@router.get("/categories/new", response_class=HTMLResponse)
def new_category_form(request: Request):
    context = _ctx(request, "categories", category=None, mode="create", error=None)
    return templates.TemplateResponse("category_form.html", context)


@router.post("/categories/new", response_class=HTMLResponse)
async def create_category(request: Request):
    form = await _form(request)
    category_id = (form.get("id") or "").strip()

    error = None
    if category_id:
        try:
            storage.get_category(category_id)
            error = f"A category with id \"{category_id}\" already exists."
        except RecordNotFoundError:
            pass
        except InvalidIdError:
            error = "id must be letters, numbers, '-', or '_' only."

    if not error:
        try:
            category = _category_from_form(form, category_id)
            storage.save_category(category)
            return RedirectResponse(url=f"/categories/{category.id}", status_code=303)
        except ValidationError as exc:
            error = exc.errors()[0]["msg"] if exc.errors() else str(exc)

    context = _ctx(request, "categories", category=_category_view(form), mode="create", error=error)
    return templates.TemplateResponse("category_form.html", context, status_code=400)


@router.get("/categories/{category_id}/edit", response_class=HTMLResponse)
def edit_category_form(request: Request, category_id: str):
    try:
        category = storage.get_category(category_id)
    except (RecordNotFoundError, InvalidIdError):
        return templates.TemplateResponse("404.html", _ctx(request, ""), status_code=404)
    context = _ctx(request, "categories", category=_category_view(category), mode="edit", error=None)
    return templates.TemplateResponse("category_form.html", context)


@router.post("/categories/{category_id}/edit", response_class=HTMLResponse)
async def update_category(request: Request, category_id: str):
    form = await _form(request)
    try:
        category = _category_from_form(form, category_id)
        storage.save_category(category)
        return RedirectResponse(url=f"/categories/{category.id}", status_code=303)
    except ValidationError as exc:
        error = exc.errors()[0]["msg"] if exc.errors() else str(exc)

    context = _ctx(request, "categories", category=_category_view(form), mode="edit", error=error)
    return templates.TemplateResponse("category_form.html", context, status_code=400)


@router.post("/categories/{category_id}/delete")
def delete_category(category_id: str):
    try:
        storage.delete_category(category_id)
    except (RecordNotFoundError, InvalidIdError):
        pass
    return RedirectResponse(url="/categories", status_code=303)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


def _page_from_form(form: dict, page_id: str) -> Page:
    return Page.model_validate({
        "id": page_id,
        "title": (form.get("title") or "").strip(),
        "content": form.get("content") or "",
        "order": int(form.get("order") or 100),
    })


@router.get("/docs/new", response_class=HTMLResponse)
def new_page_form(request: Request):
    context = _ctx(request, "docs", page=None, mode="create", error=None)
    return templates.TemplateResponse("page_form.html", context)


@router.post("/docs/new", response_class=HTMLResponse)
async def create_page(request: Request):
    form = await _form(request)
    page_id = (form.get("id") or "").strip()

    error = None
    if page_id:
        try:
            storage.get_page(page_id)
            error = f"A page with id \"{page_id}\" already exists."
        except RecordNotFoundError:
            pass
        except InvalidIdError:
            error = "id must be letters, numbers, '-', or '_' only."

    if not error:
        try:
            page = _page_from_form(form, page_id)
            storage.save_page(page)
            return RedirectResponse(url=f"/docs/{page.id}", status_code=303)
        except ValidationError as exc:
            error = exc.errors()[0]["msg"] if exc.errors() else str(exc)

    context = _ctx(request, "docs", page=_page_view(form), mode="create", error=error)
    return templates.TemplateResponse("page_form.html", context, status_code=400)


@router.get("/docs/{page_id}/edit", response_class=HTMLResponse)
def edit_page_form(request: Request, page_id: str):
    try:
        page = storage.get_page(page_id)
    except (RecordNotFoundError, InvalidIdError):
        return templates.TemplateResponse("404.html", _ctx(request, ""), status_code=404)
    context = _ctx(request, "docs", page=_page_view(page), mode="edit", error=None)
    return templates.TemplateResponse("page_form.html", context)


@router.post("/docs/{page_id}/edit", response_class=HTMLResponse)
async def update_page(request: Request, page_id: str):
    form = await _form(request)
    try:
        page = _page_from_form(form, page_id)
        storage.save_page(page)
        return RedirectResponse(url=f"/docs/{page.id}", status_code=303)
    except ValidationError as exc:
        error = exc.errors()[0]["msg"] if exc.errors() else str(exc)

    context = _ctx(request, "docs", page=_page_view(form), mode="edit", error=error)
    return templates.TemplateResponse("page_form.html", context, status_code=400)


@router.post("/docs/{page_id}/delete")
def delete_page(page_id: str):
    try:
        storage.delete_page(page_id)
    except (RecordNotFoundError, InvalidIdError):
        pass
    return RedirectResponse(url="/docs", status_code=303)
