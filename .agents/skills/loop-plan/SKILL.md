---
name: loop-plan
description: Plan the next loop work unit and task packets, discussing consequential decisions before implementation. Requires an initialized loop profile.
---

Read [Codex integration rules](../../../.codex/LOOP.md), then the Markdown body of the [existing loop-plan workflow](../../../.claude/skills/loop-plan/SKILL.md). Both are required: the existing workflow supplies the tested stage behavior; this entrypoint adapts the harness. Ignore the source YAML frontmatter. The integration rules and substitutions below take precedence over harness-specific source text. User instructions and existing authorization take precedence over template approval checkpoints.

Follow the source workflow with these substitutions:
- Stay in the main session so decisions remain a conversation with the user. Use the source's built-in five-question short form. Offer another grilling skill only if the user has a compatible Codex skill and wants it; do not search Claude's plugin cache or require its marketplace command.
- Skip the source block from “Check for `mattpocock-skills:grill-with-docs`” through its plugin wait instructions; retain the two guards and short form below it.
- Respect Codex Plan mode: when active, explore without writing profile, packets, or probe edits; return the proposed plan. Write the loop artifacts after execution mode is enabled.
- Write `Unit:`, `Status:`, and `Route:` on separate lines in every packet, rather than the source's combined example header. The hooks parse line-start fields.
- Before replacing an existing unit, resolve any in-flight tasks with the user and preserve the previous plan and packets in a dated `loop/archive/` directory. Never clear an active unit just because a new request arrived.
