# Codex integration rules

This is the Codex adapter for the loop template. `.claude/` remains the shared
source of role behavior, workflow details, templates and tested shell hooks.
Read the relevant source Markdown body, but ignore Claude YAML frontmatter.
Codex agent TOML files choose models; `.codex/hooks.json` registers hooks.
Claude tool names in prose mean the equivalent Codex file, search and shell tools.
Claude `/loop-*`, `/orchestrate`, and `/retro` references mean Codex skills with
the same names (`$loop-init`, `$loop-plan`, `$orchestrate`, `$retro`, `$loop-handoff`).
“Opus escalation” means the configured Codex implementer; Claude model names do
not select Codex models. The main session keeps the user's model and effort.

## Start and verify

Linux/WSL prerequisites: Git, POSIX `sh`, Python 3.11+, and a Codex version with
custom TOML agents and the four lifecycle events in `.codex/hooks.json`.
The initial compatibility target is Codex CLI 0.154.0. Older clients have not
been validated. Native Windows Codex support is not included in this release.

Launch in the adopting project:

```sh
codex --approve-for-me
```

Codex 0.154.0 rejects combining `--sandbox workspace-write` with `--approve-for-me`.
`--approve-for-me` already selects workspace-write and automatic approval review.
Keep those permissions. Never use bypass flags or change global Codex settings.
Review and trust the project and hook definitions through Codex's `/hooks` UI.
Hook trust is distinct from automatic approval review; untrusted hooks are skipped.
Verify the eight custom agents appear in the loaded agent list. If any are
missing or a configured model is unavailable, report the capability blocker.
Do not substitute a generic agent and claim the configured role ran.

After initialization creates `loop/`, run this **standalone shell command inside
Codex**, from the project root (replace the path with its quoted absolute form
when running from a nested directory):

```sh
python3 .codex/hooks/loop.py doctor
```

The adapter requires a receipt from the actual `PreToolUse` event for this
session. Calling the script in an ordinary terminal is not a hook activation
test. Configuration presence alone proves nothing about trust or execution.

Before orchestrating, run:

```sh
python3 .codex/hooks/loop.py activate
```

The hook records the owning session and transcript in `loop/.codex-session.json`.
Stop warnings and compaction checkpoints require both identities to match.
Child sessions with a different transcript cannot replace the main handoff.
The original POSIX scripts still own audit parsing, checkpoint format and budget
warnings. Codex payloads are normalized to their existing input format.

After a deliberate handoff or when orchestration returns, run:

```sh
python3 .codex/hooks/loop.py deactivate
```

These commands must be standalone, not joined to `cd`, `&&`, pipes or a heredoc;
use the shell tool's working-directory argument. Activation fails if another
session owns the loop. If its process died, confirm it has stopped before
explicitly releasing `loop/.codex-session.json` and activating a new session.
Never clear another running session's marker to take over its work.

## Hook behavior and limits

- The destructive Git guard applies to shell calls throughout this adopting
  Codex project, including the main thread and child agents. It does not depend
  on whether `loop/` exists. Its command policy is the original template's.
- Audit events are limited to the seven spawned loop roles, excluding teacher.
  The hook writes the original five columns and canonical role names. It is
  observational: it records a returned verdict, not independent proof that
  the reported tests actually ran. Killed agents can still leave no stop event.
- The stop warning remains advisory. It never forces continuation. Compaction
  derives a checkpoint from durable files and never claims the tree is coherent.
- Hook failures are visible. An unreadable shell event is denied; audit or
  checkpoint failures warn without forcing an agent to continue.
- Codex hooks are guardrails for supported tool paths, not a complete security
  boundary. `write_stdin` input is not a new shell pre-tool event. Keep Codex's
  sandbox and approval review enabled; never describe the hooks as tamper-proof.
- Role read-only settings express intent but inherited live permission overrides
  may take precedence. Reviewers, the auditor and teacher must not edit files
  even when the parent session grants write access.

## State and adoption

Both tools use the same `loop/` files. Switch only after stopping the previous
orchestration session; concurrent Claude/Codex writers are unsupported. Keep
the profile, journal, lessons, handoff and task contracts unchanged. Put `Unit:`,
`Status:` and `Route:` on separate lines in new Codex packets so the existing
line-oriented hooks can parse them. On resuming older combined-line packets,
split those fields without changing their values before running stages.

Use `scripts/install-codex.py` from the template checkout. It copies both adapters,
preflights collisions and merges only missing hook entries. It never writes a
profile, seeds lessons, edits application files, or overwrites Codex config.
Changes to previously installed files are conflicts, not permission to replace
a project's customization. Installation is repeatable for identical files.

Under a local footprint, exclude only the installed loop paths; don't hide
unrelated `.agents/` or `.codex/` content. Always exclude `loop/AUDIT.log` and
`loop/.codex-session.json` from commits. Never untrack files without authorization.
Reinitialization must preserve journal, earned lessons, packets and handoff.

## References

- https://learn.chatgpt.com/docs/build-skills
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/hooks

## Branch transitions and hook recovery

Before switching or checking out another revision in an active Codex checkout,
run `python3 scripts/check-codex-branch.py TARGET` (or inspect the complete required
file set in the target commit if the helper is unavailable). Required files are
`.codex/hooks.json`, `.codex/hooks/loop.py`, and the four `.claude/hooks/` scripts:
`guard-git-destructive.sh`, `audit-subagent.sh`, `loop-guard.sh`, and
`precompact-checkpoint.sh`. Resolve ambiguous
checkout arguments first. A missing dependency means use a separate worktree;
do not remove the current session's hook files. Review hook changes even when
all files exist. This is a workflow preflight, not enforcement on external Git clients.

Registered commands contain their own fallback so deleting the adapter cannot
turn Python's exit 2 into a Stop continuation request. Lifecycle failures warn
without requesting continuation; shell checks deny when the adapter cannot run.
Restore missing files from an external terminal. Do not disable safety checks.
Changed hook definitions require review/trust through `/hooks` before live testing.
For existing installations, `scripts/install-codex.py DEST --migrate-hooks` updates
only exact legacy hook registrations, preserving unrelated hooks and customized
conflicts. Inspect the dry run first. It does not upgrade customized adapter files.


## Required governance

Run `$loop-governance` after initialization. The shared executable check in
`.claude/skills/loop-governance/scripts/governance.py` is required before
implementation/resume/commit and with `--phase publish` before publication.
Python 3.11+ applies to Claude and Codex. Preserve governance state during
re-detection; missing or stale records are pending. Planning and authorized
setup remediation remain available. Do not use Stop hooks to enforce this gate.
