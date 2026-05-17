# MCP Servers

Manages a local stack of MCP (Model Context Protocol) servers running behind Docker. Servers are defined in config JSON files (default: `config/mcp-servers.json`), cloned or built from local Dockerfiles, and exposed over HTTP so Claude Code can connect to them.

The base `docker-compose.yml` runs [9router](https://github.com/decolua/9router) as a reverse proxy. An auto-generated `docker-compose.override.yml` adds the MCP server services on top.

## Prerequisites

- [Docker](https://www.docker.com/) with Compose
- Python 3
- Git

## Quick Start

```bash
# 1. Clone and build all servers
./install.sh

# 2. Start the stack
docker compose up -d --build
```

Claude Code will pick up `.mcp.json` automatically and connect to the running servers.

## Install

```bash
./install.sh                                    # install all servers from default config
./install.sh --config config/unity.json        # use a specific config file
```

`install.sh` does three things:

1. Clones (or pulls) each git-sourced server repo into `servers/<name>/`
2. Generates `docker-compose.override.yml` with a build service per server
3. Writes `.mcp.json` with the endpoint for each server

You can maintain multiple config files (e.g. `config/unity.json`, `config/ai-tools.json`) to group related servers and install them independently.

## Uninstall

```bash
./uninstall.sh    # stop all containers, remove servers/, clear generated files
```

## Adding a Server

Two source types are supported: `git` (default) for repos that provide their own Dockerfile, and `local` for servers whose Dockerfile lives in this repo under `dockerfiles/`.

**Git-sourced server** — clone a remote repo and build from it:

```json
{
  "name": "my-server",
  "repo": "https://github.com/org/my-server",
  "branch": "main",
  "dockerfile": "Dockerfile",
  "port": 8081,
  "mcp_path": "/mcp",
  "command": ""
}
```

**Local-sourced server** — Dockerfile lives in `dockerfiles/<name>/`:

```json
{
  "name": "my-server",
  "source": "local",
  "local_path": "dockerfiles/my-server",
  "port": 8081,
  "transport": "sse",
  "mcp_path": "/sse"
}
```

| Field | Applies to | Required | Description |
|---|---|---|---|
| `name` | both | yes | Unique identifier, used as the Docker container name |
| `source` | both | no | `"git"` (default) or `"local"` |
| `repo` | git | yes | Git URL to clone |
| `branch` | git | no | Branch to clone (default: `main`) |
| `dockerfile` | git | no | Path to Dockerfile inside the repo (default: `Dockerfile`) |
| `local_path` | local | yes | Path to the directory containing the Dockerfile |
| `port` | both | yes | Host port to expose |
| `transport` | both | no | MCP transport type: `"http"` (default) or `"sse"` |
| `mcp_path` | both | no | Path for the MCP endpoint (default: `/mcp`) |
| `command` | both | no | Override the container `CMD` |

Then run `./install.sh --only my-server && docker compose up -d --build my-server`.

## File Structure

```
mcp-servers/
├── config/
│   └── mcp-servers.json       # server definitions (source of truth)
├── dockerfiles/               # Dockerfiles for local-sourced servers
│   └── context7/
│       └── Dockerfile
├── scripts/
│   ├── install.py             # install logic
│   └── uninstall.py           # uninstall logic
├── servers/                   # cloned server repos (gitignored)
├── docker-compose.yml         # base stack (9router)
├── docker-compose.override.yml  # generated MCP services (gitignored)
├── .mcp.json                  # generated Claude Code config (gitignored)
├── install.sh
└── uninstall.sh
```
