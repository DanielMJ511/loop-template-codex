# Changelog

## v0.1.0

- Add the required loop-governance workflow for Claude and Codex, with an
  executable gate, measured GitHub verification and scoped user-approved exceptions.
- Require Python 3.11+ for both integrations. Existing projects must complete
  governance before resuming implementation; planning remains available.
- Add CI for Python 3.11/3.14 and Linux/Windows shell twins, contribution guidance,
  protected-PR development and this versioned release policy.
- Include the Codex adapter and the verified missing-hook recovery fix.
- Preserve existing project customization and earned loop state during adoption.

See docs/governance.md for migration and docs/governance-validation.md for
measured results and limitations. Native Windows Codex support remains deferred.
