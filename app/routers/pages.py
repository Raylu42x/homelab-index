"""HTML page routes rendered with Jinja templates."""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import aggregates, search, storage
from app.models import Settings
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


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    services = storage.list_services()
    categories = storage.list_categories()
    context = _ctx(
        request,
        "home",
        favorites=[s for s in services if s.favorite],
        categories=categories,
        recent=aggregates.recently_updated(services),
        stats=aggregates.compute_stats(services, categories),
    )
    return templates.TemplateResponse("home.html", context)


@router.get("/services", response_class=HTMLResponse)
def services_list(
    request: Request,
    q: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    sort: str = "name",
):
    services = storage.list_services()
    if q:
        services = search.search_services(services, q)
    if category:
        services = [s for s in services if s.category == category]
    if tag:
        services = [s for s in services if tag in s.tags]

    if sort == "updated":
        services.sort(key=lambda s: s.updated or s.created or "", reverse=True)
    elif sort == "category":
        services.sort(key=lambda s: (s.category or "", s.name.lower()))
    else:
        services.sort(key=lambda s: s.name.lower())

    all_tags = sorted({t for s in storage.list_services() for t in s.tags})
    context = _ctx(
        request,
        "services",
        services=services,
        categories=storage.list_categories(),
        all_tags=all_tags,
        q=q or "",
        active_category=category or "",
        active_tag=tag or "",
        sort=sort,
    )
    return templates.TemplateResponse("services.html", context)


@router.get("/favorites", response_class=HTMLResponse)
def favorites(request: Request):
    services = [s for s in storage.list_services() if s.favorite]
    services.sort(key=lambda s: s.name.lower())
    context = _ctx(
        request,
        "favorites",
        services=services,
        categories=storage.list_categories(),
        all_tags=[],
        q="",
        active_category="",
        active_tag="",
        sort="name",
        title_override="Favorites",
    )
    return templates.TemplateResponse("services.html", context)


@router.get("/services/{service_id}", response_class=HTMLResponse)
def service_detail(request: Request, service_id: str):
    try:
        service = storage.get_service(service_id)
    except (RecordNotFoundError, InvalidIdError):
        return templates.TemplateResponse(
            "404.html", _ctx(request, ""), status_code=404
        )

    all_services = storage.list_services()
    related = [
        s
        for s in all_services
        if s.id != service.id
        and (
            s.id in service.dependencies
            or service.id in s.dependencies
            or (service.category and s.category == service.category)
        )
    ][:6]

    context = _ctx(request, "services", service=service, related=related)
    return templates.TemplateResponse("service_detail.html", context)


@router.post("/services/{service_id}/toggle-favorite", response_class=HTMLResponse)
def toggle_favorite(request: Request, service_id: str):
    service = storage.get_service(service_id)
    service.favorite = not service.favorite
    storage.save_service(service)
    return templates.TemplateResponse(
        "partials/favorite_button.html", {"request": request, "service": service}
    )


@router.get("/categories", response_class=HTMLResponse)
def categories_list(request: Request):
    categories = storage.list_categories()
    services = storage.list_services()
    counts = {c.id: sum(1 for s in services if s.category == c.id) for c in categories}
    context = _ctx(request, "categories", categories=categories, counts=counts)
    return templates.TemplateResponse("categories.html", context)


@router.get("/categories/{category_id}", response_class=HTMLResponse)
def category_detail(request: Request, category_id: str):
    try:
        category = storage.get_category(category_id)
    except (RecordNotFoundError, InvalidIdError):
        return templates.TemplateResponse(
            "404.html", _ctx(request, ""), status_code=404
        )
    services = [s for s in storage.list_services() if s.category == category_id]
    services.sort(key=lambda s: s.name.lower())
    context = _ctx(request, "categories", category=category, services=services)
    return templates.TemplateResponse("category_detail.html", context)


@router.get("/servers", response_class=HTMLResponse)
def servers(request: Request):
    groups = aggregates.group_by_server(storage.list_services())
    return templates.TemplateResponse("servers.html", _ctx(request, "servers", groups=groups))


@router.get("/domains", response_class=HTMLResponse)
def domains(request: Request):
    groups = aggregates.group_by_domain(storage.list_services())
    return templates.TemplateResponse("domains.html", _ctx(request, "domains", groups=groups))


@router.get("/projects", response_class=HTMLResponse)
def projects(request: Request):
    groups = aggregates.group_by_project(storage.list_services())
    return templates.TemplateResponse("projects.html", _ctx(request, "projects", groups=groups))


@router.get("/docs", response_class=HTMLResponse)
def docs_list(request: Request):
    pages = storage.list_pages()
    return templates.TemplateResponse("docs.html", _ctx(request, "docs", pages=pages))


@router.get("/docs/{page_id}", response_class=HTMLResponse)
def docs_detail(request: Request, page_id: str):
    try:
        page = storage.get_page(page_id)
    except (RecordNotFoundError, InvalidIdError):
        return templates.TemplateResponse(
            "404.html", _ctx(request, ""), status_code=404
        )
    return templates.TemplateResponse("page_detail.html", _ctx(request, "docs", page=page))


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    stats = aggregates.compute_stats(storage.list_services(), storage.list_categories())
    return templates.TemplateResponse("settings.html", _ctx(request, "settings", stats=stats))


@router.post("/settings")
def update_settings(
    site_name: str = Form(...),
    tagline: str = Form(""),
    domain: str = Form(""),
    timezone: str = Form("UTC"),
):
    storage.save_settings(
        Settings(site_name=site_name, tagline=tagline, domain=domain or None, timezone=timezone)
    )
    return RedirectResponse(url="/settings", status_code=303)


@router.get("/search", response_class=HTMLResponse)
def search_page(request: Request, q: str = ""):
    results = search.search_services(storage.list_services(), q) if q else []
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return templates.TemplateResponse(
            "partials/search_results.html", {"request": request, "q": q, "results": results}
        )
    context = _ctx(request, "search", q=q, results=results)
    return templates.TemplateResponse("search.html", context)
