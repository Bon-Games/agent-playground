# Daily Developer Triage

Execute the following steps to produce the daily priority list.

---

## Step 1 — Parallel Data Fetch

Call ALL of the following tools simultaneously (in parallel, not sequentially):

1. **Jira** (`atlassian` MCP) — search for issues assigned to me:
   - JQL: `assignee = currentUser() AND status IN ("To Do", "In Progress", "In Review", "QA", "Reopened") AND updated >= -7d ORDER BY updated DESC`
   - Fetch: key, summary, priority, status, updated date, fix version, sprint name

2. **GitHub** (`github` plugin) — two queries in parallel:
   - Open PRs where I am a requested reviewer (state: open, review-requested: me)
   - Open PRs authored by me that have change-requests or are blocked

3. **Gmail** (`gws-mcp`) — unread threads from last 24h where:
   - Subject contains `[Jira]` or `[GitHub]` or `Jira` or `pull request`
   - OR sender domain matches team domains
   - Fetch: subject, sender, snippet, received time

---

## Step 2 — Classify and Prioritize

Organize all items into three tiers:

### P0 — Blocking (handle first, today)
- My PRs with change-requests pending from reviewers
- Bugs assigned to me that are overdue (past sprint end or fix-version date)
- Tickets that QA has re-opened or moved to "Reopened" in the last 24h
- PRs where CI is failing on my branch and a reviewer is waiting

### P1 — Today
- New bugs assigned to me in the last 24h
- PRs awaiting my review (prioritize oldest first)
- Tickets moved to "In Review" status awaiting my action
- QA tickets updated in last 24h (new comments, new repro steps)

### P2 — This Week
- In-progress feature tickets without updates in last 48h
- Email threads that need a reply but are not urgent
- New feature planning tickets assigned or mentioned in

---

## Step 3 — Output

Print a triage report in this exact format:

```
# Daily Triage — {TODAY'S DATE}

## P0 Blocking
| ID/URL | Type | Title/Subject | Recommended Action |
|--------|------|--------------|-------------------|
| ...    | Bug  | ...          | /fix-bug PROJ-123 |

## P1 Today
| ID/URL | Type | Title/Subject | Recommended Action |
|--------|------|--------------|-------------------|

## P2 This Week
| ID/URL | Type | Title/Subject | Recommended Action |
|--------|------|--------------|-------------------|

## Summary
{One paragraph summarizing the day's workload — suitable for a Telegram notification}
```

Recommended actions should use slash commands where applicable:
- Jira bug → `/fix-bug TICKET-ID`
- PR to review → `/review-pr <PR-URL>`
- My PR with change request → `/fix-bug TICKET-ID` (if linked) or describe action
- Email → "Reply to: <subject>"

If any tier has no items, print `_Nothing in this tier today._`

At the very end, print just the Summary paragraph again on its own line, prefixed with `TRIAGE_SUMMARY:` — this is used by the scheduler to extract the notification text.
