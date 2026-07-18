# Data model

Nothing is hardcoded into templates — the whole UI is generated from YAML
under `data/`. Editing a file and refreshing the page is the only "deploy"
step for a content change.

## Folder structure

```
data/
├── services/
│   ├── <id>.yaml           # one file per service
│   └── example-service.yaml
├── categories/
│   └── <id>.yaml           # one file per category
├── pages/
│   └── <id>.yaml           # free-form documentation pages
└── settings.yaml
```

Every `<id>` must be a slug of letters, numbers, `-`, or `_` — it's also the
filename and the URL segment (`/services/<id>`, `/categories/<id>`,
`/docs/<id>`), and it's validated on every read/write to rule out path
traversal.

## Services (`data/services/<id>.yaml`)

Only `id` and `name` are required. Every other field is optional — a field
that's left out just doesn't render anywhere, instead of showing up blank.

```yaml
id: gitea
name: Gitea
description: Self-hosted git server.
category: development       # matches a category id, see below
subcategory: null
icon: "🍵"                   # any emoji or short string
tags: [git, self-hosted]
favorite: true
status: online               # online | offline | maintenance | unknown

# Access methods — show up on the service page for whichever are set.
public_url: null             # reachable from the internet
tailscale_url: null          # reachable over your tailnet
home_url: https://gitea.example.com   # reachable on the LAN
localhost_url: null          # reachable only from the host itself
docker_address: null         # e.g. gitea:3000, for other containers on the same network

# Infra metadata — purely informational, nothing enforces these.
hostname: gitea.example.com
ip: null
server: nas-01
docker_container: gitea
docker_compose_project: gitea

github_repository: null
documentation: null
notes: "SSH on port 2222."
owner: bennett
dependencies: []            # ids of other services this one depends on

# Set automatically on save — leave these out when hand-authoring a file.
created: null
updated: null
```

See `data/services/example-service.yaml` for every field populated with a
placeholder value — copy it, rename it, and edit.

## Categories (`data/categories/<id>.yaml`)

```yaml
id: development
name: Development
description: Git hosting, CI, and tools used to build everything else.
icon: "🛠️"
order: 20                   # lower sorts first on the Categories page
subcategories:
  - id: ci
    name: CI/CD
```

A service's `category` field is just a string; there's no hard foreign key.
An unmatched category still renders fine on the service page, it just won't
group onto a dedicated category page.

## Pages (`data/pages/<id>.yaml`)

Shown under the "Documentation" nav item — for runbooks, notes, or anything
else worth surfacing inside the portal itself rather than an external wiki.

```yaml
id: adding-services
title: Adding a service
order: 10
content: |
  Plain text, rendered with line breaks preserved and HTML escaped.
```

## Settings (`data/settings.yaml`)

```yaml
site_name: Homelab Index
tagline: The operating system for the homelab.
domain: index.example.com
timezone: UTC
```

Editable from the Settings page in the UI, or by hand.

## Servers, Domains, Projects — derived, not stored

These three nav items have **no corresponding YAML files**. They're computed
at request time from fields already on each service
(`app/aggregates.py`):

- **Servers** groups services by `server` (falling back to `hostname`).
- **Domains** groups services by the hostname parsed out of
  `public_url` / `home_url` / `tailscale_url`.
- **Projects** groups services by `docker_compose_project`.

This is deliberate: the plan calls for "zero duplicated information," so
anything derivable from a service's own fields is derived, never
hand-maintained as a second copy.

## Editing surfaces

1. **YAML directly** — the primary workflow, especially for an AI agent
   editing the repo.
2. **The UI** — favoriting and the Settings form write back through the same
   storage layer.
3. **The JSON API** under `/api` (`/api/services`, `/api/categories`,
   `/api/pages`, `/api/settings`, `/api/stats`) — full CRUD, and the layer
   future MCP tools (search/add/edit/delete service, list/create category,
   etc.) are meant to call into. It carries no authentication of its own —
   same as the rest of the app, it relies entirely on whatever sits in front
   (see [Docker deployment](docker-deployment.md)).
