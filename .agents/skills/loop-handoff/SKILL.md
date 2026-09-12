---
name: loop-handoff
description: Checkpoint an in-flight loop task, stage, retry counter and tree state for a later orchestration session. Use when pausing or handing off loop work.
---

Read [Codex integration rules](../../../.codex/LOOP.md), then the Markdown body of the [existing loop-handoff workflow](../../../.claude/skills/loop-handoff/SKILL.md). Both are required: the existing workflow supplies the tested stage behavior; this entrypoint adapts the harness. Ignore the source YAML frontmatter. The integration rules and substitutions below take precedence over harness-specific source text. User instructions and existing authorization take precedence over template approval checkpoints.

Follow the source workflow in the main session. Preserve the existing handoff format and `Status: active` contract so either tool can resume. Read the packet's persisted retry counter and inspect the working tree. After writing the handoff and journal entry, deactivate the Codex orchestration session using `.codex/LOOP.md` so a later unrelated compaction cannot overwrite this considered checkpoint.
