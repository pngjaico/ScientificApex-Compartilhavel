# Contributing

Thank you for considering a contribution to ScientificApex / Article Machine. Contributions should preserve scientific traceability, user privacy, and the distinct licenses and attribution of included work.

## Before making changes

1. Read [AGENTS.md](AGENTS.md) and the [Portuguese usage guide](docs/portugues/guia_de_uso.md). Check `git status` and preserve changes already in your checkout.
2. Install Git, Python 3.13, and [uv](https://docs.astral.sh/uv/). Clone the source repository; the Python wheel alone does not include the complete skills, templates, and documentation tree.
3. Create the development environment from the committed lockfile:

   ```sh
   uv sync --locked --python 3.13
   ```

   On Windows, run this from PowerShell or use `instalar.ps1 -Development`.

4. Keep scientific project data under `projects/<project_id>/` and do not include personal or human data in a contribution.

## Make and validate a focused change

- Keep changes scoped to the relevant source, docs, or tests. Avoid unrelated formatting or generated outputs.
- Add or update tests for behavior changes. Run focused tests during iteration, then run the relevant broader checks before proposing the change:

  ```sh
  uv run pytest tests/
  uv run ruff check article_machine tests
  uv run python -m article_machine machine audit --workspace-root . --strict
  ```

- On Windows, the same checks can use `.\.venv\Scripts\python.exe -m pytest tests/`, `.\.venv\Scripts\ruff.exe check article_machine tests`, and `.\.venv\Scripts\python.exe -m article_machine machine audit --workspace-root . --strict`.
- Report each command and its actual result, including failures and checks you skipped. Do not imply that local results mean a remote CI workflow passed.
- Do not weaken protocol, privacy, provenance, or Evidence Lock gates merely to make a test pass. Do not describe operational checks as scientific or clinical validation.

## Privacy, licensing, and permissions

- Never add credentials, tokens, personal information, patient-level data, private manuscripts, or account-specific configuration to a commit, fixture, screenshot, log, or example.
- Use synthetic fixtures. Before including third-party code, data, skills, documentation, or generated assets, record its source and license and preserve required notices. The current-source license policy is in LICENSE_SCOPE.md and third_party/politica_licencas.json. Add evidence for new components; do not apply the local Apache grant to third-party work.
- Do not access external accounts, upload data, contact people, publish, create a release, deploy, or incur charges as part of a contribution without explicit authorization from the repository owner and applicable data permissions.
- Do not stage or commit on behalf of a user unless they explicitly assign that action. Review the final diff and file list before proposing changes.

## Documentation and language

User-facing scientific workflow guidance should stay aligned in Portuguese and English. Preserve uncertainty, citations, numerical values, and truthful descriptions of tested platforms. Do not claim Linux/macOS validation until it has actually been run. See the [English contributor guide](docs/ingles/contribuir.md).
