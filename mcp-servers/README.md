# MCP Servers

A self-hosted collection of MCP (Model Context Protocol) tools running behind Docker. Each tool lives in its own `tools/<name>/` folder with a `config.json`, an optional `Dockerfile`, and an optional `.env` for credentials. Claude Code and Gemini CLI are configured automatically.

The base `docker-compose.yml` runs [9router](https://github.com/decolua/9router) for LLM API routing. An auto-generated `docker-compose.override.yml` adds the MCP server services on top.

## Prerequisites

- [Docker](https://www.docker.com/) with Compose
- Python 3
- Git

## Startup

```bash
# 1. Clone repos, generate configs, write env.template
./install.sh

# 2. Copy env.template to .env and fill in your values
cp env.template .env

# 3. Build images and start all containers
docker compose up -d --build

# 4. Reload Claude Code to pick up the updated .mcp.json
#    Use /reload in Claude Code, or restart it
```

## Install

```bash
./install.sh                                          # default profile
./install.sh --profile config/profiles/unity.json    # Unity game dev profile
./install.sh --profile config/profiles/all.json      # every tool
```

`install.sh` does:
1. Clones (or pulls) each git-sourced server into `servers/<name>/`
2. Generates `docker-compose.override.yml` with a service per active server
3. Writes `.mcp.json` to both `mcp-servers/` and the project root (Claude Code reads this)
4. Writes `.gemini/settings.json` for Gemini CLI
5. Merges per-tool `.env` files into `env.template` scoped to the active profile
6. Runs `scripts/install-plugin-claude.py` to write plugin entries into `~/.claude/settings.json`

## Uninstall

```bash
./uninstall.sh    # stop containers, remove servers/, clear generated files
```

## Profiles

Profiles live in `config/profiles/` and list tool names to activate. Each name maps to a `tools/<name>/config.json`.

| Profile | Tools |
|---|---|
| `default.json` | context7, mcp-discord, atlassian, gws-mcp, openclaw, github, code-review |
| `unity.json` | unity-mcp, context7 |
| `all.json` | every tool in the catalog |

## Adding a Tool

1. Create `tools/<name>/` — copy from `tools/_template/` for a starter
2. Edit `tools/<name>/config.json` — set `source` and source-specific fields (see table below)
3. Add `tools/<name>/Dockerfile` if `source` is `local`
4. Add `tools/<name>/.env` with placeholder values if credentials are needed
5. Add `"<name>"` to the relevant profile in `config/profiles/`
6. Run `./install.sh`

See `tools/_template/README.md` for the full field reference.

### Source types

| `source` | How it works | Compose output |
|---|---|---|
| `local` | Dockerfile in `tools/<name>/` | `build: context: ./tools/<name>` |
| `git` | Shallow-clone repo, build its Dockerfile | `build: context: ./servers/<name>` |
| `image` | Pull pre-built Docker Hub image | `image: <value>` |
| `remote` | Cloud endpoint — no Docker | `.mcp.json` entry only |
| `plugin` | Claude.ai plugin — no Docker | `~/.claude/settings.json` entry only |

### Key `config.json` fields

| Field | Source | Required | Description |
|---|---|---|---|
| `name` | all | yes | Unique identifier — matches the folder name |
| `source` | all | yes | See table above |
| `port` | local, git, image | yes | Host port to expose |
| `mcp_path` | local, git, image | no | MCP endpoint path (default: `/mcp`) |
| `repo` | git | yes | Git URL to clone |
| `branch` | git | no | Branch (default: `main`) |
| `image` | image | yes | Docker image reference |
| `url` | remote | yes | Cloud MCP endpoint URL |
| `install_url` | plugin | yes | Browser URL for manual installation |
| `mcp_config` | plugin | yes | MCP connection payload written to `~/.claude/settings.json` |
| `environment` | local, git, image | no | Env vars (`${VAR}` substitution from `.env`) |
| `volumes` | local, git, image | no | Volume mount strings |
| `platform` | all | no | OS allowlist — tool is skipped on other platforms |

## Plugins

Claude.ai plugins (e.g. GitHub, code-review) cannot run in Docker. The installer writes their `mcp_config` into `~/.claude/settings.json` automatically via `scripts/install-plugin-claude.py`.

You can also run the plugin installer standalone:
```bash
python scripts/install-plugin-claude.py
python scripts/install-plugin-claude.py --profile config/profiles/unity.json
```

## Remote Services

Cloud MCP endpoints like `openclaw` have no local Docker container. They appear in `.mcp.json` and `.gemini/settings.json` automatically but generate no compose service. See `tools/openclaw/README.md` for API key setup.

## File Structure

```
mcp-servers/
├── config/
│   └── profiles/
│       ├── default.json         # default active set
│       ├── unity.json           # Unity game dev
│       └── all.json             # everything
├── tools/                       # one folder per tool
│   ├── _template/
│   │   ├── config.json          # template for new tools
│   │   ├── .env                 # env template example
│   │   └── README.md            # field reference + howto
│   ├── context7/
│   │   ├── config.json
│   │   └── Dockerfile
│   ├── mcp-discord/
│   │   ├── config.json
│   │   ├── .env
│   │   └── Dockerfile
│   ├── atlassian/
│   │   ├── config.json
│   │   ├── .env
│   │   └── README.md
│   ├── playwright/
│   │   ├── config.json
│   │   └── README.md
│   ├── gws-mcp/
│   │   ├── config.json
│   │   ├── .env
│   │   ├── Dockerfile
│   │   └── README.md
│   ├── unity-mcp/
│   │   ├── config.json
│   │   └── README.md
│   ├── windows-mcp/
│   │   ├── config.json
│   │   └── README.md
│   ├── openclaw/
│   │   ├── config.json
│   │   ├── .env
│   │   └── README.md
│   ├── github/
│   │   ├── config.json
│   │   └── README.md
│   └── code-review/
│       ├── config.json
│       └── README.md
├── scripts/
│   ├── install.py               # main installer
│   ├── install-plugin-claude.py # writes plugins → ~/.claude/settings.json
│   └── uninstall.py
├── servers/                     # cloned server repos (gitignored)
├── docker-compose.yml           # base stack (9router)
├── docker-compose.override.yml  # generated MCP services (gitignored)
├── env.template                 # generated env var template (gitignored)
├── .mcp.json                    # generated Claude Code config (gitignored)
├── install.sh
└── uninstall.sh
```
