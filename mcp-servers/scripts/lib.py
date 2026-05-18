import json, os, glob, subprocess


def yaml_indent(level, text):
    return "  " * level + text


def clone_or_update(name, repo, branch, dest):
    if os.path.isdir(os.path.join(dest, ".git")):
        print(f"[{name}] already cloned — pulling latest...")
        subprocess.run(["git", "-C", dest, "pull"], check=True)
    else:
        print(f"[{name}] cloning {repo} (branch: {branch})...")
        subprocess.run(["git", "clone", "-b", branch, "--depth", "1", repo, dest], check=True)


def load_catalog(tools_dir="tools"):
    catalog = {}
    for path in glob.glob(os.path.join(tools_dir, "*", "config.json")):
        with open(path) as f:
            entry = json.load(f)
        if entry.get("name") == "_template":
            continue
        entry.setdefault("local_path", os.path.dirname(path))
        catalog[entry["name"]] = entry
    return catalog
