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
