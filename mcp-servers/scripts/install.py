import json, subprocess, os, sys


def usage():
    print("Usage: install.sh [--only <name1,name2,...>]")
    print("       install.sh          # clone/update all servers")
    print("       install.sh --only unity-mcp,other-server")
    sys.exit(1)


# Parse optional --only flag
only = None
args = sys.argv[1:]
if args:
    if args[0] == "--only" and len(args) == 2:
        only = set(args[1].split(","))
    else:
        usage()

with open("config/mcp-servers.json") as f:
    config = json.load(f)

servers = config.get("servers", [])
if not servers:
    print("No servers defined in mcp-servers.json")
    sys.exit(0)

if only:
    unknown = only - {s["name"] for s in servers}
    if unknown:
        print(f"Unknown servers: {', '.join(unknown)}")
        sys.exit(1)
    servers_to_clone = [s for s in servers if s["name"] in only]
else:
    servers_to_clone = servers

os.makedirs("servers", exist_ok=True)

# Clone or update each server
for s in servers_to_clone:
    name = s["name"]
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

# Generate docker-compose.override.yml for ALL configured servers
# (so services are always defined even if some repos weren't re-cloned this run)
lines = ["services:"]
for s in servers:
    name = s["name"]
    port = s["port"]
    dockerfile = s.get("dockerfile", "Dockerfile")
    command = s.get("command", "")

    lines += [
        f"  {name}:",
        f"    build:",
        f"      context: ./servers/{name}",
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
        "type": "http",
        "url": f"http://localhost:{s['port']}{s.get('mcp_path', '/mcp')}",
    }

with open(".mcp.json", "w") as f:
    json.dump({"mcpServers": mcp_servers}, f, indent=2)
    f.write("\n")
print("Updated .mcp.json")

print("\nDone. Run 'docker compose up -d --build' to start the stack.")
