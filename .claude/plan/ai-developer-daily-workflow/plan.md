# AI Developer Daily Workflow — Plan

## Context

The user is a software/game developer working daily across Jira, GitHub, Gmail, Confluence, and Unity. They need AI-orchestrated workflows that reduce toil: check sources → prioritize → investigate/fix → commit → notify, then get out of the way. The repo already has all the MCP servers needed (atlassian, gws-mcp, github plugin, mcp-discord, context7, unity-mcp). This plan wires those tools into **Claude Code slash commands** — markdown instruction files under `.claude/commands/` that Claude executes using its live MCP tool access.

The primary deliverable is the **bug fix flow** (`/fix-bug`), plus two supporting commands (`/daily-triage`, `/review-pr`) and the shared infrastructure (PR template, notify helper, workflow profile).

---

## Architecture

```
User types /fix-bug PROJECT-123
        │
        ▼
.claude/commands/fix-bug.md  ←── orchestrates Claude via step-by-step prompt
        │
        ├─► atlassian MCP  ──► fetch Jira ticket, search Confluence docs
        ├─► github plugin  ──► list branches, PR history, blame context
        ├─► context7 MCP   ──► library docs if external deps involved
        ├─► File tools      ──► read/edit codebase files
        ├─► Bash tool       ──► git checkout/commit, dotnet build / Unity headless
        ├─► unity-mcp       ──► compile check (if Unity profile active)
        ├─► workflows/notify.py  ──► Discord message + draft Gmail
        └─► .claude/pr-templates/bug-fix.md  ──► fill PR body template
```

```
Daily: /daily-triage
        │
        ├─► atlassian MCP  ──► assigned Jira issues (new + updated)
        ├─► github plugin  ──► PRs awaiting my review + change requests on mine
        ├─► gws-mcp        ──► unread Gmail threads (Jira/GitHub notifications)
        └─► Output: ranked work list with recommended action per item
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `.claude/commands/fix-bug.md` | Main 8-phase bug fix slash command |
| `.claude/commands/daily-triage.md` | Daily standup slash command |
| `.claude/commands/review-pr.md` | PR review slash command |
| `.claude/pr-templates/bug-fix.md` | Parameterized PR description template |
| `workflows/notify.py` | Telegram + Gmail notification helper |
| `mcp-servers/config/profiles/dev-workflow.json` | Profile activating all workflow MCP servers |

---

## Detailed Implementation

### 1. `mcp-servers/config/profiles/dev-workflow.json`

New profile that enables everything needed for the workflow:
```json
{
  "description": "Full developer workflow: Jira, GitHub, Gmail, docs, Unity",
  "servers": ["context7", "atlassian", "gws-mcp", "github", "code-review", "unity-mcp"]
}
```

Note: `mcp-discord` removed — Telegram notifications are handled directly by `workflows/notify.py` via HTTP, no MCP server needed.

Run `./install.sh --profile config/profiles/dev-workflow.json` to activate.

---

### 2. `.claude/pr-templates/bug-fix.md`

Template Claude fills in before committing. Sections:
- **Summary**: one-line fix description
- **Jira**: link to ticket
- **Root Cause**: what was wrong and why
- **Evidence**: stack traces, logs, QA repro notes quoted from the ticket
- **Fix Description**: what changed and why this approach
- **Reproduction Steps**: ordered steps from QA notes
- **Test Plan**: what to verify after merge
- **Risk**: any side effects or areas to regression-test

---

### 3. `workflows/notify.py`

A CLI Python script that sends a notification with a summary. Invoked by Claude via Bash.

```
python workflows/notify.py \
  --ticket PROJECT-123 \
  --branch fix/PROJECT-123-null-ref-in-inventory \
  --summary "Fixed NullRef in InventoryManager when item count is 0" \
  --pr-body-file /tmp/pr_body.md \
  --channel telegram  # or: email
```

Behavior:
- **Telegram** (default): `POST api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/sendMessage` with `chat_id=TELEGRAM_CHAT_ID` — sends a formatted message with ticket link, branch name, and summary. No server, no OAuth, just a token + chat ID.
- **Email**: draft a Gmail via gws-mcp OR use SMTP fallback if `NOTIFY_EMAIL` is set in `.env`
- Reads credentials from `.env` at repo root
- Non-blocking; Claude continues after calling it

New `.env` keys needed:
```
TELEGRAM_BOT_TOKEN=<your bot token from @BotFather>
TELEGRAM_CHAT_ID=<your personal chat ID — get it from @userinfobot>
NOTIFY_EMAIL=ndinhtoan48@gmail.com
```

**Why Telegram over Discord**: Telegram's Bot API is a single HTTPS POST to `api.telegram.org/bot<token>/sendMessage` — no webhook server, no OAuth, no channel setup. Ideal for personal developer notifications. Discord is removed from the plan.

---

### 4. `.claude/commands/fix-bug.md` — The Core Workflow

Invoked as `/fix-bug PROJECT-123` (or `/fix-bug PROJECT-123 --unity` for Unity projects).

**Phase 1 — Jira Context** (automatic)
- `atlassian` MCP: fetch issue by ID → title, description, priority, reporter, QA comments, acceptance criteria, linked issues, fix-version, sprint
- `atlassian` MCP: `confluence_search` for docs mentioning the component named in the ticket
- Output: structured context block printed for user to see

**Phase 2 — Branch Strategy** (auto-detect, pause if ambiguous)
- Bash: `git branch -r | grep -i "<ticket-id>"` to find existing branches
- GitHub plugin: search PRs for ticket ID to check if one is already in flight
- **If branch found**: confirm with user ("Found `fix/PROJECT-123-foo` on remote — use this?") then `git checkout`
- **If no branch**: check Jira `fixVersions` / sprint name to determine base branch; ask user: "No branch found. I'll create `fix/PROJECT-123-<slug>` from `develop`. Confirm?"
- **Hard pause**: If base branch is ambiguous and Jira gives no signal, ask user before proceeding

**Phase 3 — Root Cause Investigation** (automatic, outputs hypothesis)
- Read files mentioned in Jira description / stack traces
- Bash: `git log --oneline -20 -- <affected-files>` to see recent changes
- Bash: `git blame <file>` on suspicious lines
- Context7: look up docs if fix touches a library
- Output: "Root cause hypothesis: …" + cited file:line evidence — printed for user review

**Phase 4 — Fix** (automatic)
- Apply edits using Edit/Write tools on the checked-out branch
- Scope limited to files implicated by the root cause; no drive-by changes

**Phase 5 — Validation** (automatic)
- Bash: run available test commands (detect from repo: `dotnet test`, `python -m pytest`, etc.)
- If `--unity` flag or `unity-mcp` is in active profile: call unity-mcp compile check
- Code-review plugin: self-review the diff for obvious issues
- If validation fails: attempt one auto-fix pass, then surface failure to user and pause

**Phase 6 — Commit** (automatic, local only)
- Bash: `git add -p` equivalent (stage only changed files by name, never `git add .`)
- Commit message format: `(PROJECT-123): <slug-from-title>`
- Body: root cause in 2-3 sentences

**Phase 7 — PR Body Generation** (automatic)
- Fill `.claude/pr-templates/bug-fix.md` with gathered data
- Write filled template to `/tmp/pr_body_<ticket>.md`
- Print the PR body for user review

**Phase 8 — Notify** (automatic)
- Bash: `python workflows/notify.py --ticket ... --branch ... --summary ... --pr-body-file ...`
- Print: "Commit done on `<branch>`. PR body written to `/tmp/pr_body_<ticket>.md`. **You push when ready.**"
- Never run `git push`

---

### 5. `.claude/commands/daily-triage.md`

Invoked as `/daily-triage` (no arguments needed).

Steps:
1. `atlassian` MCP: fetch issues assigned to me, ordered by updated date — status IN ("To Do", "In Progress", "In Review") — last 7 days
2. GitHub plugin: list open PRs where I'm a requested reviewer + open PRs authored by me with change requests
3. `gws-mcp`: list unread Gmail threads from last 24h with subject matching `[Jira]`, `[GitHub]`, or from team domains
4. Synthesize into a prioritized table:
   - **P0 (blocking)**: PRs with change requests on my branches, overdue bugs
   - **P1 (today)**: New bugs assigned, PRs awaiting my review
   - **P2 (this week)**: Feature tickets, informational email threads
5. For each item: print recommended next action (`/fix-bug`, `/review-pr`, "reply to email", etc.)

---

### 6. `.claude/commands/review-pr.md`

Invoked as `/review-pr <PR-URL>`.

Steps:
1. GitHub plugin: fetch PR diff, description, CI status, requested reviewers
2. Read changed files locally (if repo is cloned)
3. code-review plugin: run structured review
4. Output: structured findings (correctness bugs, design concerns, nits) with file:line refs
5. Ask: "Post review comments to GitHub? (yes/no/edit first)"
6. If yes: GitHub plugin posts inline comments + summary review

---

## Suggested Additional AI Steps (beyond user's original 7)

| Step | Where | Why |
|------|-------|-----|
| Confluence search after Jira fetch | Phase 1 | Surfaces architecture docs, previous similar fixes — prevents re-breaking something |
| `git log` blame trail before editing | Phase 3 | Identifies who last touched the code, recent related changes, avoids stepping on in-progress work |
| Regression surface identification | Phase 5 | After fix, identify callers/dependents of changed symbols so test plan is targeted |
| Code-review self-check before commit | Phase 5 | Catches obvious issues (null checks, edge cases) before human review |
| Unity headless compile | Phase 5 | Verifies C# doesn't have compile errors without needing the editor open |

---

## Verification

After implementation:

1. **Profile activation**: `cd mcp-servers && ./install.sh --profile config/profiles/dev-workflow.json` → verify `docker-compose.override.yml` contains unity-mcp, atlassian, gws-mcp, mcp-discord
2. **Notify script**: `python workflows/notify.py --ticket TEST-1 --branch test-branch --summary "test" --channel telegram` → Telegram message appears in your personal bot chat
3. **fix-bug command**: In Claude Code, run `/fix-bug <real-ticket-id>` on a test ticket → verify Phase 1-2 produce correct Jira data, Phase 4 creates branch, Phase 8 does not push
4. **daily-triage command**: `/daily-triage` → verify output table covers Jira, GitHub, Gmail sources
5. **Guard**: confirm `git push` never appears in any command file or notify.py

---

## Open Questions / Things to Confirm Before Implementing

1. **PR template**: The user mentioned they'll provide a template later — plan uses a reasonable default; they can edit `.claude/pr-templates/bug-fix.md` at any time
2. **Notification channel preference**: Telegram bot API is the simplest (one token, one chat ID, one HTTP POST). Gmail via gws-mcp requires service account credentials. Plan defaults to Telegram with Gmail as fallback
3. **Unity headless**: unity-mcp requires Unity Editor installed on the host. In isolated/cloned repos this may not be available — Phase 5 degrades gracefully to "no Unity validation, flagging for manual check"
4. **`/daily-triage` scheduling**: The user asked about a "fixed interval" trigger — Claude Code doesn't have a native cron scheduler, but `workflows/notify.py` could be called from a cron job or GitHub Action to trigger `/daily-triage` automatically. This can be a follow-up addition.