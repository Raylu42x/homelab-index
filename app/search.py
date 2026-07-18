"""Simple, fast in-memory search over services.

The whole catalog is expected to be a few hundred entries at most, so a
linear scan with substring scoring is instant and needs no search index.
"""

from __future__ import annotations

from app.models import Service


def search_services(services: list[Service], query: str) -> list[Service]:
    query = query.strip().lower()
    if not query:
        return []

    scored: list[tuple[int, Service]] = []
    for service in services:
        score = 0
        name = service.name.lower()
        if query == name:
            score += 100
        elif name.startswith(query):
            score += 60
        elif query in name:
            score += 40

        if service.tags and any(query in t.lower() for t in service.tags):
            score += 25

        if service.category and query in service.category.lower():
            score += 15

        if query in service.search_blob():
            score += 5

        if score:
            scored.append((score, service))

    scored.sort(key=lambda pair: (-pair[0], pair[1].name.lower()))
    return [service for _, service in scored]
