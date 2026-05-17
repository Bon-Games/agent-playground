import json, subprocess, os, sys, shutil

print("Stopping Docker Compose stack...")
subprocess.run(["docker", "compose", "down"], check=False)

if os.path.isdir("servers"):
    print("Removing servers/...")
    shutil.rmtree("servers")

if os.path.exists("docker-compose.override.yml"):
    os.remove("docker-compose.override.yml")
    print("Removed docker-compose.override.yml")

with open(".mcp.json", "w") as f:
    json.dump({"mcpServers": {}}, f, indent=2)
    f.write("\n")
print("Cleared .mcp.json")

print("\nDone.")
