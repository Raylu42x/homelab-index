"""Pydantic data models for services, categories, and settings."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Status = Literal["online", "offline", "maintenance", "unknown"]


class Service(BaseModel):
    id: str
    name: str
    description: str | None = None
    category: str | None = None
    subcategory: str | None = None
    icon: str | None = None
    tags: list[str] = Field(default_factory=list)
    favorite: bool = False
    status: Status = "unknown"

    public_url: str | None = None
    tailscale_url: str | None = None
    home_url: str | None = None
    localhost_url: str | None = None
    docker_address: str | None = None

    hostname: str | None = None
    ip: str | None = None
    server: str | None = None
    docker_container: str | None = None
    docker_compose_project: str | None = None

    github_repository: str | None = None
    documentation: str | None = None
    notes: str | None = None
    owner: str | None = None
    dependencies: list[str] = Field(default_factory=list)

    created: datetime | None = None
    updated: datetime | None = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError(
                "id must be a non-empty slug of letters, numbers, '-' or '_'"
            )
        return v

    def access_methods(self) -> list[tuple[str, str]]:
        """Ordered (label, url) pairs for whichever access methods are set."""
        methods = [
            ("Public", self.public_url),
            ("Home", self.home_url),
            ("Tailscale", self.tailscale_url),
            ("Docker", self.docker_address),
            ("Localhost", self.localhost_url),
        ]
        return [(label, url) for label, url in methods if url]

    def search_blob(self) -> str:
        """Lowercased blob of every searchable field."""
        parts = [
            self.name,
            self.description or "",
            self.category or "",
            self.subcategory or "",
            self.notes or "",
            self.hostname or "",
            self.docker_container or "",
            self.server or "",
            " ".join(self.tags),
            self.public_url or "",
            self.home_url or "",
            self.tailscale_url or "",
            self.localhost_url or "",
            self.docker_address or "",
        ]
        return " ".join(parts).lower()


class Subcategory(BaseModel):
    id: str
    name: str
    description: str | None = None


class Category(BaseModel):
    id: str
    name: str
    description: str | None = None
    icon: str | None = None
    order: int = 100
    subcategories: list[Subcategory] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError(
                "id must be a non-empty slug of letters, numbers, '-' or '_'"
            )
        return v


class Page(BaseModel):
    id: str
    title: str
    content: str = ""
    order: int = 100

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError(
                "id must be a non-empty slug of letters, numbers, '-' or '_'"
            )
        return v


class Settings(BaseModel):
    site_name: str = "Homelab Index"
    tagline: str = "The operating system for the homelab."
    domain: str | None = None
    timezone: str = "UTC"
