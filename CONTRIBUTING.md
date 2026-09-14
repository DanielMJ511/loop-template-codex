# Contributing

Use a feature branch or separate worktree. Before switching an active Codex
checkout, run `python3 scripts/check-codex-branch.py TARGET`. An incompatible
revision belongs in a separate worktree. Preserve unrelated local changes.

Python 3.11+, Git and POSIX sh are required for both loop integrations.
GitHub governance verification also needs authenticated `gh`. Cross-platform hook
validation needs PowerShell (`pwsh`); Git Bash supplies sh on Windows. Codex
integration is supported on Linux/WSL; running Claude's Windows hook tests does
not establish native Windows Codex support.

After loop-init, run loop-governance. Its executable check is required before
normal implementation and publication; planning and authorized governance-only
remediation remain available when it is pending. See
[governance](docs/governance.md) for exceptions and migration.

Run these checks from the repository root:

```
python3 scripts/ci-tests.py python
python3 scripts/ci-tests.py twins
```

The twins command requires both implementations to execute. A skipped interpreter
or empty suite is a failure. A local `--sh-only` run is useful during iteration,
but is not a substitute for the required CI matrix. Live Codex lifecycle/model
tests require a disposable trusted session and account access; never claim a
synthetic payload test proves runtime behavior. Record applicable live evidence.

Every change goes through a pull request and the `CI required` check. The branch
must be up to date and review conversations resolved. This project's initial
solo-maintainer policy does not require a second-person approval. Add independent
approval when another maintainer is available; AI review is not a human approval.
Use squash merges with a concise `feat:`, `fix:`, `docs:` or `test:` title. Do not
force-push/delete main or bypass its protections for ordinary changes.

PRs should explain the concrete problem, resulting behavior, test evidence,
compatibility and migration effects. Fix documentation alongside behavior changes.
Use a regression that fails before the fix for a reproduced defect. Do not add
word-matching tests that only prove instructions contain their own wording.

See [release policy](RELEASING.md) for publishing and rollback. Public issues are
for bugs and proposals; do not include credentials or private session transcripts.
