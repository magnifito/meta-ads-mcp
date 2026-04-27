# Meta Ads MCP

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for Meta Ads. Lets an LLM analyze, manage, and optimize Meta ad campaigns (Facebook, Instagram, etc.) through structured tool calls against the Meta Graph API.

> **Note:** Independent open-source project that uses Meta's public APIs. Meta, Facebook, Instagram, and other Meta brand names are trademarks of their respective owners.

This fork is maintained for **local-first** use. It runs as either:
- a **stdio** subprocess (for Claude Desktop / Claude Code / Cursor / etc.), or
- a **streamable-http** server (for self-hosted deploys behind a reverse proxy, e.g. Dokploy + Traefik).

There is no cloud relay — every request goes directly from your process to `graph.facebook.com`.

## Table of Contents

- [Quick Start (stdio)](#quick-start-stdio)
- [Authentication](#authentication)
- [Configuration](#configuration)
- [Hosted Deploy (Docker + Dokploy + Traefik)](#hosted-deploy-docker--dokploy--traefik)
- [Available Tools](#available-tools)
- [Testing](#testing)
- [Licensing](#licensing)
- [Privacy and Security](#privacy-and-security)
- [Troubleshooting](#troubleshooting)

## Quick Start (stdio)

Install from source:

```bash
pip install -e .
```

Provide a Meta token (see [Authentication](#authentication)) and run:

```bash
META_ACCESS_TOKEN="EAAB..." python -m meta_ads_mcp
```

Wire into Claude Code:

```bash
claude mcp add meta-ads \
  --env META_ACCESS_TOKEN=EAAB... \
  --env META_ADS_MCP_WRITE=true \
  -- python -m meta_ads_mcp
```

Or hand-edit `~/.claude.json`:

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "python",
      "args": ["-m", "meta_ads_mcp"],
      "env": {
        "META_ACCESS_TOKEN": "EAAB...",
        "META_ADS_MCP_WRITE": "true"
      }
    }
  }
}
```

Restart the client and verify with `/mcp` — `meta-ads` should be listed as connected.

## Authentication

Two modes. Pick one.

### 1. Direct System User token (recommended)

Mint a long-lived System User token in Meta Business Suite, export it, done:

```bash
export META_ACCESS_TOKEN="EAAB..."
export META_APP_SECRET="..."   # optional but strongly recommended (enables appsecret_proof signing)
```

The token is used as-is for every Graph API call. No OAuth round-trip.

### 2. Local OAuth flow

```bash
export META_APP_ID="<Meta App ID>"
export META_APP_SECRET="<Meta App secret>"   # required for long-lived-token exchange
python -m meta_ads_mcp --login
```

Or call the `get_login_link` MCP tool — the server starts a callback listener on `localhost:<port>/callback` and returns a clickable Facebook OAuth URL. Tokens cache to:

- macOS: `~/Library/Application Support/meta-ads-mcp/token_cache.json`
- Linux: `~/.config/meta-ads-mcp/token_cache.json`
- Windows: `%APPDATA%\meta-ads-mcp\token_cache.json`

If `META_ACCESS_TOKEN` is set it always takes precedence.

## Configuration

### Read-only by default

The server **defaults to read-only**. Mutating tools (create / update / upload on campaigns, adsets, ads, creatives, images, budget schedules) are hidden from `tools/list` and refused at call time unless `META_ADS_MCP_WRITE=true` is set. This prevents an LLM from changing live ad spend on a casual chat request.

### Environment variables

See [`.env.example`](.env.example) for a copy-paste template with notes. Most-used:

| Variable | Purpose |
| --- | --- |
| `META_ADS_MCP_WRITE` | `true`/`1`/`yes` to enable mutating tools. **Defaults to off.** |
| `META_ACCESS_TOKEN` | Meta System User access token. Used as-is for every API call. |
| `META_APP_ID` | Meta App ID for the local OAuth flow. Not needed when `META_ACCESS_TOKEN` is set. |
| `META_APP_SECRET` | Meta App secret. Enables `appsecret_proof` signing on every Graph API call. |
| `META_ADS_BM_IDS` | Comma-separated Business Manager IDs to scan via `client_ad_accounts` + `owned_ad_accounts` edges in `get_ad_accounts`. |
| `META_ADS_EXTRA_ACCOUNT_IDS` | Comma-separated extra `act_xxx` IDs to direct-fetch even when not in any BM edge. |
| `META_ADS_DISABLE_LOGIN_LINK` | Hides the `get_login_link` tool. Recommended for hosted deploys. |
| `META_ADS_DISABLE_CALLBACK_SERVER` | Disables the local OAuth callback listener. Recommended for hosted deploys. |
| `META_ADS_DISABLE_ADS_LIBRARY` | Hides `search_ads_archive`. |
| `META_ADS_ENABLE_REPORTS` | Registers `generate_report`. |
| `MCP_HTTP_PATH` | Mount path for streamable-http transport (default `/mcp`). The Dockerfile defaults this to `/meta`. |

## Hosted Deploy (Docker + Dokploy + Traefik)

The repo ships a [`Dockerfile`](Dockerfile) and [`docker-compose.yml`](docker-compose.yml) configured for Dokploy + Traefik. Default route: `https://mcp.<your-domain>/meta`.

### Multi-tenant model

The hosted server holds **no Meta token by default**. Each Claude Code client sends `Authorization: Bearer <meta-token>` per request. Tokens never persist on the server.

### Deploy

1. Push this repo to a git remote your Dokploy can reach.
2. Create a Dokploy app → build type **Docker Compose** → compose path `docker-compose.yml`.
3. Edit the `Host(...)` value in `docker-compose.yml` to your real domain.
4. Confirm Dokploy's Traefik cert resolver name matches (default `letsencrypt`; some installs differ).
5. Set env in Dokploy panel — minimum:
   ```
   META_ADS_MCP_WRITE=true
   META_ADS_DISABLE_LOGIN_LINK=1
   META_ADS_DISABLE_CALLBACK_SERVER=1
   ```
6. Deploy.
7. Smoke-test:
   ```bash
   curl -X POST https://mcp.<your-domain>/meta \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -H "Authorization: Bearer EAAB..." \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
   ```
   Should return a JSON tool list.

### Wire into Claude Code

```bash
claude mcp add meta-ads --transport http https://mcp.<your-domain>/meta \
  --header "Authorization: Bearer EAAB..."
```

### Run streamable-http directly (no Docker)

```bash
python -m meta_ads_mcp --transport streamable-http --host 0.0.0.0 --port 8080 --path /mcp
```

CLI flags: `--transport`, `--host`, `--port`, `--path`, `--sse-response`. `--path` also configurable via `MCP_HTTP_PATH` env.

## Available Tools

Discoverable via the standard MCP `tools/list` request. After connecting, ask your client to list tools or call `/mcp` in Claude Code.

Read tools (default): account / campaign / adset / ad / creative / insights getters, interest+demographic+geo search, ads library search.

Write tools (require `META_ADS_MCP_WRITE=true`): `create_campaign`, `create_adset`, `create_ad`, `create_ad_creative`, `create_budget_schedule`, `update_campaign`, `update_adset`, `update_ad`, `update_ad_creative`, `upload_ad_image`.

The full canonical list is enforced by [`meta_ads_mcp/core/write_gate.py`](meta_ads_mcp/core/write_gate.py); a drift-alarm test (`tests/test_write_gate.py::test_every_registered_tool_is_classified`) fails CI if a new tool is registered without classification.

## Testing

```bash
pip install -e '.[dev]'
pytest -q
```

448+ tests, ~90 s. End-to-end tests (`*_e2e.py`) are excluded by default and require a real Meta access token — opt in with `pytest -m e2e`.

## Licensing

[Business Source License 1.1](LICENSE) — Licensor: ARTELL SOLUÇÕES TECNOLÓGICAS LTDA.

- Use freely for individual and business purposes.
- Modify and customize.
- Redistribute.
- Cannot host as a service that competes with the Licensor's commercial offering.
- Auto-converts to Apache 2.0 on **2029-01-01**.

## Privacy and Security

- `META_ACCESS_TOKEN` lives in the process environment only.
- OAuth-obtained tokens cache to disk (paths above) as plain JSON. Delete the file to invalidate.
- HTTP-mode Bearer tokens are scoped to the request via Python `contextvars` — never persisted, never logged.
- No token material leaves your machine except in outbound calls to Meta's Graph API.

## Troubleshooting

- **`Authentication Required`**: confirm `META_ACCESS_TOKEN` (or `META_APP_ID` + `META_APP_SECRET`) is set in the environment the server actually sees. Restart Claude Code after env changes.
- **Write tool missing from `tools/list`**: `META_ADS_MCP_WRITE` is unset or not truthy. Set to `true`/`1`/`yes`.
- **Hosted: 404 on `/meta`**: PathPrefix collision or label conflict between hand-written compose labels and Dokploy-generated labels. Pick one source of truth.
- **Hosted: 502**: container crashed or wrong service port. Check `docker logs <container>` and the Traefik service `loadbalancer.server.port=8080` label.
- **Hosted: TLS handshake fails**: cert resolver name in compose doesn't match Dokploy's Traefik config. Check `docker exec dokploy-traefik cat /etc/dokploy/traefik/traefik.yml`.
- **Cache file corrupt**: remove the cached token file and re-run `--login`.
