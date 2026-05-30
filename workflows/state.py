"""Workflow state file helpers — read/write phase artifacts for fix-bug and other commands."""
import json
from datetime import date
from pathlib import Path


def _repo_root() -> Path:
    here = Path(__file__).parent
    for candidate in (here, here.parent, here.parent.parent):
        if (candidate / ".git").exists() or (candidate / "CLAUDE.md").exists():
            return candidate
    return here.parent


STATE_DIR = _repo_root() / ".claude" / "workflow-state"


def get_run_dir(ticket: str) -> Path:
    today = date.today().strftime("%Y%m%d")
    run_dir = STATE_DIR / f"{ticket}-{today}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_state(ticket: str, phase: str, data) -> Path:
    run_dir = get_run_dir(ticket)
    path = run_dir / phase
    if isinstance(data, (dict, list)):
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        path.write_text(str(data), encoding="utf-8")
    return path


def load_state(ticket: str, phase: str):
    dir_name = _find_latest_run(ticket)
    if dir_name is None:
        return None
    path = STATE_DIR / dir_name / phase
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    if phase.endswith(".json"):
        return json.loads(content)
    return content


def _find_latest_run(ticket: str) -> str | None:
    if not STATE_DIR.exists():
        return None
    dirs = sorted(
        [d.name for d in STATE_DIR.iterdir() if d.is_dir() and d.name.startswith(f"{ticket}-")],
        reverse=True,
    )
    return dirs[0] if dirs else None
