# AI Developer Daily Workflow — System Architecture

## Layer Model

```
┌──────────────────────────────────────────────────────────────┐
│  L1 · INTERFACE                                              │
│  /fix-bug  /daily-triage  /review-pr   (Claude Code CLI)     │
│  + scheduled entry: Task Scheduler (Win) · launchd (macOS)  │
└────────────────────────┬─────────────────────────────────────┘
                         │ slash command → loads .md prompt
┌────────────────────────▼─────────────────────────────────────┐
│  L2 · ORCHESTRATION                                          │
│  Workflow state machine  .claude/workflow-state/<run>/       │
│  Phase sequencer · pause/resume · parallelism hints          │
└────────────────────────┬─────────────────────────────────────┘
                         │ structured instructions to Claude
┌────────────────────────▼─────────────────────────────────────┐
│  L3 · AGENT COGNITION  (Claude)                              │
│  ReAct loops · plan-before-execute · context budget mgmt     │
│  self-review · sub-agent delegation for deep investigation   │
└────────────────────────┬─────────────────────────────────────┘
                         │ tool calls (parallel where independent)
┌────────────────────────▼─────────────────────────────────────┐
│  L4 · TOOL ABSTRACTION  (MCP + native)                       │
│  atlassian · gws-mcp · github · context7 · unity-mcp        │
│  Bash (git, build, test) · File (Read/Edit/Write)            │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│  L5 · EXTERNAL SYSTEMS                                       │
│  Jira · Confluence · GitHub · Gmail · Drive · Unity Editor   │
│  Telegram Bot API                                            │
└──────────────────────────────────────────────────────────────┘
```

---

## Critical Gap in the Original Plan: No State Management

The original plan's biggest weakness is that each phase lives only in Claude's context window. This causes three problems:

1. **No resumability** — if Phase 5 validation fails after 10 minutes of investigation, the run dies and Phase 1–4 work is lost
2. **Context budget exhaustion** — long Jira + Confluence + git log dumps early in the conversation leave little room for code edits in Phase 4
3. **No audit trail** — nothing to review if the fix was wrong

**Solution: workflow state files at phase boundaries.**

Each `/fix-bug` run writes artifacts to `.claude/workflow-state/<ticket>-<YYYYMMDD>/`:

```
workflow-state/
  PROJECT-123-20260530/
    01-context.json        # Jira + Confluence summary (compact)
    02-branch.json         # branch name, base branch, created/existing
    03-root-cause.json     # hypothesis + file:line evidence
    04-diff.json           # list of changed files + summary
    05-validation.json     # test results, compile status, self-review
    06-commit.json         # commit hash, message
    07-pr-body.md          # filled PR template
    08-notification.json   # channel, sent timestamp, status
```

Later phases load only their relevant artifact, not the full conversation history. This keeps each phase's context clean and makes any phase independently resumable: `/fix-bug PROJECT-123 --resume phase5`.

---

## Fix-Bug State Machine

```
INIT
  │  (parallel) Jira fetch + comments + Confluence search + git branch scan
  ▼
CONTEXT_FETCHED  ──[write 01-context.json]──►  print summary
  │                                             ├─ if comments reference ambiguity → PAUSE: "Dive deeper?" (yes/no)
  │                                             └─ if clear → continue automatically
  │
  ▼
BRANCH_READY  ──[write 02-branch.json]──►  if ambiguous → PAUSE (user input)
  │
  ▼
ROOT_CAUSE_FOUND  ──[write 03-root-cause.json]──►  print hypothesis, continue
  │
  ▼                ◄── sub-agent spawned for deep codebase search
FIXED  ──[write 04-diff.json]──►  scoped edits only, no collateral changes
  │
  ▼
VALIDATED  ──[write 05-validation.json]──►  if fail: 1 auto-fix attempt, then PAUSE
  │
  ▼
COMMITTED  ──[write 06-commit.json]──►  local only, never git push
  │
  ▼
PR_READY  ──[write 07-pr-body.md]──►  print PR body for review
  │
  ▼
NOTIFIED  ──[write 08-notification.json]──►  Telegram + print "push when ready"
```

**Hard pauses** (require user confirmation before continuing):
- Phase 2: base branch is ambiguous
- Phase 5: validation fails after one auto-fix attempt
- Phase 3 optional: if root cause hypothesis confidence is low, surface it

---

## Parallelism Strategy

The commands must explicitly instruct parallel tool calls. The three high-value parallel points:

**Phase 1 of /fix-bug** — call all four simultaneously:
```
PARALLEL:
  - atlassian.getIssue(PROJECT-123)                          → title, desc, priority, status, sprint
  - atlassian.getIssueComments(PROJECT-123, maxResults=5)    → last 5 comments, newest first
  - atlassian.confluenceSearch(component from ticket)        → architecture docs
  - git branch -r | grep PROJECT-123                        → existing branches
```

**Jira comments — initial fetch + dive-deeper pattern:**

The last 5 comments are fetched automatically as part of Phase 1. Comments often carry the most current state: QA failure details, developer notes, reproduction steps added after the ticket was filed. Claude summarizes them in `01-context.json`.

After summarizing, Claude evaluates:

| Signal in comments | Automatic action |
|--------------------|-----------------|
| QA describes a new reproduction path not in the description | Include in root cause input; flag it |
| Comment references a linked ticket (`PROJ-456 is the root`) | Offer: "Found reference to PROJ-456. Dive deeper? (yes/no)" → PAUSE |
| Comment references a Confluence page URL | Offer: "Referenced doc found. Dive deeper? (yes/no)" → PAUSE |
| Comment count > 10 and latest is > 3 days old | Fetch all comments automatically (pattern suggests long-running investigation) |
| Comments are clear and self-contained | Continue to Phase 2 without pausing |

**Dive deeper** (user confirms or auto-triggered):
- Fetch full comment history (`startAt=0`, paginate all)
- Follow all linked issues (fetch their summaries)
- Fetch any Confluence page URLs mentioned in comments
- Update `01-context.json` with the enriched data before continuing

**Daily triage** — all three sources simultaneously:
```
PARALLEL:
  - atlassian: assigned issues, last 7 days
  - github: my open PRs + PRs needing review
  - gws-mcp: unread Jira/GitHub email threads, last 24h
```

This cuts `/daily-triage` wall time by ~3x vs sequential.

---

## Context Budget Strategy

LLM context is finite. The commands must enforce budget discipline:

| Phase | What to Load | What NOT to Load |
|-------|-------------|------------------|
| 1 | Full Jira + Confluence | — |
| 2 | `01-context.json` (compact) | Raw Jira JSON |
| 3 | `02-branch.json` + specific files | Full conversation history |
| 4 | `03-root-cause.json` only | Investigation trail |
| 5 | Changed file contents only | Phase 1–3 artifacts |
| 6–8 | Cumulative compact artifacts | Raw tool outputs |

Each `.json` artifact is a **compact summary**, not a raw API response. Claude writes summaries to files, not raw data.

---

## Sub-Agent Delegation for Root Cause (Phase 3)

Phase 3 is unbounded — it could read 20 files, run 10 git commands, look up library docs. If done in the main conversation, it consumes context needed for Phase 4.

**Pattern**: Claude spawns a focused sub-agent via the `Agent` tool:
- Main context: passes `01-context.json` + stack trace
- Sub-agent: does all file reading, git blame, context7 lookups
- Sub-agent returns: compact `root_cause.json` (hypothesis + evidence, under 500 tokens)
- Main context: receives only the compact result, proceeds to Phase 4 with full budget

This is the most important structural change vs. the original plan.

---

## Graceful Degradation Tiers

Each phase degrades gracefully when tools are unavailable:

| Tool | Unavailable Behavior |
|------|---------------------|
| atlassian MCP | Ask user: "Paste Jira ticket content" → proceed |
| github plugin | Fall back to local `git branch -r` + `git log` |
| context7 | Skip library docs; note gap in root cause report |
| unity-mcp | Skip compile check; flag "no Unity validation" in PR |
| gws-mcp | Skip email in triage; note gap in output table |
| Telegram | Log to `.claude/workflow-state/<run>/notification-failed.txt` |

Never abort a workflow because a secondary tool fails. Degrade and note the gap.

---

## Scheduling Architecture

Scheduling is **entirely Docker-based** — no OS-level setup (no Task Scheduler, no launchd, no cron on the host). A dedicated `scheduler` service joins the existing Docker Compose stack. Everything starts with a single command on any platform:

```
docker compose up -d
```

### Overview

```
docker compose up -d
       │
       ├─► atlassian (port 9090)  ─────────────────────┐
       ├─► gws-mcp   (port 8100)  ─────────────────────┤
       ├─► context7  (port 3000)  ─────────────────────┤
       ├─► 9router   (port 20128) ─────────────────────┤ Docker network
       └─► scheduler ────────────────────────────────────┘
               │
               │  on schedule (TRIAGE_HOUR / TRIAGE_DAYS from .env)
               ▼
       workflows/scheduler-service.py
               │  Anthropic Python SDK + remote MCP servers
               │  (connects to atlassian, gws-mcp via Docker-internal hostnames)
               ▼
       Anthropic API ──► claude-opus-4-8
               │  model uses MCP tools over Docker network
               ▼
       workflows/notify.py --channel telegram
```

### Why Anthropic SDK instead of `claude --print`

The `claude` CLI requires interactive authentication (OAuth browser flow) that cannot run headlessly in a container. The Anthropic Python SDK authenticates with a single `ANTHROPIC_API_KEY` env var — already present in `.env`. The SDK also supports passing MCP server URLs directly to the API, so the model can use the same MCP tools as the interactive slash commands, over the Docker-internal network.

### `tools/scheduler/` — new tool definition

Added to `dev-workflow.json` profile with a new source type `service`: included in `docker-compose.override.yml` but not registered as an MCP endpoint (no port exposed to Claude Code).

```
tools/scheduler/
  config.json      # source: service, no port — compose-only, no MCP registration
  Dockerfile       # python:3.12-slim + anthropic SDK + schedule lib
```

**`config.json`:**
```json
{
  "name": "scheduler",
  "source": "service",
  "description": "Scheduled workflow runner — daily triage and future automations"
}
```

**`Dockerfile`:**
```dockerfile
FROM python:3.12-slim
RUN pip install anthropic schedule python-dotenv requests
WORKDIR /app
COPY workflows/ ./workflows/
COPY .claude/commands/ ./.claude/commands/
CMD ["python", "workflows/scheduler-service.py"]
```

### `workflows/scheduler-service.py`

Long-running Python process. Reads schedule from env, runs the triage workflow via Anthropic API.

```python
import schedule, time, os
from triage_runner import run_triage

HOUR = int(os.environ.get("TRIAGE_HOUR", "8"))
DAYS = os.environ.get("TRIAGE_DAYS", "mon,tue,wed,thu,fri").split(",")

for day in DAYS:
    getattr(schedule.every(), day.strip()).at(f"{HOUR:02d}:00").do(run_triage)

while True:
    schedule.run_pending()
    time.sleep(30)
```

### `workflows/triage_runner.py`

Executes the triage via Anthropic SDK with MCP servers on the Docker network.

```python
import anthropic, os
from pathlib import Path
from notify import send_notification

MCP_SERVERS = [
    {"type": "url", "url": "http://atlassian:9090/mcp",  "name": "atlassian"},
    {"type": "url", "url": "http://gws-mcp:8100/mcp",   "name": "gws-mcp"},
    {"type": "url", "url": "http://context7:3000/mcp",   "name": "context7"},
]

def run_triage():
    prompt = Path(".claude/commands/daily-triage.md").read_text()
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.beta.messages.create(
        model="claude-opus-4-8-20251101",
        max_tokens=4096,
        mcp_servers=MCP_SERVERS,
        messages=[{"role": "user", "content": prompt}],
        betas=["mcp-client-2025-04-04"],
    )
    summary = response.content[-1].text
    send_notification(summary, channel="telegram")
```

### Compose service definition (generated into `docker-compose.override.yml`)

```yaml
scheduler:
  build:
    context: tools/scheduler
  env_file: .env
  environment:
    - TRIAGE_HOUR=${TRIAGE_HOUR:-8}
    - TRIAGE_DAYS=${TRIAGE_DAYS:-mon,tue,wed,thu,fri}
  volumes:
    - ../../workflows:/app/workflows:ro
    - ../../.claude/commands:/app/.claude/commands:ro
  restart: unless-stopped
  networks:
    - mcp_default
  depends_on:
    - atlassian
    - gws-mcp
```

### New `.env` keys

```
ANTHROPIC_API_KEY=<your key>
TRIAGE_HOUR=8
TRIAGE_DAYS=mon,tue,wed,thu,fri
```

`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are already required by `notify.py`.

---

## Component Breakdown

### `.claude/commands/fix-bug.md`
Orchestration prompt for the 8-phase bug fix workflow.
- Explicit state file write instructions at each phase boundary
- Parallelism hints at Phase 1
- Sub-agent delegation hint for Phase 3
- Hard pause conditions defined
- Context load instructions per phase (load only the artifact, not prior raw output)

### `.claude/commands/daily-triage.md`
Triage orchestration prompt.
- Explicit parallel tool calls for all 3 sources
- Priority matrix (P0 blocking / P1 today / P2 this week)
- Recommended action per item with links to other commands

### `.claude/commands/review-pr.md`
PR review prompt.
- Structured diff analysis via code-review plugin
- Confirmation gate before posting GitHub comments
- Outputs findings with file:line references

### `workflows/notify.py`
Notification CLI invoked by Claude via Bash.
- Telegram (primary): single HTTP POST to `api.telegram.org`
- Gmail via gws-mcp (secondary): requires service account
- SMTP fallback: if `SMTP_*` vars present in `.env`
- Reads credentials from `.env` at runtime; never from CLI args

### `workflows/state.py`
State file helpers imported by notify.py and future workflow scripts.
- Uses `pathlib.Path` throughout — no hardcoded separators, works on Windows and macOS
- `load_state(ticket, phase)` — load artifact JSON
- `save_state(ticket, phase, data)` — write artifact JSON
- `get_run_dir(ticket)` — resolve `.claude/workflow-state/<ticket>-<date>/`

### `tools/scheduler/`
New Docker service definition. Source type `service` — included in Compose but not registered as an MCP endpoint.
- `config.json`: declares source, description; no port
- `Dockerfile`: `python:3.12-slim` + `anthropic`, `schedule`, `requests`, `python-dotenv`

### `workflows/scheduler-service.py`
Long-running process that is the container's entrypoint.
- Reads `TRIAGE_HOUR` and `TRIAGE_DAYS` from env
- Uses the Python `schedule` library to fire `triage_runner.run_triage()` at the configured time
- Loops with 30-second sleep between checks

### `workflows/triage_runner.py`
Executes the daily triage via Anthropic Python SDK.
- Loads the prompt from `.claude/commands/daily-triage.md`
- Calls `client.beta.messages.create()` with `mcp_servers` pointing to Docker-internal hostnames (`http://atlassian:9090/mcp`, etc.)
- On success: calls `notify.send_notification(summary, channel="telegram")`
- On exception: sends error notification with traceback excerpt

---

## Full File Manifest

```
.claude/
  commands/
    fix-bug.md                    # 8-phase bug fix orchestration
    daily-triage.md               # parallel triage across Jira/GitHub/Gmail
    review-pr.md                  # structured PR review
  pr-templates/
    bug-fix.md                    # PR body template
  workflow-state/                 # gitignored — per-run phase artifacts

workflows/
  notify.py                       # Telegram + Gmail notification CLI
  state.py                        # state file helpers, pathlib-based
  scheduler-service.py            # container entrypoint — schedule loop
  triage_runner.py                # Anthropic SDK triage execution

tools/scheduler/
  config.json                     # source: service (compose-only, no MCP port)
  Dockerfile                      # python:3.12-slim + anthropic + schedule

mcp-servers/config/profiles/
  dev-workflow.json               # activates: context7, atlassian, gws-mcp,
                                  #            github, code-review, unity-mcp, scheduler
```

---

## Build Sequence

Order matters — later files depend on earlier ones:

1. `mcp-servers/config/profiles/dev-workflow.json` — activate profile, verify MCP servers start
2. `workflows/state.py` — shared helper, no deps, testable standalone
3. `workflows/notify.py` — depends on state.py; test with a real Telegram message
4. `.claude/pr-templates/bug-fix.md` — standalone template, no deps
5. `.claude/commands/daily-triage.md` — simplest command; good smoke test for MCP connectivity
6. `.claude/commands/review-pr.md` — medium complexity
7. `.claude/commands/fix-bug.md` — most complex; build last when all tools verified
8. `tools/scheduler/` + `workflows/scheduler-service.py` + `workflows/triage_runner.py` — Docker scheduler service, last
   - No OS setup required; starts with `docker compose up -d`

---

## Delta from Original Plan

| Original Plan | Architecture Decision | Reason |
|---------------|-----------------------|--------|
| No state files | Phase artifact files at `.claude/workflow-state/` | Resumability + context budget control |
| Single monolithic Phase 3 | Sub-agent delegation for root cause | Protect main context for Phase 4 fix |
| OS-level scheduling (Task Scheduler / launchd) | Docker `scheduler` service with Anthropic SDK | Platform-agnostic; starts with `docker compose up -d`; no host-side setup |
| `claude --print` headless CLI | Anthropic Python SDK + `mcp_servers` URLs | CLI requires interactive OAuth; SDK authenticates with `ANTHROPIC_API_KEY` only |
| Phase 1 fetches only ticket body | Parallel fetch of ticket + last 5 comments + Confluence + branch scan | Comments hold the most current state; dive-deeper pause on ambiguous references |
| No degradation strategy | Per-tool fallback tiers | MCP servers go down; workflow must not die |
| Sequential Phase 1 | Parallel Jira + Confluence + git | 3x faster triage start |
| Discord notification | Telegram Bot API | Single HTTP POST, no webhook server, no OAuth |

---

## Open Questions (carry forward from plan)

1. **PR template**: User will provide a custom template — default is in place, editable at `.claude/pr-templates/bug-fix.md`
2. **Unity headless**: Requires Unity Editor on host; Phase 5 degrades gracefully if absent
3. **Gmail vs Telegram**: Telegram is the default. Gmail via gws-mcp requires service account credentials already configured in `mcp-servers/.env`
4. **Multi-repo**: If the user works across multiple Unity repos, `/fix-bug` will need a `--repo <path>` flag or a repo selection step before Phase 2
