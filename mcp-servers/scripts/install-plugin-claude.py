#!/usr/bin/env python3
"""Install MCP plugin configs for Claude Code — writes to ~/.claude/settings.json.

Usage:
  python scripts/install-plugin-claude.py
  python scripts/install-plugin-claude.py --profile config/profiles/unity.json
"""
import json, os, sys, tempfile

sys.path.insert(0, os.path.dirname(__file__))
from lib import load_catalog


def to_claude_entry(mcp_cfg):
    entry = {"type": mcp_cfg.get("type", "http")}
    if entry["type"] == "http":
        entry["url"] = mcp_cfg["url"]
        if "headers" in mcp_cfg:
            entry["headers"] = mcp_cfg["headers"]
    else:
        entry["command"] = mcp_cfg["command"]
        entry["args"] = mcp_cfg.get("args", [])
        if mcp_cfg.get("env"):
            entry["env"] = mcp_cfg["env"]
    return entry


def install_plugins(profile_path, tools_dir="tools"):
    catalog = load_catalog(tools_dir)
    with open(profile_path) as f:
        profile = json.load(f)

    plugins = [
        catalog[n]
        for n in profile.get("servers", [])
        if n in catalog and catalog[n].get("source") == "plugin"
    ]
    if not plugins:
        print("No plugins in this profile.")
        return

    settings_path = os.path.expanduser("~/.claude/settings.json")
    settings = {}
    if os.path.exists(settings_path):
        with open(settings_path) as f:
            settings = json.load(f)
    mcp_servers = settings.setdefault("mcpServers", {})

    for p in plugins:
        mcp_cfg = p.get("mcp_config")
        if not mcp_cfg:
            print(f"[WARN] {p['name']} has no mcp_config — skipping")
            continue
        mcp_servers[p["name"]] = to_claude_entry(mcp_cfg)
        print(f"[plugin] {p['name']} → {settings_path}")

    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    # Atomic write: write to a temp file then replace to avoid corruption
    dir_ = os.path.dirname(settings_path)
    with tempfile.NamedTemporaryFile("w", dir=dir_, delete=False, suffix=".tmp") as tmp:
        json.dump(settings, tmp, indent=2)
        tmp.write("\n")
        tmp_path = tmp.name
    os.replace(tmp_path, settings_path)


if __name__ == "__main__":
    args = sys.argv[1:]
    profile = "config/profiles/default.json"
    while args:
        if args[0] == "--profile" and len(args) >= 2:
            profile = args[1]
            args = args[2:]
        else:
            print("Usage: install-plugin-claude.py [--profile <path>]")
            sys.exit(1)
    install_plugins(profile)
