Developer Setup
===============

Local Git hook to prevent pushes to main/master:

1. Point Git hooks to the repo's hooks directory:

   ```bash
   git config core.hooksPath .githooks
   ```

2. Verify the hook is executable:

   ```bash
   chmod +x .githooks/pre-push
   ```

Continuous Integration
----------------------

GitHub Actions workflow is configured in `.github/workflows/ci.yml` to:

- Block direct pushes to `main`/`master`.
- Run `python manage.py test -v 2` on PRs and pushes.

Debugging scripts
-----------------

Standalone helpers live in the repository root (e.g. `debug_*.py`, `scripts/`).
They do not load in production; they’re for local diagnosis only. Each script
bootstraps Django via `deadline_api.settings` and uses the local SQLite DB by
default.
