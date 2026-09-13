# Governance validation

## Local executable and workflow validation

The gate has automated cases for missing/corrupt records, stale file and workflow
evidence, changed identity, unresolved gaps, absent approvals, unit and configuration
binding, API outages, solo/team review rules, classic and ruleset protection, and
publication checks on HEAD. CI runner regressions reject skipped twins, empty
suites and failed runners. Existing hook-recovery and installer cases remain in
its suite. The final measured counts and hosted run are recorded below after CI.

An independent skill forward-test used disposable repositories. It confirmed
that an existing project with no record blocks, user-approved local-only exceptions
work only for their unit, changed evidence blocks, resealing does not renew approval,
and reinitialization preserves the record and journal. These are executable local
scenarios, not evidence of an external human approving a GitHub PR.

## Hosted acceptance

Pending bootstrap CI and branch-protection adoption. Do not treat this section as
a successful hosted verification until the observed run and settings are recorded.

## Limits

Local records are mutable evidence, not signed attestations. The gate participates
in the loop workflow and does not intercept arbitrary external shell use. GitHub
server-side branch protection supplies enforcement on the remote branch.
Non-GitHub hosting and non-Actions CI require explicit scoped exceptions in v1.
The automated Windows job exercises original shell twins, not native Codex support.
Paid model routing and all lifecycle scenarios are not rerun by CI; the earlier
hook recovery evidence remains in docs/hook-recovery-validation.md.
