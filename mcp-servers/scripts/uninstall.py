import json, subprocess, os, sys, shutil

print("Stopping Docker Compose stack...")
subprocess.run(["docker", "compose", "down"], check=False)

if os.path.isdir("servers"):
    print("Removing servers/...")
    shutil.rmtree("servers")

if os.path.exists("docker-compose.override.yml"):
    os.remove("docker-compose.override.yml")
    print("Removed docker-compose.override.yml")

empty = json.dumps({"mcpServers": {}}, indent=2) + "\n"

with open(".mcp.json", "w") as f:
    f.write(empty)
print("Cleared mcp-servers/.mcp.json")

root_mcp = os.path.join("..", ".mcp.json")
with open(root_mcp, "w") as f:
    f.write(empty)
print("Cleared project root .mcp.json")

print("\nDone.")
