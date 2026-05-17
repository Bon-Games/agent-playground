import json, subprocess, os, sys, shutil


def usage():
    print("Usage: uninstall.sh [--only <name1,name2,...>] [--remove-images]")
    print("       uninstall.sh                       # stop & remove all server dirs")
    print("       uninstall.sh --only unity-mcp      # remove only specific servers")
    print("       uninstall.sh --remove-images       # also remove Docker images")
    sys.exit(1)


only = None
remove_images = False
args = sys.argv[1:]
while args:
    if args[0] == "--remove-images":
        remove_images = True
        args = args[1:]
    elif args[0] == "--only" and len(args) >= 2:
        only = set(args[1].split(","))
        args = args[2:]
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
    servers_to_remove = [s for s in servers if s["name"] in only]
else:
    servers_to_remove = servers

removing_all = only is None

# Stop docker compose stack (only when removing everything)
if removing_all:
    compose_args = ["docker", "compose", "down"]
    if remove_images:
        compose_args += ["--rmi", "all"]
    print("Stopping Docker Compose stack...")
    subprocess.run(compose_args, check=False)
else:
    # Stop only the selected services
    names = [s["name"] for s in servers_to_remove]
    compose_args = ["docker", "compose", "stop"] + names
    print(f"Stopping services: {', '.join(names)}...")
    subprocess.run(compose_args, check=False)
    subprocess.run(["docker", "compose", "rm", "-f"] + names, check=False)
    if remove_images:
        for name in names:
            subprocess.run(["docker", "rmi", name], check=False)

# Remove cloned server directories
for s in servers_to_remove:
    name = s["name"]
    dest = os.path.join("servers", name)
    if os.path.isdir(dest):
        print(f"[{name}] removing {dest}...")
        shutil.rmtree(dest)
    else:
        print(f"[{name}] directory not found, skipping.")

if removing_all:
    # Remove generated files
    for path in ("docker-compose.override.yml",):
        if os.path.exists(path):
            os.remove(path)
            print(f"Removed {path}")

    # Clear .mcp.json
    with open(".mcp.json", "w") as f:
        json.dump({"mcpServers": {}}, f, indent=2)
        f.write("\n")
    print("Cleared .mcp.json")
else:
    # Regenerate docker-compose.override.yml and .mcp.json without removed servers
    remaining = [s for s in servers if s["name"] not in {r["name"] for r in servers_to_remove}]

    lines = ["services:"]
    for s in remaining:
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
    print("Regenerated docker-compose.override.yml")

    mcp_servers = {}
    for s in remaining:
        mcp_servers[s["name"]] = {
            "type": "http",
            "url": f"http://localhost:{s['port']}{s.get('mcp_path', '/mcp')}",
        }
    with open(".mcp.json", "w") as f:
        json.dump({"mcpServers": mcp_servers}, f, indent=2)
        f.write("\n")
    print("Updated .mcp.json")

print("\nDone.")
