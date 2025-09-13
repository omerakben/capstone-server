Developer Setup
===============

Local Git hook to prevent pushes to main/master:

1. Point Git hooks to the repo's hooks directory:

   git config core.hooksPath .githooks

2. Verify the hook is executable:

   chmod +x .githooks/pre-push

Continuous Integration
----------------------

GitHub Actions workflow is configured in `.github/workflows/ci.yml` to:

- Block direct pushes to `main`/`master` (CI fails the push).
- Run Django test suite on PRs and pushes.

