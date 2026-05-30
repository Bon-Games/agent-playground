# PR Review Workflow

**Usage:** `/review-pr <PR-URL>`

The PR URL is: $ARGUMENTS

---

## Step 1 — Fetch PR Data

Using the `github` plugin, fetch in parallel:
- PR diff (all changed files and their diffs)
- PR description and title
- CI/check status (passing/failing/pending)
- Existing review comments (if any)
- Requested reviewers and current review state

## Step 2 — Read Changed Files Locally

For each file in the diff that exists in the local working tree:
- Read the full file (not just the diff) to understand the surrounding context
- Note any callers or dependents of changed functions/classes

## Step 3 — Structured Review

Analyze the diff for:

**Correctness bugs** (high severity — must fix before merge):
- Null/nil dereference, index out of bounds, off-by-one errors
- Incorrect error handling or swallowed exceptions
- Race conditions or shared mutable state issues
- Logic errors that contradict the PR description

**Design concerns** (medium severity — worth discussing):
- API surface changes that break callers not in the diff
- Missing edge cases in conditional logic
- Patterns that will be hard to maintain or extend
- Duplication that could be extracted

**Nits** (low severity — optional cleanup):
- Naming inconsistencies with the surrounding codebase
- Unnecessary complexity
- Missing or misleading comments on non-obvious logic

Use the `code-review` plugin for an additional automated pass.

## Step 4 — Output Findings

Print findings in this format:

```
## PR Review: {PR title} — {PR URL}
CI: {status}

### Correctness Bugs
- **{file}:{line}** — {finding}. Suggested fix: {suggestion}

### Design Concerns
- **{file}:{line}** — {finding}.

### Nits
- **{file}:{line}** — {finding}.

### Overall
{2-3 sentence summary. Approve / Request changes / Comment.}
```

If there are no findings in a category, omit that section.

## Step 5 — Confirm Before Posting

After printing findings, ask:

> Post these review comments to GitHub? Options: **yes** / **no** / **edit first**

- **yes**: Use `github` plugin to post all findings as inline comments + a summary review
- **no**: End here — findings are in the conversation for the user to act on manually  
- **edit first**: Print the review in editable form, wait for user to paste back revised version, then post

Do NOT post to GitHub without explicit confirmation.
