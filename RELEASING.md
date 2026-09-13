# Release policy

This template uses semantic tags `vMAJOR.MINOR.PATCH`, beginning at v0.1.0.
Before 1.0, changes to prerequisites or workflow contracts require a minor
release; compatible fixes use patch releases. Preserve existing published tags.
The copied machinery also carries a date stamp, distinct from the release tag.

Publish only when authorized. Merge through a passing, protected PR; fetch the
resulting main commit and require CI success on that exact commit. Complete the
applicable disposable live workflow probes, record unsupported cases, and run
the governance validator with `--phase publish`. Update CHANGELOG.md with
compatibility, prerequisites, migration steps and measured verification.

Create the version tag at the verified main commit and publish a GitHub release
whose notes identify that commit and link to the changelog. Do not silently
retag or publish from an unverified feature-branch SHA. GitHub's source archives
are the release artifact; the repository has no compiled package to publish.

Adopters should download a tagged version, inspect their installed-file diff and
run the installer dry run. Customized files remain conflicts; preserve their
content and all loop state while reviewing the migration. Installation never
reseeds earned lessons or replaces a journal. New governance machinery is
mandatory for normal implementation; older projects begin pending, not exempt.
Python 3.11+ is now required for Claude as well as Codex. Review changed hooks
through the client's normal trust UI.

To roll back a faulty release, preserve the current project and loop state,
restore the previous known-good machinery from its pinned tag, and recheck hooks
and compatibility before resuming. Do not switch an active checkout to a revision
without its hook dependencies. Publish the correction as a new version and mark
the affected release in its notes; do not move the old tag.
