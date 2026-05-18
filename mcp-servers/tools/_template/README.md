# Adding a New Tool

Copy this folder to `tools/<your-tool-name>/`, then edit `config.json` and optionally add a `Dockerfile` and `.env`.

## `config.json` field reference

| Field | Source types | Required | Description |
|---|---|---|---|
| `name` | all | yes | Unique identifier — matches the folder name |
| `source` | all | yes | `local`, `git`, `image`, `remote`, or `plugin` |
| `description` | all | no | One-line description shown in logs |
| `port` | local, git, image | yes | Host port to expose |
| `mcp_path` | local, git, image | no | MCP endpoint path (default: `/mcp`) |
| `transport` | local, git, image | no | `http` (default) or `sse` |
| `local_path` | local | no | Build context path (default: `tools/<name>`) |
| `repo` | git | yes | Git URL to clone |
| `branch` | git | no | Branch (default: `main`) |
| `dockerfile` | git | no | Dockerfile path inside the repo (default: `Dockerfile`) |
| `image` | image | yes | Docker image reference (e.g. `mcp/playwright:latest`) |
| `url` | remote | yes | Cloud MCP endpoint URL |
| `install_url` | plugin | yes | Browser URL for manual installation |
| `mcp_config` | plugin | yes | MCP connection payload written to `~/.claude/settings.json` |
| `environment` | local, git, image | no | Env vars (supports `${VAR}` substitution) |
| `volumes` | local, git, image | no | List of volume mount strings |
| `platform` | all | no | Allowed OS list — server is skipped on others |
| `command` | local, git, image | no | Override container CMD |

## Source types

- **`local`** — Dockerfile lives in `tools/<name>/`. No cloning.
- **`git`** — Shallow-clone the repo, build from its Dockerfile.
- **`image`** — Pull a pre-built Docker Hub image. No build step.
- **`remote`** — Cloud endpoint. Written to `.mcp.json` only; no Docker service.
- **`plugin`** — Claude.ai plugin. Written to `~/.claude/settings.json` via `install-plugin-claude.py`.

## `mcp_config` for plugins

Two formats are supported:

```json
{ "type": "http", "url": "https://...", "headers": { "Authorization": "Bearer ${TOKEN}" } }
```

```json
{ "type": "stdio", "command": "npx", "args": ["-y", "some-package"], "env": {} }
```

## Steps to add a new tool

1. `cp -r tools/_template tools/<name>`
2. Edit `config.json` — set `name`, `source`, and source-specific fields.
3. Add a `Dockerfile` if `source` is `local`.
4. Add a `.env` with placeholder values if the tool needs credentials.
5. Add `"<name>"` to the relevant profile in `config/profiles/`.
6. Run `./install.sh` to verify.
