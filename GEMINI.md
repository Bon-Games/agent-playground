# MCP Servers Project Instructions

This project manages a local stack of MCP (Model Context Protocol) servers running behind Docker. It automates the setup, configuration, and integration with Claude Code.

## Project Overview

- **Purpose:** Provide a centralized management system for multiple MCP servers, allowing them to be easily deployed and connected to Claude Code.
- **Core Components:**
  - **9router:** An AI provider router (running on port 20128) used for managing LLM API keys and routing.
  - **MCP Servers:** Individual tools/services exposed via HTTP/SSE.
- **Technologies:** Docker, Docker Compose, Python, Shell scripts, MCP.

## File Structure Highlights

- `mcp-servers/config/mcp-servers.json`: The source of truth for server definitions.
- `mcp-servers/dockerfiles/`: Contains Dockerfiles for servers with `source: local`.
- `mcp-servers/scripts/`: Python logic for installation (`install.py`) and uninstallation (`uninstall.py`).
- `mcp-servers/docker-compose.yml`: The base Docker Compose file (runs 9router).
- `mcp-servers/docker-compose.override.yml`: Generated file containing the MCP server services (gitignored).
- `.mcp.json`: Generated Claude Code configuration. Updated in both the `mcp-servers/` directory and the project root (`../`).

## Key Commands

### Setup and Installation

```bash
cd mcp-servers

# Install all servers from the default config
./install.sh

# Install using a specific configuration file
./install.sh --config config/my-config.json
```

The `install.sh` script:
1. Clones/pulls git-based servers into `servers/`.
2. Generates `docker-compose.override.yml`.
3. Updates `.mcp.json` in `mcp-servers/` and the project root (`../`).

### Running the Stack

```bash
# Build and start all containers in the background
docker compose up -d --build

# View logs
docker compose logs -f
```

### Uninstallation and Cleanup

```bash
# Stop containers and remove generated files/cloned repos
./uninstall.sh
```

## Development Conventions

### Adding a New Server (Agent Skill)

For an automated workflow to add new servers from GitHub or Docker Hub, use the **`add-server`** skill. You can trigger this by asking the agent to "add a new MCP server".

The skill definition is located at [`.gemini/skills/add-server/SKILL.md`](.gemini/skills/add-server/SKILL.md) and handles:
- **GitHub Links:** Automatic git-sourced server configuration.
- **Docker Hub Links:** Automated Dockerfile generation for local-sourced servers.
- **Port Management:** Unique port assignment and conflict checking.
- **Verification:** Step-by-step testing instructions.

---

### Integration with Claude Code

- Claude Code automatically reads `.mcp.json` from the project root.
- The `install.sh` script ensures this file is always up-to-date based on the `mcp-servers.json` configuration.
- Servers are typically exposed via HTTP at `http://localhost:<port>/mcp`.
