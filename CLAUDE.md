# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **self-hosted MCP (Model Context Protocol) servers management system** that runs multiple AI tool integrations behind Docker. The project provides:

- **9router**: An LLM API provider router (port 20128) for managing API keys
- **MCP Servers**: Individual tool/service containers exposed via HTTP/SSE at unique ports
- **Integration**: Automatic configuration for Claude Code (`.mcp.json`) and Gemini CLI (`~/.gemini/settings.json`)

The system uses Docker Compose to orchestrate services and Python scripts to manage installation, configuration, and lifecycle.

## Directory Structure

The main application lives in `mcp-servers/` with this layout:

- **config/profiles/**: Activation profiles (default, unity, all)
- **tools/**: Tool definitions (one folder per tool with config.json)
- **scripts/**: Installation and management automation (install.py, uninstall.py)
- **servers/**: Cloned git-sourced repos (gitignored)
- **docker-compose.yml**: Base stack (9router service)
- **docker-compose.override.yml**: Generated MCP services (gitignored)

Root level:
- **.mcp.json**: Generated Claude Code MCP config (gitignored)
- **GEMINI.md**: Full project instructions
- **.claude/**: Claude Code configuration
- **.gemini/**: Gemini CLI configuration

## Key Concepts

### Source Types

Each tool in `tools/<name>/config.json` specifies a `source` that determines deployment:

| Source | Behavior | Example |
|--------|----------|---------|
| **local** | Uses Dockerfile in `tools/<name>/` — no cloning | context7, gws-mcp |
| **git** | Shallow-clones repo, builds its Dockerfile | unity-mcp, windows-mcp |
| **image** | Pre-built Docker Hub image | atlassian, playwright |
| **remote** | Cloud endpoint (no local Docker service) | openclaw |
| **plugin** | Claude.ai plugin (in `~/.claude/settings.json`) | github, code-review |

### Profiles

Profiles in `config/profiles/*.json` list tools to activate:

- **default.json**: Recommended setup (context7, mcp-discord, atlassian, gws-mcp, openclaw, github, code-review)
- **unity.json**: Game dev focused (unity-mcp, context7, code-review)
- **all.json**: All available tools

### Configuration Files

Each tool's `tools/<name>/config.json` requires:
- `name`: Unique identifier (matches folder name)
- `source`: One of the source types above
- `port`: Host port (for local, git, image sources)

Source-specific fields:
- `repo`, `branch`, `dockerfile` (git)
- `image` (image)
- `url` (remote)
- `plugin_id` (plugin) — passed to `claude plugin install <plugin_id>`
- `local_path` (local) — path to the tool directory (default: `tools/<name>`)

Optional fields:
- `mcp_path`: MCP endpoint path (default: `/mcp`)
- `transport`: `http` (default) or `sse`
- `install_url`: Human-readable install URL for plugins (informational only)
- `environment`: Env vars with `${VAR}` substitution from `.env`
- `volumes`: Docker volume mounts
- `command`: Docker CMD override
- `platform`: OS allowlist (e.g., `["windows"]`)

## Common Commands

### Initial Setup

```bash
cd mcp-servers
./install.sh                                       # default profile
./install.sh --profile config/profiles/unity.json # Unity profile
cp env.template .env                              # fill in credentials
docker compose up -d --build                      # start services
docker compose logs -f                            # view logs
```

### Docker Compose Management

```bash
cd mcp-servers
docker compose build <service-name>               # rebuild
docker compose up -d <service-name>               # start one service
docker compose down <service-name>                # stop one service
docker compose down                               # stop all
docker compose logs -f <service-name>             # view logs for one
```

### Adding a New Tool

Use the **add-server** skill or manually:

```bash
cd mcp-servers
cp -r tools/_template tools/<name>
# Edit tools/<name>/config.json with source, port, and required fields
# Add Dockerfile if local source
# Add .env if credentials needed
# Add "<name>" to desired profile(s)
./install.sh
docker compose up -d --build
```

### Plugin Management

```bash
cd mcp-servers
python scripts/install-plugin-claude.py                          # default profile
python scripts/install-plugin-claude.py --profile config/profiles/unity.json
# Calls: claude plugin install <plugin_id> for each plugin in the profile
```

### Cleanup

```bash
cd mcp-servers
./uninstall.sh  # stop containers, remove repos, clear generated files
```

## Architecture

### Installation Flow

The `install.sh` script orchestrates:

1. **Profile Resolution**: Load `config/profiles/<profile>.json`, filter by OS platform
2. **Git Cloning**: Shallow-clone each git-sourced tool to `servers/<name>/`
3. **Docker Compose Generation**: Create `docker-compose.override.yml` with service definitions
4. **MCP Configuration**: Generate `.mcp.json` (project root + `mcp-servers/`)
5. **Environment Setup**: Merge per-tool `.env` files into `env.template`
6. **Plugin Installation**: Register Claude plugins via `install-plugin-claude.py`
7. **Per-Tool Setup**: Run `tools/<name>/install.py` if present (parallel)

### Runtime

- **9router** (port 20128): LLM API provider router
- **MCP Servers**: Individual containers at configured ports (e.g., context7 at 3000)
- **Claude Code**: Reads `.mcp.json` and connects to servers via HTTP
- **Gemini CLI**: Reads `~/.gemini/settings.json`

### Uninstallation

`uninstall.sh` orchestrates:
1. Stop Docker containers
2. Remove `servers/` directory
3. Clear `docker-compose.override.yml` and `env.template`
4. Empty `.mcp.json` files
5. Empty `.gemini/settings.json`
6. Remove plugin entries from `~/.claude/settings.json`

## Key Implementation Details

### Variable Substitution

- Tool configs support `${VAR}` syntax in environment and volumes
- Variables come from `.env` at compose time
- Example: `volumes: ["${GOOGLE_CREDENTIALS_FILE}:/app/credentials.json:ro"]`

### Multi-Profile Support

- Profiles are independent; each `./install.sh --profile <path>` overwrites generated files
- Only one profile active at a time
- Switch profiles by re-running `install.sh`

### Platform-Aware Filtering

- Tools can specify `"platform": ["linux", "darwin", "windows"]`
- Installer skips unavailable tools with warning
- Example: windows-mcp only on Windows

### Plugin vs. Docker

- **Docker services** (local, git, image): Full containers in Compose
- **Remote services**: Cloud endpoints, no local container
- **Plugins**: Claude.ai integrations installed via `claude plugin install` CLI

### Generated vs. Source-Controlled Files

Never edit these directly — they are regenerated by `install.sh`:

| File | Generated by |
|------|--------------|
| `mcp-servers/docker-compose.override.yml` | `scripts/install.py` |
| `.mcp.json` (root + `mcp-servers/`) | `scripts/install.py` |
| `mcp-servers/env.template` | `scripts/install.py` (merged from tool `.env` files) |

## Development Workflows

### Testing a Tool Addition

1. Create `tools/<name>/config.json` with source, port, required fields
2. Add `Dockerfile` if local
3. Add to profile
4. Run `./install.sh --profile config/profiles/default.json`
5. Verify `docker-compose.override.yml` generated
6. Check `.mcp.json` entry
7. `docker compose up -d --build`
8. `docker compose logs -f <name>`
9. Test: `curl http://localhost:<port><mcp_path>`

### Debugging

- Check Python errors in `install.py` output
- Verify JSON syntax in configs and profiles
- Ensure tool folder name matches `"name"` field
- For git: verify repo URL and branch
- For images: verify name and availability

### Modifying Tools

1. Edit `tools/<name>/config.json`
2. Update `Dockerfile` if local
3. For images: `docker image pull <image>`
4. Re-run `./install.sh`
5. Restart: `docker compose down && docker compose up -d --build`

## Environment Variables & Secrets

- `.env` files are gitignored (`**/*.env`)
- Each tool can have `.env` template
- `install.sh` merges active tool `.env` files into `env.template`
- Copy `env.template` to `.env` and fill credentials
- Variables substituted at compose time

## Integration with Claude Code

- `.mcp.json` at project root is auto-read by Claude Code
- After `install.sh`, reload Claude Code (`/reload` or restart)
- `.claude/settings.local.json` overrides which servers are enabled (see `enabledMcpjsonServers`, `disabledMcpjsonServers`)

## Tools Overview

| Name | Source | Purpose | Port |
|------|--------|---------|------|
| context7 | local | Library documentation | 3000 |
| unity-mcp | git | Unity Editor control | 8080 |
| gws-mcp | local | Google Workspace | 8100 |
| mcp-discord | local | Discord integration | 8085 |
| atlassian | image | Jira + Confluence | 9090 |
| playwright | image | Browser automation | 8931 |
| windows-mcp | git | Windows OS control (Windows-only) | 8200 |
| openclaw | remote | Cloud MCP endpoint | N/A |
| github | plugin | GitHub integration | N/A |
| code-review | plugin | Code-review plugin | N/A |

