---
name: loop-governance
description: Complete the required development-governance assessment before loop implementation or publishing; prepare and verify CI, review, contribution and release safeguards, including explicitly approved exceptions.
---

Run in the main session. This is the required workflow after loop-init, also used
when evidence becomes stale or an existing installation has no governance record.
Planning remains available while governance is pending. Do not invoke orchestration
recursively to configure its own prerequisites.

1. Read loop/PROFILE.md, the existing governance record and the project's actual
   CI, contribution, Git and release policies. Verify Python 3.11+ and authenticated
   `gh` for GitHub projects. Follow [the contract](references/contract.md) for the
   record and executable commands. Never infer readiness from a passed-looking flag.
2. Assess CI, default-branch protection, contribution/review guidance and a suitable
   release or deployment policy. Inspect actual GitHub settings, inherited rules,
   latest checks and available maintainers; preserve stronger existing policies.
   Propose solo PR+CI policy or one independent team approval as appropriate.
3. Prepare a concrete remediation diff and settings proposal. CI must use the
   project's measured test commands and prerequisites, reject empty or skipped
   required suites, use least-privilege permissions and immutable action pins.
   Contribution guidance must cover setup, validation, review and merges; release
   guidance must cover versioning/deployment, compatibility and rollback. Do not
   invent a universal application stack or require every project to publish a tag.
4. Obtain authorization only for consequential changes not already authorized.
   Apply authorized governance-only changes on a feature branch or worktree. This
   bootstrap allowance covers CI, policy docs, settings and tests of this setup;
   it never permits normal feature implementation behind a failing gate. Respect
   existing branch protections, and do not disable them to get the bootstrap merged.
   For a new CI setup, establish successful PR checks before requiring those names.
5. When a control cannot be satisfied, record the concrete gap. An exception
   requires explicit user approval, reason, scope and approval reference. Do not
   treat silence, API failure, unavailable reviewers or a local-only project as
   approval. Offline approval is bounded to the named current unit. Non-GitHub
   hosting uses approved exceptions for the unsupported GitHub-specific controls.
6. Write the assessment summary and record; seal its evidence and run the validator.
   Verify effective settings rather than just files or command success. Recheck
   before publication with --phase publish, requiring successful checks at HEAD.
   A pending bootstrap PR may be published solely to establish CI; merging it must
   satisfy configured GitHub protections. Record readiness only after verification.
7. Return ready or a finite list of blockers. Failed checks must end normally;
   never use a Stop-hook continuation, automatic retry loop or blanket exception.
   Do not alter unrelated applications, earned lessons, existing tasks or journals.

A skill instruction and local record are not tamper-proof. The executable gate is
mandatory in the loop workflow; server-side protections enforce the GitHub boundary.
