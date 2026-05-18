import json, os, glob


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
