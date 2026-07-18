# Connecting an AI agent over MCP

`docker-compose.yml` includes an optional second container,
`homelab-index-mcp`, running an MCP server (streamable-http transport) on
port 8001. It shares the same `/data` directory as the web app — no HTTP
hop between them, both just read/write the YAML directly. Remove that
service from the compose file if you don't want it.

Like the rest of the app, it has **no authentication of its own**. Expose
it only on a trusted network — a VPN/tailnet (Tailscale, WireGuard) or a
LAN you trust, never publicly.

**Endpoint:** `http://<your-host>:8001/mcp`

## Tools it exposes

- `search_services`, `list_services`, `get_service`
- `add_service`, `edit_service`, `delete_service`
- `list_categories`, `add_category`, `delete_category`
- `search_servers`, `search_domains`, `list_projects` — the derived views
- `get_stats`

## Claude Code (CLI)

```bash
claude mcp add --transport http homelab-index http://<your-host>:8001/mcp
```

`claude mcp list` confirms it connected. Then just ask things like "what
services are on my NAS" or "add jellyfin as a new service" — Claude calls
the tools above.

## Claude Desktop

Settings → Connectors → Add custom connector, pointed at
`http://<your-host>:8001/mcp`. On older versions, edit
`claude_desktop_config.json` directly:

```json
{
  "mcpServers": {
    "homelab-index": {
      "type": "http",
      "url": "http://<your-host>:8001/mcp"
    }
  }
}
```

Exact key names have shifted between Desktop versions — prefer the UI if
it's available.

## Verifying it's working

```bash
docker logs homelab-index-mcp
```

should show `Uvicorn running on http://0.0.0.0:8001` with no errors.
