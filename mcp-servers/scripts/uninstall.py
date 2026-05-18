import json, subprocess, os, sys, shutil

sys.path.insert(0, os.path.dirname(__file__))
from lib import load_catalog

print("Stopping Docker Compose stack...")
subprocess.run(["docker", "compose", "down"], check=False)

if os.path.isdir("servers"):
    print("Removing servers/...")
    shutil.rmtree("servers")

for path in ["docker-compose.override.yml", "env.template"]:
    if os.path.exists(path):
        os.remove(path)
        print(f"Removed {path}")

empty = json.dumps({"mcpServers": {}}, indent=2) + "\n"

for mcp_path in [".mcp.json", os.path.join("..", ".mcp.json")]:
    with open(mcp_path, "w") as f:
        f.write(empty)
    print(f"Cleared {os.path.normpath(mcp_path)}")

# Clear Gemini settings
gemini_path = os.path.join("..", ".gemini", "settings.json")
if os.path.exists(gemini_path):
    with open(gemini_path, "w") as f:
        f.write(empty)
    print(f"Cleared {os.path.normpath(gemini_path)}")

# Remove plugin entries from ~/.claude/settings.json
catalog = load_catalog("tools")
plugin_names = {name for name, entry in catalog.items() if entry.get("source") == "plugin"}

settings_path = os.path.expanduser("~/.claude/settings.json")
if plugin_names and os.path.exists(settings_path):
    with open(settings_path) as f:
        settings = json.load(f)
    mcp_servers = settings.get("mcpServers", {})
    removed = [n for n in plugin_names if n in mcp_servers]
    for n in removed:
        del mcp_servers[n]
    if removed:
        import tempfile
        dir_ = os.path.dirname(settings_path)
        with tempfile.NamedTemporaryFile("w", dir=dir_, delete=False, suffix=".tmp") as tmp:
            json.dump(settings, tmp, indent=2)
            tmp.write("\n")
            tmp_path = tmp.name
        os.replace(tmp_path, settings_path)
        print(f"Removed plugins from {settings_path}: {', '.join(removed)}")

print("\nDone.")
