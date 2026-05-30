Spawn a background agent to analyze this codebase and create or update CLAUDE.md, then immediately return control to the user.

Use the Agent tool with run_in_background=true and subagent_type="general-purpose". Pass this self-contained prompt to the agent:

---
Analyze the codebase at $CWD and create (or update) CLAUDE.md at $CWD/CLAUDE.md.

Steps:
1. Read README.md if it exists
2. Read all root-level config files (package.json, pyproject.toml, setup.py, Cargo.toml, go.mod, Makefile, requirements.txt, build.gradle, CMakeLists.txt, etc.)
3. List the top-level directory structure
4. Read key source files to understand the high-level architecture — how components connect, not what every file does
5. Check for .cursor/rules/, .cursorrules, or .github/copilot-instructions.md and incorporate their important content
6. If CLAUDE.md already exists, improve it rather than replacing from scratch

Write CLAUDE.md starting with exactly these two lines:
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Then include:
- Build/lint/test commands, including how to run a single test
- High-level architecture: how major pieces fit together (things that require reading multiple files to understand)
- Non-obvious conventions or constraints specific to this repo

Do NOT include:
- Generic development practices or obvious instructions
- Repetition
- A listing of every file/component (only what requires cross-file understanding to grasp)
- Sections not evidenced by the actual codebase
---

After spawning the agent, respond with exactly: "CLAUDE.md analysis is running in the background — you'll be notified when it's done."
