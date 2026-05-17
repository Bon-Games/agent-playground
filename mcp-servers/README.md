# MCP Servers

Manages a local stack of MCP (Model Context Protocol) servers running behind Docker. Servers are defined in `config/mcp-servers.json`, cloned or built from local Dockerfiles, and exposed over HTTP so Claude Code can connect to them.

The base `docker-compose.yml` runs [9router](https://github.com/decolua/9router), an AI provider router for managing LLM API keys and routing across providers. An auto-generated `docker-compose.override.yml` adds the MCP server services on top. The two are independent — 9router handles LLM API calls, while the MCP servers expose tools directly to Claude Code.

`install.sh` writes `.mcp.json` to both this directory and the **project root** (`../`). Claude Code reads `.mcp.json` from the project root automatically, so no manual Claude config changes are ever needed.

## Prerequisites

- [Docker](https://www.docker.com/) with Compose
- Python 3
- Git

## Startup

```bash
# 1. Clone/pull server repos and generate config files
./install.sh

# 2. Build images and start all containers
docker compose up -d --build

# 3. Reload Claude Code to pick up the updated .mcp.json
#    Use /reload in Claude Code, or restart it
```

The servers will be available at their configured ports (e.g. `http://localhost:8080/mcp`). Claude Code reads the project-root `.mcp.json` on startup and connects automatically.

## Install

```bash
./install.sh                              # install all servers from default config
./install.sh --config config/unity.json  # use a specific config file
```

`install.sh` does three things:

1. Clones (or pulls) each git-sourced server repo into `servers/<name>/`
2. Generates `docker-compose.override.yml` with a build service per server
3. Writes `.mcp.json` to both `mcp-servers/` and the project root

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

After editing the config:

```bash
./install.sh
docker compose up -d --build
# Then reload Claude Code to pick up the new server
```

## File Structure

```
mcp-servers/
├── config/
│   └── mcp-servers.json         # server definitions (source of truth)
├── dockerfiles/                 # Dockerfiles for local-sourced servers
│   └── context7/
│       └── Dockerfile
├── scripts/
│   ├── install.py               # install logic
│   └── uninstall.py             # uninstall logic
├── servers/                     # cloned server repos (gitignored)
├── docker-compose.yml           # base stack (9router)
├── docker-compose.override.yml  # generated MCP services (gitignored)
├── .mcp.json                    # generated Claude Code config (gitignored)
├── install.sh
└── uninstall.sh
```

The project root also gets a `.mcp.json` (written by `install.sh`) — that is the file Claude Code actually reads.
