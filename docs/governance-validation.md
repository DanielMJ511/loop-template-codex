# Governance validation

## Local executable and workflow validation

The gate has automated cases for missing/corrupt records, stale file and workflow
evidence, changed identity, unresolved gaps, absent approvals, unit and configuration
binding, API outages, solo/team review rules, classic and ruleset protection, and
publication checks on HEAD. CI runner regressions reject skipped twins, empty
suites and failed runners. Existing hook-recovery and installer cases remain in
its suite. 60 Python tests passed locally on Python 3.14.7. Both new skills passed the
skill-creator validator; CI YAML parsed and action references are pinned. Hosted
Python 3.11/3.14 and shell-twin execution remains pending.

An independent skill forward-test used disposable repositories. It confirmed
that an existing project with no record blocks, user-approved local-only exceptions
work only for their unit, changed evidence blocks, resealing does not renew approval,
and reinitialization preserves the record and journal. These are executable local
scenarios, not evidence of an external human approving a GitHub PR.

## Hosted acceptance

The bootstrap PR is [#1](https://github.com/DanielMJ511/loop-template-codex/pull/1).
Hosted run [34787380951](https://github.com/DanielMJ511/loop-template-codex/actions/runs/34787380951)
passed Python 3.11/3.14 and both shell implementations on Ubuntu 24.04 and
Windows 2022. Both runtimes executed all 39 guard and 23 audit fixtures.

After that run, the repository's main protection was configured and read back:
PRs required, admin enforcement enabled, CI required bound to GitHub Actions
(app 15368), up-to-date checks and resolved conversations required, force pushes
and deletion disabled. A protected merge attempt during the correction's pending
CI was refused with "the base branch policy prohibits the merge". No bypass or
auto-merge flag was used.

The live publication gate returned ready=true against the successful bootstrap
commit and actual GitHub settings. This integration probe found a trailing-slash
metadata URL defect; the correction has a regression test. Final merge and release
must wait for required checks on the correction and on the resulting main commit.

The initial workflow push required adding workflow scope through GitHub's normal
device authorization flow. It was retried only after authorization completed.

## Limits

Local records are mutable evidence, not signed attestations. The gate participates
in the loop workflow and does not intercept arbitrary external shell use. GitHub
server-side branch protection supplies enforcement on the remote branch.
Non-GitHub hosting and non-Actions CI require explicit scoped exceptions in v1.
The automated Windows job exercises original shell twins, not native Codex support.
Paid model routing and all lifecycle scenarios are not rerun by CI; the earlier
hook recovery evidence remains in docs/hook-recovery-validation.md.
