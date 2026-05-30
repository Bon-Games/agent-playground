#!/usr/bin/env python3
"""
Notification CLI for AI developer workflow.

Usage (CLI):
  python workflows/notify.py --ticket PROJECT-123 --branch fix/... --summary "..." [--pr-body-file /tmp/pr.md] [--channel telegram]

Usage (module):
  from notify import send_notification
  send_notification(summary="...", channel="telegram", ticket="PROJECT-123", branch="fix/...")
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path


def _load_env():
    candidates = [
        Path(__file__).parent.parent / "mcp-servers" / ".env",
        Path(__file__).parent.parent / ".env",
        Path.cwd() / "mcp-servers" / ".env",
        Path.cwd() / ".env",
    ]
    for path in candidates:
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())
            return


def _send_telegram(message: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("[notify] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping Telegram.", file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[notify] Telegram error: {e}", file=sys.stderr)
        return False


def _save_failed(message: str):
    failed_path = Path(__file__).parent.parent / ".claude" / "workflow-state" / "notification-failed.txt"
    failed_path.parent.mkdir(parents=True, exist_ok=True)
    failed_path.write_text(message, encoding="utf-8")
    print(f"[notify] Saved failed notification to {failed_path}", file=sys.stderr)


def send_notification(
    summary: str,
    channel: str = "telegram",
    ticket: str = "",
    branch: str = "",
    pr_body_file: str = "",
):
    _load_env()

    jira_base = os.environ.get("JIRA_URL", "").rstrip("/")
    ticket_url = f"{jira_base}/browse/{ticket}" if jira_base and ticket else ""

    parts = []
    if ticket:
        header = f"*[{ticket}]* fix ready"
        if ticket_url:
            header += f" — [{ticket}]({ticket_url})"
        parts.append(header)
    if branch:
        parts.append(f"Branch: `{branch}`")
    parts.append("")
    parts.append(summary)
    if pr_body_file:
        parts.append(f"\nPR body: `{pr_body_file}`")
    parts.append("\n_Push when ready — agent has not pushed._")

    message = "\n".join(parts)

    if channel == "telegram":
        ok = _send_telegram(message)
        if not ok:
            _save_failed(message)
    elif channel == "email":
        print(f"[notify] Email channel not yet implemented.\n{message}")
    else:
        print(f"[notify] Unknown channel '{channel}'.\n{message}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send workflow notification")
    parser.add_argument("--ticket", default="", help="Jira ticket ID")
    parser.add_argument("--branch", default="", help="Git branch name")
    parser.add_argument("--summary", required=True, help="One-paragraph summary")
    parser.add_argument("--pr-body-file", default="", help="Path to generated PR body file")
    parser.add_argument("--channel", default="telegram", choices=["telegram", "email"])
    args = parser.parse_args()

    send_notification(
        summary=args.summary,
        channel=args.channel,
        ticket=args.ticket,
        branch=args.branch,
        pr_body_file=args.pr_body_file,
    )
