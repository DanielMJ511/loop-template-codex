# Required development governance

Run `/loop-governance` in Claude or `$loop-governance` in Codex after initialization.
Python 3.11+ is required for both. GitHub inspection uses authenticated `gh` with
read access to checks and effective branch protections. Settings changes need
administrative access and authorization; lack of access is not a successful check.

The workflow assesses existing CI, PR/branch protections, contributor guidance and
a suitable release/deployment policy. It preserves stronger existing rules and
adapts to solo or team maintenance. Planning remains available. Normal implementation,
resume, commit and publication must pass the executable gate. CI setup and related
policy remediation may bootstrap themselves in a bounded governance-only workflow.
This allowance must not be used to implement unrelated features.

The gate lives in `.claude/skills/loop-governance/scripts/governance.py`. It uses
`loop/GOVERNANCE.json` and fingerprints the profile, workflows and policy evidence;
`loop/GOVERNANCE.md` explains the assessment. Check results are computed, never
accepted from a top-level passed flag. The JSON record is local mutable workflow
state, not a signature or a security boundary. GitHub branch protection enforces
PRs and checks at the server independently of agent instructions.

## Policy and exceptions

Default GitHub policy requires PRs, successful required CI, resolved conversations,
up-to-date branches, and prevention of default-branch deletion/force pushes. Solo
projects need no unavailable second reviewer; team projects require one independent
approval. Preserve stronger project rules. Do not override inherited organization
policies. Release policy is required, but local projects need not publish a tag.

The current verifier supports GitHub Actions checks and classic protection or
active branch rules. Other hosting/CI providers require explicit, scoped exceptions
for the controls the verifier cannot independently establish. Keep their real
validation evidence in the assessment. Missing tests, missing permissions and
network failures are gaps or unverifiable evidence, not automatic exemptions.

Every exception requires the user's actual approval reference, approver, rationale,
scope and a binding to the current project configuration. Configuration changes
invalidate that approval; resealing alone does not renew it. Offline exceptions
apply only to the explicitly named work unit. Pass that unit when invoking the gate.

A gate failure returns exit 1 and a finite list of blockers. It does not activate
orchestration, spawn builders, retry in the background or request Stop continuation.
The workflow ends normally and identifies the separate remediation needed.

## Existing project migration

Update the machinery from a pinned release in a separate checkout; inspect the
installer dry run. Existing customized files remain conflicts for explicit review,
not permission to overwrite. The installer copies the governance skill and helper
with the rest of `.claude/`; Codex receives its thin entrypoint too. Preserve
profile, journal, lessons, tasks, handoff and existing governance records. The
installer never initializes or replaces these records. Keep their existing local
or committed footprint; the workflow does not publish local approval transcripts.

Older projects without a record start pending. Re-detection preserves any record,
but relevant changed evidence must be reassessed. There is no automatic grandfathering.
Claude-only adopters must install Python 3.11+ before using the updated loop.

Use the skill's [record contract](../.claude/skills/loop-governance/references/contract.md)
for exact fields and commands. Changes in hosting or required checks require a
new assessment. Publication uses `--phase publish`, which requires successful
checks at local HEAD; start/resume checks the remote default branch's current SHA.
No paid account-backed Codex/Claude sessions run in CI; their live acceptance
results are recorded separately and must not be inferred from synthetic tests.
