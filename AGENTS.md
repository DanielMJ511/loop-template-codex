# Working on this template

Before changing the active checkout's branch or revision, run
`python3 scripts/check-codex-branch.py TARGET` and review changes to the registered
hooks and their dependencies. If the helper is unavailable, inspect the target
commit for every file listed in `.codex/LOOP.md`'s branch-transition procedure.
Do not switch this session to a revision missing required hook files. Use a
separate worktree instead. Check the working tree for unrelated files first.

Treat hook infrastructure failures as failures to run a check, not as successful
checks or requests to retry indefinitely. Preserve the shell guard's denial on
failure. Never repair a missing guard by replacing it with a permissive stub.


After initialization, complete loop-governance before normal implementation.
Run its shared Python check before implementation/resume/commit and with
`--phase publish` before publishing. Missing or failed records block normal work;
only explicitly authorized governance remediation may bootstrap its own gate.
Never use a Stop hook to retry governance failures. Preserve explicit exceptions
and user approvals; planning remains available while pending.
