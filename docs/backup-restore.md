# Backup & restore

The entire application state is the `data/` directory — plain YAML files,
nothing in a database. There's nothing else to back up.

## Backup

The primary backup mechanism is git, since `data/` is already tracked:

```bash
git add data/
git commit -m "Update service inventory"
git push
```

For a point-in-time snapshot outside git (e.g. as part of a broader host
backup job):

```bash
tar czf homelab-index-backup-$(date +%F).tar.gz data/
```

Fold that into whatever already backs up the rest of the host — there's no
special-case handling needed, it's just files.

## Restore

From git:

```bash
git clone <your-repo-url>
cd homelab-index
docker compose up -d
```

From a tarball, onto a fresh checkout of the code:

```bash
git clone <your-repo-url>
cd homelab-index
tar xzf /path/to/homelab-index-backup-2026-07-17.tar.gz
docker compose up -d
```

No database migrations, no import step — the YAML files on disk *are* the
state. If `docker compose up` starts and the pages render your services,
the restore is complete.
