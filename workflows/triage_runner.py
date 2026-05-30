"""
Executes the daily triage prompt via the Anthropic API with Docker-networked MCP servers.
Called by scheduler-service.py on schedule.
"""
import logging
import os
from pathlib import Path

import anthropic

from notify import send_notification

log = logging.getLogger(__name__)

# MCP server URLs — Docker-internal hostnames (service names from docker-compose)
MCP_SERVERS = [
    {"type": "url", "url": "http://atlassian:9090/mcp",  "name": "atlassian"},
    {"type": "url", "url": "http://gws-mcp:8100/mcp",    "name": "gws-mcp"},
    {"type": "url", "url": "http://context7:3000/mcp",   "name": "context7"},
]

TRIAGE_PROMPT_PATH = Path("/app/.claude/commands/daily-triage.md")


def run_triage() -> str:
    if not TRIAGE_PROMPT_PATH.exists():
        raise FileNotFoundError(f"Triage prompt not found: {TRIAGE_PROMPT_PATH}")

    prompt = TRIAGE_PROMPT_PATH.read_text(encoding="utf-8")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set")

    client = anthropic.Anthropic(api_key=api_key)

    log.info("Calling Anthropic API for triage...")
    response = client.beta.messages.create(
        model="claude-opus-4-8-20251101",
        max_tokens=4096,
        mcp_servers=MCP_SERVERS,
        messages=[{"role": "user", "content": prompt}],
        betas=["mcp-client-2025-04-04"],
    )

    text_blocks = [b.text for b in response.content if hasattr(b, "text")]
    summary = "\n".join(text_blocks).strip()
    log.info("Triage complete. Sending notification...")

    send_notification(summary=summary, channel="telegram")
    return summary
