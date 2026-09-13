---
name: loop-init
description: Detect project commands, conventions and git policy, then initialize or refresh the loop profile. Use when adopting the loop or explicitly requesting loop-init.
---

Read [Codex integration rules](../../../.codex/LOOP.md), then the Markdown body of the [existing loop-init workflow](../../../.claude/skills/loop-init/SKILL.md). Both are required: the existing workflow supplies the tested stage behavior; this entrypoint adapts the harness. Ignore the source YAML frontmatter. The integration rules and substitutions below take precedence over harness-specific source text. User instructions and existing authorization take precedence over template approval checkpoints.

Follow the source workflow with these substitutions:
- Before detection, verify Python 3.11+, Git, POSIX sh, the eight Codex agents, and the four configured hooks are available. Read `.codex/hooks.json`; do not claim hooks ran just because the file exists.
- Replace source step 7b with the hook setup in `.codex/LOOP.md`. Never change Claude agent frontmatter or install a Claude plugin for Codex.
- For the local footprint, examine tracked paths first and exclude only untracked installed loop files. Include `.agents/skills/<each loop skill>/`, `.codex/agents/<each loop agent>.toml`, `.codex/hooks/loop.py`, `.codex/LOOP.md`, `.codex/hooks.json`, `.codex/loop-installed.json`, `.claude/`, and `loop/` where applicable. Preserve unrelated tracked config; disclose any committed footprint instead of claiming it is hidden. Use `git rev-parse --git-path info/exclude` for worktree-aware exclusion.
- Always exclude `loop/.codex-session.json` and `loop/AUDIT.log` from commits.
- Preserve pre-existing `loop/` files even on partial adoption: create missing initial files, never reseed existing lessons or replace a journal. Re-detection changes the profile and appends its journal entry only.
- At the end, run the standalone doctor command from `.codex/LOOP.md` inside Codex to confirm the PreToolUse hook actually fires. Missing hook trust is an incomplete setup, not success.


## Required next workflow

Require Python 3.11+ for the governance validator in both integrations. After
initialization, the next required step is loop-governance, not implementation.
If loop/GOVERNANCE.json is absent, report governance pending; never assume older
installations are exempt. Preserve existing governance records and summaries on
re-detection. Changed profile/workflow evidence requires reassessment. Planning
remains available, but orchestration and publication require the executable gate.
