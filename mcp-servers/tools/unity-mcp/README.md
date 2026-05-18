# Unity MCP

Git source: https://github.com/CoplayDev/unity-mcp (branch: beta)

Provides Unity Editor control tools to Claude via MCP: manage GameObjects, scenes, scripts, and more.

## Requirements

- The Unity Editor must be running with the **MCPForUnity** C# package installed in your project.
- The MCP server (this Docker container) connects to the Unity Editor over a local socket.

## Unity Editor setup

1. In your Unity project, install the `MCPForUnity` package (included in the repo under `MCPForUnity/`).
2. Enable the MCP server from the Unity Editor menu.
3. Start this container — it will connect automatically.

## Source

https://github.com/CoplayDev/unity-mcp
