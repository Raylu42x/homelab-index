"""Derived views over services: servers, domains, projects, stats.

Nothing here is stored separately — servers/domains/projects are inferred
from service records so there is zero duplicated information.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.models import Category, Service


def group_by_server(services: list[Service]) -> dict[str, list[Service]]:
    groups: dict[str, list[Service]] = {}
    for service in services:
        key = service.server or service.hostname
        if not key:
            continue
        groups.setdefault(key, []).append(service)
    return dict(sorted(groups.items(), key=lambda kv: kv[0].lower()))


def _extract_domain(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url if "://" in url else f"//{url}")
    return parsed.hostname


def group_by_domain(services: list[Service]) -> dict[str, list[Service]]:
    groups: dict[str, list[Service]] = {}
    for service in services:
        domains = {
            _extract_domain(u)
            for u in (service.public_url, service.home_url, service.tailscale_url)
        }
        for domain in domains:
            if domain:
                groups.setdefault(domain, []).append(service)
    return dict(sorted(groups.items(), key=lambda kv: kv[0].lower()))


def group_by_project(services: list[Service]) -> dict[str, list[Service]]:
    groups: dict[str, list[Service]] = {}
    for service in services:
        key = service.docker_compose_project
        if not key:
            continue
        groups.setdefault(key, []).append(service)
    return dict(sorted(groups.items(), key=lambda kv: kv[0].lower()))


def compute_stats(services: list[Service], categories: list[Category]) -> dict[str, int]:
    return {
        "total_services": len(services),
        "public_services": sum(1 for s in services if s.public_url),
        "tailscale_services": sum(1 for s in services if s.tailscale_url),
        "home_only_services": sum(
            1 for s in services if s.home_url and not s.public_url
        ),
        "docker_services": sum(1 for s in services if s.docker_container),
        "servers": len(group_by_server(services)),
        "categories": len(categories),
        "online": sum(1 for s in services if s.status == "online"),
        "favorites": sum(1 for s in services if s.favorite),
    }


def recently_updated(services: list[Service], limit: int = 8) -> list[Service]:
    with_dates = [s for s in services if s.updated is not None]
    with_dates.sort(key=lambda s: s.updated, reverse=True)
    return with_dates[:limit]
