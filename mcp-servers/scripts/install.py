import json, subprocess, os, sys, platform as _platform
sys.path.insert(0, os.path.dirname(__file__))
from lib import load_catalog, yaml_indent as i, clone_or_update


DEFAULT_PROFILE = "config/profiles/default.json"
TOOLS_DIR = "tools"


def usage():
    print("Usage: install.sh [--profile <path>]")
    print("       install.sh                                        # uses default profile")
    print("       install.sh --profile config/profiles/unity.json  # named profile")
    sys.exit(1)


def resolve_profile(tools_dir, profile_path):
    catalog = load_catalog(tools_dir)
    current_os = _platform.system().lower()

    with open(profile_path) as f:
        profile = json.load(f)

    active_servers, remote_services, plugins, service_only = [], [], [], []
    for name in profile.get("servers", []):
        if name not in catalog:
            print(f"[WARN] '{name}' not in tools/ catalog — skipping")
            continue
        entry = catalog[name]
        source = entry.get("source", "git")
        if source == "plugin":
            plugins.append(entry)
            continue
        if source == "remote":
            remote_services.append(entry)
            continue
        if source == "service":
            service_only.append(entry)
            continue
        allowed = entry.get("platform", ["linux", "darwin", "windows"])
        if current_os not in allowed:
            print(f"[WARN] '{name}' not supported on {current_os} — skipping")
            continue
        active_servers.append(entry)

    return active_servers, remote_services, plugins, service_only


def service_lines(s):
    name = s["name"]
    port = s.get("port")
    source = s.get("source", "git")

    lines = [i(1, f"{name}:")]

    if source == "image":
        lines.append(i(2, f"image: {s['image']}"))
    else:
        ctx = f"./{s.get('local_path', os.path.join('tools', name))}" if source in ("local", "service") else f"./servers/{name}"
        lines += [
            i(2, "build:"),
            i(3, f"context: {ctx}"),
            i(3, f"dockerfile: {s.get('dockerfile', 'Dockerfile')}"),
        ]

    lines.append(i(2, f"container_name: {name}"))

    if port:
        lines += [
            i(2, "ports:"),
            i(3, f'- "{port}:{port}"'),
        ]

    environment = s.get("environment", {})
    if environment:
        lines.append(i(2, "environment:"))
        for k, v in environment.items():
            lines.append(i(3, f"{k}: {v}"))

    volumes = s.get("volumes", [])
    if volumes:
        lines.append(i(2, "volumes:"))
        for v in volumes:
            lines.append(i(3, f"- {v}"))

    depends_on = s.get("depends_on", [])
    if depends_on:
        lines.append(i(2, "depends_on:"))
        for dep in depends_on:
            lines.append(i(3, f"- {dep}"))

    if s.get("command"):
        lines.append(i(2, f"command: {s['command']}"))

    lines += [i(2, "restart: unless-stopped"), ""]
    return lines


def generate_env_template(tools, output_path=".env"):
    parts = []
    for t in tools:
        env_file = os.path.join(t.get("local_path", os.path.join("tools", t["name"])), ".env")
        if not os.path.exists(env_file):
            continue
        with open(env_file) as f:
            content = f.read().strip()
        if content:
            parts.append(f"# --- {t['name']} ---\n{content}")
    if parts:
        with open(output_path, "w") as f:
            f.write("\n\n".join(parts) + "\n")
        print(f"Generated {output_path} — copy to .env and fill in your values")
    else:
        print("No env vars required for this profile")


# Parse flags
profile_file = None
args = sys.argv[1:]
while args:
    if args[0] == "--profile" and len(args) >= 2:
        profile_file = args[1]
        args = args[2:]
    else:
        usage()

profile_file = profile_file or DEFAULT_PROFILE
active_servers, remote_services, plugins, service_only = resolve_profile(TOOLS_DIR, profile_file)

if not active_servers and not remote_services and not plugins and not service_only:
    print("No tools to install.")
    sys.exit(0)

os.makedirs("servers", exist_ok=True)

# Clone or update git-sourced servers
for s in active_servers:
    name = s["name"]
    source = s.get("source", "git")
    if source in ("local", "image"):
        print(f"[{name}] {source} source, skipping clone.")
        continue

    clone_or_update(name, s["repo"], s.get("branch", "main"), os.path.join("servers", name))

# Generate docker-compose.override.yml (active MCP servers + service-only containers)
compose_lines = ["services:"]
for s in active_servers + service_only:
    compose_lines.extend(service_lines(s))

with open("docker-compose.override.yml", "w") as f:
    f.write("\n".join(compose_lines) + "\n")
print("Generated docker-compose.override.yml")

# Build .mcp.json (active servers + remote services)
mcp_servers = {}
for s in active_servers:
    mcp_servers[s["name"]] = {
        "type": s.get("transport", "http"),
        "url": f"http://localhost:{s['port']}{s.get('mcp_path', '/mcp')}",
    }
for r in remote_services:
    mcp_servers[r["name"]] = {"type": "http", "url": r["url"]}

mcp_json = json.dumps({"mcpServers": mcp_servers}, indent=2) + "\n"

with open(".mcp.json", "w") as f:
    f.write(mcp_json)
print("Updated mcp-servers/.mcp.json")

root_mcp = os.path.join("..", ".mcp.json")
with open(root_mcp, "w") as f:
    f.write(mcp_json)
print(f"Updated {os.path.normpath(root_mcp)} (project root — Claude Code reads this)")

# Regenerate .gemini/settings.json
gemini_mcp = {}
for s in active_servers:
    gemini_mcp[s["name"]] = {"url": f"http://localhost:{s['port']}{s.get('mcp_path', '/mcp')}"}
for r in remote_services:
    gemini_mcp[r["name"]] = {"url": r["url"]}

gemini_json = json.dumps({"mcpServers": gemini_mcp}, indent=2) + "\n"
gemini_settings_path = os.path.join("..", ".gemini", "settings.json")
os.makedirs(os.path.dirname(gemini_settings_path), exist_ok=True)
with open(gemini_settings_path, "w") as f:
    f.write(gemini_json)
print(f"Updated {os.path.normpath(gemini_settings_path)} (Gemini CLI config)")

# Generate env.template from per-tool .env files
generate_env_template(active_servers + remote_services + service_only)

# Install plugins into ~/.claude/settings.json
if plugins:
    subprocess.run(
        [sys.executable, "scripts/install-plugin-claude.py", "--profile", profile_file],
        check=True,
    )

# Run per-tool install.py scripts in parallel
procs = []
for s in active_servers + remote_services + plugins + service_only:
    name = s["name"]
    tool_install = os.path.join(TOOLS_DIR, name, "install.py")
    if os.path.isfile(tool_install):
        print(f"[{name}] starting {tool_install}...")
        proc = subprocess.Popen([sys.executable, tool_install])
        procs.append((name, proc))
    else:
        print(f"No custom install.py found for {name}")

failed = []
for tool_dir, proc in procs:
    proc.wait()
    if proc.returncode != 0:
        failed.append(tool_dir)

if failed:
    print(f"[ERROR] Tool installs failed: {', '.join(failed)}", file=sys.stderr)
    sys.exit(1)

print("\nDone. Run 'docker compose up -d --build' to start the stack.")
