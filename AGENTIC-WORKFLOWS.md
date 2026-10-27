# GitHub Agentic Workflows

The `pr-triage` workflow in `.github/workflows/pr-triage.md` runs when a pull
request is opened, reopened, or marked ready for review. It can read pull
request metadata and request one label from the existing `bug`, `enhancement`,
`documentation`, or `question` labels. It cannot change files, create issues or
labels, comment, assign, approve, or merge. GitHub Agentic Workflows applies
the requested label in a separate safe-output job.

## Copilot authentication

This repository is owned by a personal GitHub account, so Copilot inference
uses a fine-grained personal access token. Create a token with the resource
owner set to the account that has an active Copilot license and only the
**Copilot Requests: read** account permission. Add it in the repository's
**Settings → Secrets and variables → Actions** as `COPILOT_GITHUB_TOKEN`.
Never put the token in source code or a workflow file.

To validate or update the generated GitHub Actions workflow, install the
`gh-aw` GitHub CLI extension and run `gh aw compile`. Commit both the Markdown
source and generated `.lock.yml`; do not edit the generated workflow directly.

## Human review

Review the workflow source and generated lock file before enabling triggers.
After each initial or changed workflow run, verify the selected pull request,
label, and rationale against its diff before relying on the classification.
The label is advisory metadata, not an approval or a substitute for human code
review. Pull requests still require the repository's normal human review and
merge process.
