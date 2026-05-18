# OpenClaw (Remote Service)

Cloud MCP endpoint — no local Docker container needed.

OpenClaw is a remote MCP service. Its URL is registered in `.mcp.json` automatically so Claude Code can reach it, but nothing runs locally.

## Setup

1. Sign up at https://openclaw.ai and obtain an API key.
2. Configure the key as instructed by OpenClaw (via HTTP header or query param — see their docs).
3. The endpoint `https://api.openclaw.ai/mcp` is already registered in `.mcp.json` after running `./install.sh`.

## Source

https://docs.openclaw.ai/
