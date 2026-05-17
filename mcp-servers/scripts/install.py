import json, subprocess, os, sys


def usage():
    print("Usage: install.sh [--config <path>]")
    print("       install.sh                               # install all servers")
    print("       install.sh --config config/unity.json   # use a specific config file")
    sys.exit(1)


def build_config(s):
    """Return (build_context, dockerfile) for docker-compose."""
    if s.get("source") == "local":
        return f"./{s['local_path']}", "Dockerfile"
    return f"./servers/{s['name']}", s.get("dockerfile", "Dockerfile")


# Parse flags
config_file = "config/mcp-servers.json"
args = sys.argv[1:]
while args:
    if args[0] == "--config" and len(args) >= 2:
        config_file = args[1]
        args = args[2:]
    else:
        usage()

with open(config_file) as f:
    config = json.load(f)

servers = config.get("servers", [])
if not servers:
    print("No servers defined in", config_file)
    sys.exit(0)

servers_to_clone = servers

os.makedirs("servers", exist_ok=True)

# Clone or update each git-sourced server
for s in servers_to_clone:
    name = s["name"]
    if s.get("source") == "local":
        print(f"[{name}] local source, skipping clone.")
        continue

    repo = s["repo"]
    branch = s.get("branch", "main")
    dest = os.path.join("servers", name)

    if os.path.isdir(os.path.join(dest, ".git")):
        print(f"[{name}] already cloned — pulling latest...")
        subprocess.run(["git", "-C", dest, "pull"], check=True)
    else:
        print(f"[{name}] cloning {repo} (branch: {branch})...")
        subprocess.run(
            ["git", "clone", "-b", branch, "--depth", "1", repo, dest],
            check=True,
        )

# Generate docker-compose.override.yml for ALL servers in this config
lines = ["services:"]
for s in servers:
    name = s["name"]
    port = s["port"]
    command = s.get("command", "")
    context, dockerfile = build_config(s)

    lines += [
        f"  {name}:",
        f"    build:",
        f"      context: {context}",
        f"      dockerfile: {dockerfile}",
        f"    container_name: {name}",
        f"    ports:",
        f'      - "{port}:{port}"',
    ]
    if command:
        lines.append(f"    command: {command}")
    lines.append(f"    restart: unless-stopped")
    lines.append("")

with open("docker-compose.override.yml", "w") as f:
    f.write("\n".join(lines))
print("Generated docker-compose.override.yml")

# Regenerate .mcp.json
mcp_servers = {}
for s in servers:
    mcp_servers[s["name"]] = {
        "type": s.get("transport", "http"),
        "url": f"http://localhost:{s['port']}{s.get('mcp_path', '/mcp')}",
    }

mcp_json = json.dumps({"mcpServers": mcp_servers}, indent=2) + "\n"

with open(".mcp.json", "w") as f:
    f.write(mcp_json)
print("Updated mcp-servers/.mcp.json")

# Also write to project root so Claude Code picks it up automatically
root_mcp = os.path.join("..", ".mcp.json")
with open(root_mcp, "w") as f:
    f.write(mcp_json)
print(f"Updated {os.path.normpath(root_mcp)} (project root — Claude Code reads this)")

print("\nDone. Run 'docker compose up -d --build' to start the stack.")
