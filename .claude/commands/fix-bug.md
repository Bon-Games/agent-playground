# Fix-Bug Workflow

**Usage:** `/fix-bug <TICKET-ID>` or `/fix-bug <TICKET-ID> --unity`

Parse `$ARGUMENTS`:
- `TICKET_ID` = first word (e.g., `PROJECT-123`)
- `UNITY_MODE` = `true` if `--unity` appears anywhere in the arguments

**Safety rules — enforce throughout this entire workflow:**
- NEVER run `git push` or any variant (`--force`, `--set-upstream`, etc.)
- NEVER stage files with `git add .` or `git add -A` — always stage by explicit filename
- NEVER modify files outside the branch created/checked out in Phase 2
- Write state files at every phase boundary before continuing
- Hard-pause (ask the user) at the checkpoints marked **[PAUSE]** below

---

## Phase 1 — Jira Context

Call ALL of the following tools **simultaneously** (in parallel):

1. `atlassian` MCP → fetch the issue: `jira_get_issue(TICKET_ID)`
   - Extract: title, description, priority, status, reporter, fix-version, sprint name, labels, linked issues
2. `atlassian` MCP → fetch last 5 comments newest-first: `jira_get_issue_comments(TICKET_ID, maxResults=5, orderBy="-created")`
3. `atlassian` MCP → `confluence_search` — search for the component or system named in the ticket title
4. Bash: `git branch -r | grep -i "TICKET_ID"` — find existing remote branches for this ticket

**After fetching, evaluate comments:**

| Signal in comments | Action |
|-------------------|--------|
| References another ticket ID (e.g., `PROJ-456 is related`) | Fetch that ticket's summary; offer dive-deeper **[PAUSE]** |
| References a Confluence page URL | Note the URL; offer dive-deeper **[PAUSE]** |
| Total comment count > 10 AND newest comment is > 3 days old | Auto-fetch all comments (paginate with `startAt=0, maxResults=100`) |
| QA adds new reproduction steps not in the original description | Include in root-cause inputs; flag in context summary |
| Comments are clear and self-contained | Continue without pausing |

**Dive-deeper** (when offered and user confirms, or auto-triggered):
- Fetch full comment history
- Fetch linked ticket summaries (any ticket IDs mentioned in comments or the "Links" field)
- Fetch any Confluence page URLs mentioned in comments
- Update the context before writing the state file

**Write state file:** `.claude/workflow-state/TICKET_ID-YYYYMMDD/01-context.json`
```json
{
  "ticket_id": "TICKET_ID",
  "title": "...",
  "description": "...",
  "priority": "...",
  "status": "...",
  "fix_version": "...",
  "sprint": "...",
  "reporter": "...",
  "comments_summary": "Last N comments: ...",
  "confluence_docs": ["..."],
  "linked_tickets": ["..."],
  "existing_branches": ["..."]
}
```

Print the full context block for the user to read. Continue to Phase 2.

---

## Phase 2 — Branch Strategy

Load `01-context.json`. Using the `existing_branches` list and any GitHub PR search:

1. Search GitHub (`github` plugin) for open PRs with `TICKET_ID` in the title or branch name
2. Decide:

| Situation | Action |
|-----------|--------|
| Existing remote branch found | **[PAUSE]** "Found `fix/TICKET_ID-foo` on remote — use this branch? (yes/no)" |
| Open PR already exists | **[PAUSE]** "PR #N already exists for this ticket. Continue on that branch? (yes/no)" |
| No branch found, Jira sprint/fixVersion names a release branch | **[PAUSE]** "No branch found. I'll create `fix/TICKET_ID-<slug>` from `<release-branch>`. Confirm? (yes/no)" |
| No branch found, base branch is ambiguous | **[PAUSE — hard stop]** "Cannot determine base branch. Which branch should I use? (e.g., `main`, `develop`, `release/1.2`)" |
| No branch found, main/develop is clearly the base | **[PAUSE]** "No branch found. I'll create `fix/TICKET_ID-<slug>` from `develop`. Confirm? (yes/no)" |

The `<slug>` is derived from the ticket title: lowercase, hyphens, max 40 chars, no special chars.

After user confirms:
- If existing branch: `git checkout <branch-name>`
- If new branch: `git checkout -b fix/TICKET_ID-<slug> <base-branch>`

**Write state file:** `.claude/workflow-state/TICKET_ID-YYYYMMDD/02-branch.json`
```json
{
  "branch_name": "fix/TICKET_ID-...",
  "base_branch": "develop",
  "is_new_branch": true,
  "existing_pr_url": null
}
```

---

## Phase 3 — Root Cause Investigation

**Use the Agent tool to spawn a focused investigation sub-agent.**

Pass to the sub-agent:
- The full content of `01-context.json`
- The branch name from `02-branch.json`
- The following instructions:

> Investigate the root cause of this bug. You have access to File (Read), Bash, and context7 tools.
> 1. Read files mentioned in the ticket description or stack traces
> 2. Run `git log --oneline -20 -- <affected-files>` to see recent changes
> 3. Run `git blame <file>` on suspicious lines
> 4. If the bug involves a library, use context7 to look up the relevant API docs
> 5. Form a root cause hypothesis with evidence (cite file:line for every claim)
> 6. Return a compact JSON: { "hypothesis": "...", "evidence": [{"file": "...", "line": N, "note": "..."}], "affected_files": ["..."], "confidence": "high|medium|low" }
> Keep the response under 500 tokens. Hypothesis + evidence only — no fix suggestions yet.

Wait for the sub-agent to return. If `confidence` is `"low"`:
**[PAUSE]** "Root cause confidence is low. Here's the hypothesis: [print it]. Should I proceed with this hypothesis or investigate further? (proceed / investigate more)"

**Write state file:** `.claude/workflow-state/TICKET_ID-YYYYMMDD/03-root-cause.json`
(Use the JSON returned by the sub-agent exactly)

Print the root cause hypothesis and evidence for the user to review. Continue to Phase 4.

---

## Phase 4 — Fix

Load `03-root-cause.json`. Apply edits to the codebase:

- Use the Edit or Write tools to modify **only** the files listed in `affected_files`
- Do not make drive-by changes to unrelated code
- Do not reformat files unless formatting was the bug
- For Unity/C# bugs: keep changes minimal; match the surrounding code style
- If the fix requires more than 5 file changes, **[PAUSE]** and explain the scope to the user before continuing

**Write state file:** `.claude/workflow-state/TICKET_ID-YYYYMMDD/04-diff.json`
```json
{
  "changed_files": ["path/to/file.cs", "..."],
  "change_summary": "One sentence per file describing what changed and why"
}
```

---

## Phase 5 — Validation

Run all applicable checks:

**Automated tests** (detect from repo structure):
- C#/.NET: `dotnet test` (if `.sln` or `.csproj` found)
- Python: `python -m pytest` (if `pytest.ini` or `tests/` found)
- Other: check for `Makefile` test target or `package.json` scripts

**Unity compile check** (if `UNITY_MODE` is true OR `unity-mcp` is in the active MCP config):
- Use `unity-mcp` to trigger a headless compile check
- If Unity Editor is not available, log "Unity validation skipped — Editor not found" and continue

**Self-review** (`code-review` plugin):
- Run an automated review of the diff (`git diff HEAD`)
- Include findings in the validation state file

**If any check fails:**
- Attempt one auto-fix pass (read the error, apply a targeted fix, re-run)
- If it still fails: **[PAUSE — hard stop]** "Validation failed after auto-fix attempt. Here's the error: [print it]. How should I proceed? (fix manually / skip and continue / abandon)"

**Write state file:** `.claude/workflow-state/TICKET_ID-YYYYMMDD/05-validation.json`
```json
{
  "tests_run": ["dotnet test"],
  "tests_passed": true,
  "unity_compile": "passed|skipped|failed",
  "self_review_findings": ["..."],
  "overall": "passed|failed"
}
```

---

## Phase 6 — Commit (local only)

Stage and commit **only** the files in `04-diff.json`'s `changed_files` list:

```bash
git add <file1> <file2> ...   # explicit filenames only — NEVER git add .
git commit -m "(TICKET_ID): <slug-from-title>

Root cause: <1-2 sentences from 03-root-cause.json hypothesis>
Fixes: TICKET_ID"
```

**Write state file:** `.claude/workflow-state/TICKET_ID-YYYYMMDD/06-commit.json`
```json
{
  "commit_hash": "...",
  "commit_message": "...",
  "branch": "..."
}
```

---

## Phase 7 — PR Body Generation

Fill in `.claude/pr-templates/bug-fix.md` with all gathered data:
- Summary: one-line fix description from the commit message
- Jira: ticket URL (construct from `JIRA_URL` env var + `/browse/TICKET_ID`)
- Root Cause: from `03-root-cause.json` hypothesis + cited evidence
- Evidence: stack traces / QA notes from ticket comments (quoted verbatim)
- Fix Description: from `04-diff.json` change summary
- Reproduction Steps: from QA comments or ticket description
- Test Plan: based on `05-validation.json` + callers of changed functions
- Risk: any side effects identified in the self-review

Write the filled template to: `/tmp/pr_body_TICKET_ID.md`

Print the full PR body for the user to review.

**Write state file:** `.claude/workflow-state/TICKET_ID-YYYYMMDD/07-pr-body.md`
(Same content as `/tmp/pr_body_TICKET_ID.md`)

---

## Phase 8 — Notify

Run:
```bash
python workflows/notify.py \
  --ticket TICKET_ID \
  --branch <branch-name-from-02-branch.json> \
  --summary "<one-sentence summary of the fix>" \
  --pr-body-file /tmp/pr_body_TICKET_ID.md \
  --channel telegram
```

**Write state file:** `.claude/workflow-state/TICKET_ID-YYYYMMDD/08-notification.json`
```json
{
  "channel": "telegram",
  "sent_at": "ISO timestamp",
  "status": "sent|failed"
}
```

Print this final message:

```
✓ Fix complete on branch `<branch>`.
  PR body: /tmp/pr_body_TICKET_ID.md
  State: .claude/workflow-state/TICKET_ID-YYYYMMDD/

Push when ready:
  git push origin <branch>

Then open a PR using the PR body above.
```

**The workflow is done. Do NOT run `git push`.**
