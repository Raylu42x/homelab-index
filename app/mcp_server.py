"""MCP server exposing the homelab index as tools for an AI agent.

Runs as its own process (see docker-compose.yml) using the streamable-http
transport so it's reachable remotely, e.g. over Tailscale from a laptop.
Shares the same /data directory as the web app — both just call into
app.storage directly, no HTTP hop between them.

Same trust model as the rest of the app: no auth of its own. Anyone who can
reach this port can read and rewrite the whole inventory, so keep it off
anything Cloudflare Access doesn't already cover (Tailscale-only is the
intended exposure).
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from app import aggregates, search, storage
from app.config import ensure_data_dirs
from app.models import Category, Service
from app.storage import InvalidIdError, RecordNotFoundError

ensure_data_dirs()

mcp = FastMCP(
    "Homelab Index",
    host="0.0.0.0",
    port=int(os.environ.get("MCP_PORT", "8001")),
)


def _service_dict(service: Service) -> dict[str, Any]:
    return service.model_dump(mode="json", exclude_none=True)


def _category_dict(category: Category) -> dict[str, Any]:
    return category.model_dump(mode="json", exclude_none=True)


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


@mcp.tool()
def search_services(query: str) -> list[dict[str, Any]]:
    """Search services by name, description, tags, category, notes, URLs, hostnames, and docker container names."""
    results = search.search_services(storage.list_services(), query)
    return [_service_dict(s) for s in results]


@mcp.tool()
def list_services(category: str | None = None, tag: str | None = None) -> list[dict[str, Any]]:
    """List all services, optionally filtered by category id or tag."""
    services = storage.list_services()
    if category:
        services = [s for s in services if s.category == category]
    if tag:
        services = [s for s in services if tag in s.tags]
    return [_service_dict(s) for s in services]


@mcp.tool()
def get_service(id: str) -> dict[str, Any]:
    """Get full details for one service by its id."""
    try:
        return _service_dict(storage.get_service(id))
    except RecordNotFoundError:
        raise ValueError(f"no service with id '{id}'")
    except InvalidIdError:
        raise ValueError(f"'{id}' is not a valid service id")


@mcp.tool()
def add_service(service: dict[str, Any]) -> dict[str, Any]:
    """Add a new service. Only 'id' and 'name' are required; see get_service on an
    existing entry for the full list of optional fields (urls, hostname, tags, etc)."""
    try:
        storage.get_service(service.get("id", ""))
        raise ValueError(f"service '{service.get('id')}' already exists — use edit_service instead")
    except RecordNotFoundError:
        pass
    return _service_dict(storage.save_service(Service.model_validate(service)))


@mcp.tool()
def edit_service(id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update one or more fields on an existing service. Only include the fields you want to change."""
    try:
        existing = storage.get_service(id)
    except RecordNotFoundError:
        raise ValueError(f"no service with id '{id}'")
    except InvalidIdError:
        raise ValueError(f"'{id}' is not a valid service id")
    data = existing.model_dump(mode="json")
    data.update(updates)
    data["id"] = id
    updated = Service.model_validate(data)
    updated.created = existing.created
    return _service_dict(storage.save_service(updated))


@mcp.tool()
def delete_service(id: str) -> dict[str, str]:
    """Permanently delete a service."""
    try:
        storage.delete_service(id)
    except RecordNotFoundError:
        raise ValueError(f"no service with id '{id}'")
    except InvalidIdError:
        raise ValueError(f"'{id}' is not a valid service id")
    return {"deleted": id}


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


@mcp.tool()
def list_categories() -> list[dict[str, Any]]:
    """List all categories."""
    return [_category_dict(c) for c in storage.list_categories()]


@mcp.tool()
def add_category(category: dict[str, Any]) -> dict[str, Any]:
    """Create a new category. Requires 'id' and 'name'."""
    try:
        storage.get_category(category.get("id", ""))
        raise ValueError(f"category '{category.get('id')}' already exists")
    except RecordNotFoundError:
        pass
    return _category_dict(storage.save_category(Category.model_validate(category)))


@mcp.tool()
def delete_category(id: str) -> dict[str, str]:
    """Delete a category. Services that referenced it are unaffected — they just
    stop grouping onto a category page until re-pointed at a different category."""
    try:
        storage.delete_category(id)
    except RecordNotFoundError:
        raise ValueError(f"no category with id '{id}'")
    except InvalidIdError:
        raise ValueError(f"'{id}' is not a valid category id")
    return {"deleted": id}


# ---------------------------------------------------------------------------
# Derived views
# ---------------------------------------------------------------------------


@mcp.tool()
def search_servers() -> dict[str, list[dict[str, Any]]]:
    """List every server, each with the services running on it (derived from
    each service's server/hostname field, not separately stored)."""
    groups = aggregates.group_by_server(storage.list_services())
    return {server: [_service_dict(s) for s in services] for server, services in groups.items()}


@mcp.tool()
def search_domains() -> dict[str, list[dict[str, Any]]]:
    """List every domain/hostname in use, each with the services reachable there
    (derived from each service's public/home/tailscale URLs)."""
    groups = aggregates.group_by_domain(storage.list_services())
    return {domain: [_service_dict(s) for s in services] for domain, services in groups.items()}


@mcp.tool()
def list_projects() -> dict[str, list[dict[str, Any]]]:
    """List every docker-compose project, each with the services in it."""
    groups = aggregates.group_by_project(storage.list_services())
    return {project: [_service_dict(s) for s in services] for project, services in groups.items()}


@mcp.tool()
def get_stats() -> dict[str, int]:
    """Inventory counts: total/public/tailscale/home-only/dockerized services, servers, categories, etc."""
    return aggregates.compute_stats(storage.list_services(), storage.list_categories())


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
