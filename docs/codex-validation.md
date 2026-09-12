# Codex compatibility and validation

Baseline: upstream commit `043796e9405968d79257f0c66997395fda8ff9d3`.
Environment: Linux, Codex CLI `0.154.0`, Python 3.14.7.

## Automated checks

- `python3 -m unittest discover -s tests/codex -v`: 24 tests passed, including installer preservation and
  collision checks; Codex command/payload translation; original Git and audit
  fixtures; missing/null reports; session and transcript scoping; checkpoint
  counters; blocked tasks; activation/deactivation; one-use hook receipts;
  malformed inputs and missing hook scripts.
- `sh tests/run-guard-tests.sh --sh-only`: 39 cases passed.
- `sh tests/run-audit-tests.sh --sh-only`: 23 cases passed.
- All five Codex skills pass the skill-creator validator. All eight custom-agent
  definitions parse as TOML. Their selected models and effort levels are present
  in the installed CLI's bundled catalog; that is not a guarantee of account access.
- The `.claude/` tree and original tests are unchanged from the baseline.

PowerShell is not installed here. The `.ps1` twins were not executed; their source
files are unchanged. Native Windows Codex integration is outside this release.

## Live CLI check

The requested `codex --sandbox workspace-write --approve-for-me` exits with a CLI
argument conflict before starting. The supported equivalent is
`codex --approve-for-me`: its CLI help explicitly selects workspace-write and
automatic approval review. No sandbox or approval bypass flags were used.

A disposable Git repository with a Python function and unittest suite was installed
using the installer. Codex loaded project configuration, displayed the four project
hooks for review, and ran `python3 .codex/hooks/loop.py activate` successfully through
its real PreToolUse event. Only the four project hooks were trusted; unrelated
plugin hooks were left untrusted.

After account usage became available again, the fixture completed the full
applicable pipeline. The first builder exposed a portability defect: this runtime
has no explicit agent-close tool. The skill was corrected to close agents only
when the tool is available, then the recorded handoff resumed at independent
testing without rebuilding or resetting the first-attempt counter.

Observed results:

| Stage | Actual model | Result |
|---|---|---|
| Builder | `gpt-5.6-sol` | Fixed increment; three focused tests passed and failed against the old implementation |
| Independent test runner | `gpt-5.6-luna` | Three tests passed |
| Code reviewer | `gpt-5.6-sol` | APPROVED |
| Docs writer | `gpt-5.6-sol` | Recorded task completion |
| Unit verification | `gpt-5.6-luna` | TESTS PASSED |
| Security auditor | `gpt-6-astra` | NO FINDINGS |

Actual session metadata confirmed model selection. The corresponding real
SubagentStop records preserved role, task and verdict attribution, including `-`
for unit-level work. The fixture was not committed or pushed. Runtime application
verification was correctly skipped because this fixture is a pure function.

An additional real `/compact` probe generated `loop/HANDOFF.md` for a pending
T-002 fixture packet, preserving `attempt 2 of 3`, marking the handoff active,
and correctly reporting that no stage verdict existed yet. It recorded the actual
dirty files without claiming to assess tree coherence. No code was implemented
for the checkpoint-only packet.

Child session/transcript isolation and blocked-task checkpoint selection are also
covered by synthetic lifecycle tests. Automatic compaction was not separately
triggered; the configured hook matches both manual and automatic events.
Direct-route promotion, prerequisite failures
and empty-suite routing retain the referenced source instructions; they have not
been separately exercised through a live Codex model run.

## Reproduce the end-to-end acceptance check

1. Use a disposable project with a known failing behavior, a real test suite and a
   committed baseline. Install the template, launch Codex, review the project hooks,
   and check the named custom agents resolve.
2. Run `$loop-init`, then `$loop-plan` for a small observable fix. Choose no commits
   or pushes for the fixture. Confirm the profile and packet before execution.
3. Run `$orchestrate`. Confirm the builder changes the fixture, the independent
   test runner measures its results, the reviewer approves the actual diff, and the
   docs writer records completion. Check the unit-close security audit separately.
4. Compare `loop/AUDIT.log` with the actual child reports: task ids, roles and
   verdicts must agree. A missing event, skipped test or failed model request must
   not be reported as success.
5. Pause a later task with `$loop-handoff`, resume, and confirm its retry counter
   and stage survive. Trigger manual compaction during orchestration and inspect
   the checkpoint. A child compaction must not replace the parent's handoff.

The shell hooks retain their original command-matching policy. They are not a
complete enforcement boundary for arbitrary tools or code. The sandbox and automatic
approval review remain part of the runtime configuration.

## Updating from the original template

Keep `upstream` pointing at DanielMJ511/loop-template and use a separate feature
branch to review future changes. The Codex skills and agents reference the original
Markdown bodies, so upstream behavioral changes require a compatibility review even
when the adapter itself has no diff. Re-run both original suites and the Codex tests.
Do not overwrite an adopting project's conflicting files or reseed its `loop/` state
as an update mechanism.
