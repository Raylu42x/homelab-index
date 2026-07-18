# Installation

## Requirements

- Docker Engine + Docker Compose plugin
- That's it — Python, FastAPI, and every dependency are installed inside the
  container. Nothing needs to be installed on the host.

## Steps

```bash
git clone <your-repo-url>
cd homelab-index
docker compose up -d --build
```

The app is now up on the port configured in `docker-compose.yml` (default
`8000`; change the left side of the `ports:` mapping if that port is already
taken on your host).

Visit it in a browser. There's no login screen — the app assumes something
in front of it (Cloudflare Access, a VPN, or nothing at all on a trusted LAN)
already handles authentication. See [Docker deployment](docker-deployment.md)
for putting it behind Cloudflare Tunnel + Access.

## Running without Docker (development)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
HOMELAB_DATA_DIR=./data uvicorn app.main:app --reload
```

Requires Python 3.13+.
