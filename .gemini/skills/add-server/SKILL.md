---
name: add-server
description: Procedural workflow for adding new MCP (Model Context Protocol) servers to the local stack via GitHub or Docker Hub. Triggered when the user wants to "add a server", "add mcp server", or "extend mcp stack".
---

# Add MCP Server Task

This task automates the addition of a new MCP server to the configuration and ensures it is ready for deployment.

## Inputs
- **Source Link:** A URL to a GitHub repository or a Docker Hub image page.
- **Config File:** The path to the configuration file (default: `mcp-servers/config/mcp-servers.json`).
- **Server Name:** (Optional) A custom name for the server.
- **Port:** (Optional) A specific port to assign.

## Process

### 1. Analyze Source
- **If GitHub Link:**
  - Identify the repository URL.
  - Determine if it's a "git-sourced" server (standard flow).
- **If Docker Hub Link:**
  - Use `web_fetch` to read the image details and usage instructions.
  - Generate a `Dockerfile` under `mcp-servers/dockerfiles/<server-name>/`.
  - Determine if it's a "local-sourced" server pointing to the new Dockerfile.

### 2. Configuration Update
- **Port Assignment:**
  - Scan the config file for existing ports.
  - Assign a new, unique port (e.g., starting from 8080 or 3000, depending on context).
  - **Conflict Check:** Explicitly check if the requested/assigned port is already in use by another server in the config. Highlight any conflicts.
- **Update JSON:**
  - Add the server entry to the `servers` array in the specified config file.

### 3. Execution
- Run `./mcp-servers/install.sh --config <config-file>` to regenerate the stack.

## Testing Instructions
After adding the server, perform the following steps:
1.  **Start the Stack:**
    ```bash
    cd mcp-servers
    docker compose up -d --build <server-name>
    ```
2.  **Verify Port Connectivity:**
    - Check if the port is listening: `netstat -ano | findstr :<port>` (Windows) or `lsof -i :<port>` (Unix).
3.  **Check Logs:**
    ```bash
    docker compose logs -f <server-name>
    ```
4.  **Validate MCP Connection:**
    - Use the generated URL in Claude Code or an MCP inspector tool.
    - URL: `http://localhost:<port><mcp_path>` (usually `/mcp`).

## Verification Commands
- `gemini mcp list`: Verify if the server is recognized by the CLI (if added to Claude/Gemini config).
- `docker ps`: Ensure the container is running and healthy.
