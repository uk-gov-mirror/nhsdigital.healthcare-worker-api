# ADR-004: Harden GitHub Actions usage

>|              | |
>| ------------ | --- |
>| Date         | `07/04/2026` |
>| Status       | `Accepted` |
>| Deciders     | `HCW Engineering` |
>| Significance | `Security` |
>| Owners       | `HCW admins` |

---

## Context

Recent supply-chain incidents affecting GitHub Actions have increased the risk of consuming mutable or insufficiently reviewed upstream action code.

The repository already removed the `aquasecurity/trivy-action` dependency after the upstream compromise. The next hardening step is to reduce trust in all external actions, pin any remaining use to immutable SHAs, and make workflow changes easier to review.

The NHS England guidance requires:

- full-length commit SHA pinning for every action reference, with an inline version comment
- minimising the use of third-party actions
- documenting any surviving external action usage and the alternatives considered
- using Dependabot for GitHub Actions with a delay period before version updates are proposed

## Decision

This repository will adopt the following controls:

1. All non-local GitHub Action references must be pinned to a full commit SHA and include an inline version comment.
2. Local shell or native GitHub CLI steps must be preferred over marketplace actions when the capability is straightforward to implement in-repo.
3. Workflow and composite action changes must be protected by CODEOWNERS review.
4. A repository check will fail if any external action reference is not pinned or lacks a version comment.
5. Dependabot will continue to manage GitHub Actions updates, but with a seven-day delay before routine version bumps are proposed.

## Reviewed external actions

### Retained

`actions/checkout`

- Required to retrieve repository contents for workflow execution.
- Native workflow syntax does not provide an equivalent checkout capability.

`actions/setup-python`

- Required to provision the Python runtime used by tests and static analysis.
- Replacing it with bespoke install logic would add more maintenance and more network-dependent shell code.

`actions/setup-node`

- Required for the static analysis composite action.
- Retained because the repo already depends on Node-based tooling in CI.

`actions/upload-artifact`

- Required to preserve generated reports from CI runs.
- Native shell alternatives would require custom API calls and token handling with no security benefit.

`aws-actions/configure-aws-credentials`

- Retained for OIDC-based AWS authentication.
- This avoids storing long-lived AWS credentials in GitHub and is preferable to custom STS exchange logic embedded in shell scripts.

### Removed in favour of native steps

`actions/create-release`

- Replaced with `gh release create` using the built-in `GITHUB_TOKEN`.

`nhs-england-tools/notify-msteams-action`

- Replaced with a direct webhook call from a shell step.

## Consequences

- Workflow changes are now easier to review because every external reference is immutable and annotated.
- Dependabot updates for GitHub Actions will be delayed by seven days, reducing exposure to newly published compromised releases.
- The repository still depends on a small set of external actions, but each one has a clear operational reason and a recorded review decision.