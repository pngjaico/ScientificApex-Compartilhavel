# Contributing

Thank you for considering a contribution to ScientificApex / Article Machine. Contributions should preserve scientific traceability, user privacy, and the separate licenses and attribution of included work.

## Before changing files

1. Read [AGENTS.md](../../AGENTS.md) and the [English usage guide](guia_de_uso.md). Check `git status` and preserve changes already in your checkout.
2. Install Git, Python 3.13, and [uv](https://docs.astral.sh/uv/). Clone the source repository; a Python wheel alone does not contain the full skills, templates, and documentation tree.
3. Create the development environment from the committed lockfile:

   ```sh
   uv sync --locked --python 3.13
   ```

   On Windows, run this from PowerShell or use `instalar.ps1 -Development`.

4. Keep scientific project data under `projects/<project_id>/`; do not include personal or human data in a contribution.

## Make and validate a focused change

- Limit changes to relevant source, docs, or tests. Avoid unrelated formatting and generated outputs.
- Add or update tests for behavior changes. Run focused tests while iterating, then run relevant broader checks before proposing the change:

  ```sh
  uv run pytest tests/
  uv run ruff check article_machine tests
  uv run python -m article_machine machine audit --workspace-root . --strict
  ```

- On Windows, use `.\.venv\Scripts\python.exe -m pytest tests/`, `.\.venv\Scripts\ruff.exe check article_machine tests`, and `.\.venv\Scripts\python.exe -m article_machine machine audit --workspace-root . --strict`.
- Report each command and its actual result, including failures and skipped checks. Local results do not show that a remote CI workflow passed.
- Do not weaken protocol, privacy, provenance, or Evidence Lock gates to make a test pass. Operational checks are not scientific or clinical validation.

## Privacy, licensing, and authorization

- Never add credentials, tokens, personal information, patient-level data, private manuscripts, or account-specific configuration to a commit, fixture, screenshot, log, or example.
- Use synthetic fixtures. Before including third-party code, data, skills, documentation, or generated assets, record their source and license and preserve required notices. Follow LICENSE_SCOPE.md and third_party/politica_licencas.json. New third-party components require source and permission evidence.
- Do not access external accounts, upload data, contact people, publish, create a release, deploy, or incur charges as part of a contribution without explicit authorization from the repository owner and applicable data permissions.
- Do not stage or commit for a user unless that action is explicitly assigned. Review the final diff and file list before proposing changes.

## Documentation and language

User-facing scientific workflow guidance should remain aligned in Portuguese and English. Preserve uncertainty, citations, numbers, and truthful descriptions of tested platforms. Do not claim Linux/macOS validation until it has actually been run. See the [Portuguese contributor guide](../../CONTRIBUTING.md).
