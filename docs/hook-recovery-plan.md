# Prevent hook failures from causing continuation loops

Status: implemented and validated; see hook-recovery-validation.md for measured results.

## Evidence and scope

Switching from `feat/codex-support` to the older local `main` removed the tracked
`.codex/hooks/loop.py` while the session retained its hook registration. Python
exited 2 before adapter error handling could run. Stop interpreted that exit as
a continuation request; the shell hook also failed, blocking recovery.

Current checkout: local `main` at `043796e`, tracking `upstream/main`. The Codex
implementation is on `feat/codex-support` at `476a080`. Untracked files observed
are Python bytecode caches; preserve them during preparation. Existing tests
cover a missing downstream shell script, not a missing adapter entrypoint.

Implement a resilient event-specific launcher and a branch-transition preflight.
Do not disable hooks, weaken sandbox settings, or change the original Claude
hook policy. Warp's resolved jq dependency issue is outside this change.

## 1. Prepare an isolated implementation checkout

- Inspect actual refs and untracked files before changing any branch.
- Create a separate worktree based on the Codex implementation for this fix;
  do not switch the active checkout to reproduce the incident.
- If needed, repair local main by fast-forward only after checking collisions
  and the target hook files; set its tracking branch to origin/main.
- Preserve unrelated files and record the baseline test results.

## 2. Reproduce the failure safely

- Create a disposable repository with one revision containing the adapter and
  a second revision without it. Save the registered hook commands outside the
  fixture so the harness can simulate a session retaining its configuration.
- Invoke the actual old Stop command before and after switching the fixture
  to the revision without the adapter. Capture exit status, stdout and stderr.
- Demonstrate exit 2 and the missing-file diagnostic without starting an
  unbounded live continuation loop. Bound the synthetic continuation simulation.
- Probe PreToolUse separately with a harmless command and missing adapter.
- Cover both missing adapter and missing whole .codex directory, including
  invocation from a nested directory and repository paths containing spaces.

## 3. Implement resilient registered commands

- Put a minimal POSIX shell fallback directly in each registered command.
  It must survive removal of every tracked adapter file. A separate tracked
  launcher alone is insufficient.
- Give each launcher its event explicitly; do not require Python or jq merely
  to determine fallback behavior. Preserve stdin for the actual adapter.
- Capture adapter execution and validate its response at the appropriate
  boundary. Handle missing interpreter, missing file, startup exception,
  nonzero exit and malformed output without leaking accidental exit 2 into Stop.
- For Stop infrastructure failure, emit one concise JSON systemMessage and
  exit 0, with no continuation decision. The loop's Stop policy remains advisory.
- For SubagentStop and PreCompact failures, emit a visible advisory error;
  never invent audit or checkpoint success. Orchestration must still detect
  missing evidence and stop its work.
- For PreToolUse infrastructure failure, return an explicit deny with a useful
  repair reason. Never silently allow an unchecked command.
- Preserve valid guard decisions and activation receipts. Do not use a blanket
  `|| true` or globally disable other plugins' continuation behavior.
- Verify fallback warning frequency in the live probe. If runtime behavior
  requires deduplication, scope it narrowly to the same event/turn/failure;
  never hide later independent failures.

## 4. Prevent branch transitions that remove active hooks

- Add an explicit preflight for agent-initiated checkout/switch operations:
  resolve the target revision and verify the complete required hook file set
  before changing the active working tree.
- Check availability at the destination, not only in the current checkout.
  If the target lacks required files, use a separate worktree and leave the
  active session's files intact. Ambiguous destinations require inspection.
- Document this procedure in Codex integration rules and applicable workflow
  instructions, with a small testable helper if useful for consistent checks.
- Treat this as an agent workflow safeguard, not a claim to intercept every
  external Git client or arbitrary shell program. The resilient launcher covers
  files disappearing outside that workflow.

## 5. Installer and regression coverage

- Update hook registration and installer recognition together. Existing exact
  registrations must not be duplicated; customized definitions remain conflicts.
- Provide a reviewable migration for existing installations, preserving backups
  and unrelated hooks. Changed registrations need normal hook trust review.
- Add tests that execute commands extracted from hooks.json rather than only
  importing loop.py. Include valid allow/deny, missing Python, missing adapter,
  crash/exit 2, malformed output, nested paths and absence of the Git root.
- Check the branch preflight accepts a complete destination and rejects one
  missing the adapter or a required downstream script before any checkout.
- Re-run Codex installer/hook tests and both original POSIX suites. Confirm the
  original Claude files and policies are unchanged. Report untested platforms.

## 6. Live acceptance and delivery

- Use a fresh disposable Codex session with reviewed/trusted new definitions.
  Arrange an external recovery path and a bounded monitoring window first.
- Establish that the shell guard works. Remove the fixture adapter from an
  external fixture controller, then let the session finish one response.
- Verify the real Stop event reports the missing adapter once, completes the
  turn, and produces no automatic continuation prompt. Confirm using lifecycle
  evidence, not the assistant's statement that it finished.
- In a separate probe, confirm missing-adapter PreToolUse denies a harmless
  command. Restore the fixture externally and verify normal operation resumes.
- Exercise the preflight against an incompatible destination and confirm the
  active checkout does not change; work proceeds in a separate worktree.
- Record exact commands, runtime version, outputs and limitations in validation
  documentation. If the live runtime is unavailable, keep acceptance pending.
- Review the final diff, commit the fix and follow the existing publication
  authorization. Do not claim this plan or synthetic tests prove live acceptance.

## Completion criteria

The old configured command demonstrably reproduces the missing-file exit 2.
The replacement Stop command warns and ends without continuation when its
adapter disappears. PreToolUse still denies when it cannot check a command.
The branch preflight prevents the original transition in the active checkout.
Installer migration preserves existing customization, regression suites pass,
and the bounded live fixture verifies the turn actually ends.
