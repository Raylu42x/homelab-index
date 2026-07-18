# Updating

```bash
git pull
docker compose up -d --build
```

`data/` lives outside the image (bind-mounted), so rebuilding the image
never touches your services, categories, or settings.

## Content updates (the common case)

No rebuild needed at all. Add, edit, or delete a YAML file under `data/`
and refresh the browser — the UI reads the files fresh on every request.

## Checking what changed

Since `data/` is git-tracked, a normal `git log -p -- data/` or
`git diff` shows exactly what inventory changes happened over time —
services added, decommissioned, moved to a new server, etc.
