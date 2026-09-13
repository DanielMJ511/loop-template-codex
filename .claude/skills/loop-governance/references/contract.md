# Governance contract (version 1)

Python 3.11+ is required for both Claude and Codex. The shared script is
`.claude/skills/loop-governance/scripts/governance.py` in the adopting project.
It uses Git and, for GitHub controls, authenticated `gh`. It executes no commands
stored inside assessment data. All check invocations are read-only.

```
python3 .claude/skills/loop-governance/scripts/governance.py init
python3 .claude/skills/loop-governance/scripts/governance.py seal
python3 .claude/skills/loop-governance/scripts/governance.py check --unit UNIT
python3 .claude/skills/loop-governance/scripts/governance.py check --phase publish --unit UNIT
```

Use `init --local` for a project without a remote, `--remote NAME` for a different
remote and `--review team` for team policy. Never reinitialize an existing record.
`--root PATH` selects the project; `--gh PATH` selects a known authenticated CLI.
`check` exits 0 only when ready and 1 otherwise, printing JSON `{ready, issues}`.
Unknown schema versions, malformed input, stale evidence and unavailable APIs block.

`loop/GOVERNANCE.json` contains version 1, detected identity, policy with `review`
(solo/team), `default_branch` and nonempty `required_checks`, and four `controls`:
`ci`, `protection`, `contributions`, `release`. Each control has `status`
(verified/gap/unverifiable/excepted), `evidence` (specific assessment explanation)
and `paths` (project-relative policy/evidence files). Contribution paths include
both contribution guidance and the PR template. Release paths point to the
project's suitable release/deployment policy. Existing equivalent docs are valid.
Write the human assessment and exact settings proposal in `loop/GOVERNANCE.md`.

`seal` records UTC `assessed_at`, configuration fingerprints and a policy digest;
it never sets readiness or creates approvals. Fingerprints cover the profile,
all workflow files and referenced policy files. Reassess after these change.
Remote identity must still match. GitHub checks re-fetch default-branch policy
and current default-branch CI; publication checks CI at local HEAD instead.
Required checks must be successful GitHub Actions checks, not skipped or neutral.
Other CI providers currently require a specific approved exception; record their
measured evidence in the summary instead of pretending the adapter verified them.

An excepted control includes `exception` with nonempty `reason`, `approved_by`,
`approval_reference` (the actual user approval), `scope` (`unit` or `configuration`),
and `kind` (e.g. offline, local-only or unsupported-provider). Unit scope also
contains the exact `unit` argument. Offline exceptions can only use unit scope.
Approval must be renewed when the bound configuration changes; record the
`configuration` hash returned by the script's `binding` action at approval time.
Do not generate an approval reference or renew that hash without user authorization.
An expired/mismatched exception leaves the control blocked.

The record is local workflow state, not a signature or security boundary. Preserve
it on re-detection. Do not publish local transcripts, tokens or confidential API
responses as evidence. Gate at start/resume and precommit; when governance-relevant
files change, re-run this separate workflow before continuing implementation.
