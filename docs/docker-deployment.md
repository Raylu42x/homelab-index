# Docker deployment

## Compose file

```yaml
services:
  homelab-index:
    build: .
    image: homelab-index:latest
    container_name: homelab-index
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - homelab-index-data:/data
    environment:
      - HOMELAB_DATA_DIR=/data

volumes:
  homelab-index-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data
```

`./data` is bind-mounted rather than a named Docker volume so the YAML files
show up as plain files next to the compose file — easy to `git diff`, easy
to edit directly, easy to back up with any generic file-based tool.

```bash
docker compose up -d
```

## Putting it behind Cloudflare

The app has **no built-in authentication** — it trusts whatever sits in
front of it completely. The intended setup:

```
Internet → Cloudflare DNS → Cloudflare Tunnel → Cloudflare Access → app
```

1. Create a Cloudflare Tunnel pointing at `http://homelab-index:8000` (or
   `http://<host-ip>:8000` if the tunnel daemon runs outside this compose
   network).
2. Add a public hostname for the tunnel, e.g. `index.yourdomain.com`.
3. Put a Cloudflare Access application in front of that hostname requiring
   your identity provider / email OTP / etc.
4. Never expose the container's port directly to the internet without Access
   in front of it — anyone who can reach `/settings` or `/api/services` can
   edit your inventory.

## File ownership

The compose file sets `user:` to match your host UID/GID (`id -u`/`id -g`)
so files the app writes through the UI or `/api` — new services, edits,
favorites — come out owned by you, not root. Skip this and everything
still works, but anything written through the app becomes root-owned and
unreadable/un-`git diff`-able from the host until you `chown` it back.

## Health check

The image ships a `HEALTHCHECK` hitting `GET /healthz`, so
`docker compose ps` and orchestrators that respect health checks (Portainer,
Watchtower, etc.) can tell if the app is actually serving requests, not just
that the process is alive.
