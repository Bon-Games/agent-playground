#!/usr/bin/env python3
"""Install Claude plugins via 'claude plugin install'.

Usage:
  python scripts/install-plugin-claude.py
  python scripts/install-plugin-claude.py --profile config/profiles/unity.json
"""
import json, os, sys, subprocess

sys.path.insert(0, os.path.dirname(__file__))
from lib import load_catalog


def install_plugin(p):
    plugin_id = p.get("plugin_id") or p["name"]
    result = subprocess.run(
        ["claude", "plugin", "install", plugin_id],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"[ERROR] {plugin_id}: {result.stderr.strip()}")
    else:
        print(f"[plugin] {plugin_id} installed")


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

    for p in plugins:
        install_plugin(p)


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
