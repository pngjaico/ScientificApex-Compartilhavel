# Install and operate on your computer

Open this clone in Antigravity and read GEMINI.md and AGENTS.md. On Windows,
install Git and uv, then run `powershell -NoProfile -ExecutionPolicy Bypass
-File .\instalar.ps1` from the cloned folder. The script installs Python 3.13
and locked core dependencies in this clone's .venv. Use -Development for the
development environment, or -VerifyOnly to check an existing installation offline.

Create your own project:

```powershell
.\.venv\Scripts\python.exe -m article_machine init "My study" --type systematic-review
.\.venv\Scripts\python.exe -m article_machine preflight projects/my-study
```

Read project.yaml, protocol.yaml, standards.yaml and compute.yaml. Other project
types include prediction-model and network-meta-analysis. Begin with planning.
The final PROSPERO/OSF protocol registration and documented review must precede
scientific execution. Local registry commands do not create a provider registration.
Never invent IDs, authorship, ethics approval or prospective-registration statements.

Select skills with `python -m article_machine skills route --query "your task"`
using the local interpreter. Build a Task Packet before substantive work.
Preserve source provenance, verified extraction, reproducible analysis, claim_map
and bibliography consistency, bilingual PT-BR/EN deliverables, Evidence Lock and
Review Trinity. Operational checks do not establish scientific validity.

R and renv, the separate ML/DL environments in modelos/, Quarto, Zotero, browser
tools, external catalogs and API credentials require project-specific installation
and verification. A skill is guidance, not an installed service. The core needs
no AI API key; Antigravity uses your own account and model configuration.
Dependencies may require internet downloads; no external scientific retrieval,
paid API calls or human-data uploads are part of the installer.

Generate a graph of your own clone with the included
`scripts/generate_workspace_graph.py`, then use the canonical
`python -m article_machine graph query "protocol evidence gates" --limit 5`.

No original research projects, patient datasets, manuscripts, account profile,
credentials or original Git history are included. modelos/ contains templates and
demonstrations, not approved studies. Your projects and credentials are ignored
by Git by default. Use truthful AI disclosure reflecting the tools actually used.
Third-party skill licenses and origins remain in skills/registry.json and notices.

Linux/macOS: `uv sync --locked --no-dev --python 3.13`, then
`.venv/bin/python -m article_machine --help`; adapt compute.yaml accordingly.
Only Windows core installation is tested for this delivery. R, ML, browsers,
remote providers, clinical validity and submission readiness are outside that test.
