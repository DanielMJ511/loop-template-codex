# Hook recovery validation

Validated on 2026-09-13 with Codex CLI 0.154.0 on Linux.
Baseline implementation: 476a080. Original Claude files remain unchanged.

## Automated results

- 35 Codex tests passed (`python3 -m unittest discover -s tests/codex -q`).
- Original POSIX guard suite: 39 cases passed.
- Original POSIX audit suite: 23 cases passed.
- `git diff --check` passed.

The registered-command regression reproduces exit 2 from the old launcher with
loop.py absent. New registered commands return JSON and exit 0 for missing
adapter files, missing Python, startup crashes, exit 2, malformed output and
missing Git roots. Lifecycle fallbacks are advisory; PreToolUse explicitly denies.
Tests use nested paths with spaces and remove the entire adapter directory.
A disposable branch transition confirms the target preflight refuses missing
hook files without changing HEAD, and restored files restore normal behavior.
Installer tests cover exact legacy migration, backup, dry run, repeatability,
unrelated hooks and refusal of customized definitions, including a custom
registration alongside a recognized one.

## Real session acceptance

Fixture: /tmp/loop-hook-live. Session:
01a09b16-64b1-7bf3-b680-230857a60323.
Launched with `codex --approve-for-me --no-alt-screen -C /tmp/loop-hook-live`.
Reviewed the four project hook definitions and trusted them through the normal
CLI UI. No hook-trust or sandbox bypass flags were used.

1. The guard denied a harmless echo containing a blocked command phrase. The
   tool result, not only the assistant report, confirmed PreToolUse denial.
2. The external fixture controller moved loop.py to a backup. A tool-free
   response completed with STOP_PROBE_COMPLETE. The UI showed one advisory
   missing-adapter warning. The session remained idle for over 30 seconds;
   no automatic continuation prompt appeared.
3. With the adapter still absent, one pwd command was explicitly denied by
   PreToolUse. That turn completed and its Stop warning did not restart it.
4. The controller restored the exact file. A new pwd command succeeded with
   exit 0 and returned the fixture path.

The rollout records four completed turns and zero injected `<hook_prompt>` user
messages. The fixture's adapter was restored after testing. No missing-file
probe was run against the user's active checkout.

## Limits

The branch helper verifies required blobs exist in a resolved destination commit;
it does not prove their behavior or intercept arbitrary external Git clients.
Agents must review hook changes and use a separate worktree for incompatible
revisions. The registered fallback protects against adapter removal even when
that workflow rule is not followed.

Native Windows and the PowerShell twins were not exercised. This run did not
repeat full loop orchestration, model routing or manual compaction acceptance.
Other plugins can independently request continuation; this fix does not disable
them. Updated registrations require normal `/hooks` trust review in each project.
