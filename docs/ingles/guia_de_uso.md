# Usage guide

ScientificApex / Article Machine is an open-source scientific machine made up of a Python CLI, project contracts, evidence and review gates, documentation, and skills. Use it in a terminal, with any agent that can read repository files, or in a combined workflow. The core does not require a specific AI provider, model, account, or agent.

## Install the complete source clone

Install Git and [uv](https://docs.astral.sh/uv/), clone the repository, and enter the clone. The source clone is required for the complete machine: skills, templates, documentation, and operational files are not included in a Python wheel by itself.

### Windows (PowerShell)

```powershell
git clone https://github.com/pngjaico/ScientificApex-Compartilhavel.git
cd ScientificApex-Compartilhavel
powershell -NoProfile -ExecutionPolicy Bypass -File .\instalar.ps1
```

Pass `-Development` to install development dependencies. Pass `-VerifyOnly` to check an existing installation without syncing packages. The script creates and uses `.venv` inside this clone.

### Linux or macOS (Bash)

```sh
git clone https://github.com/pngjaico/ScientificApex-Compartilhavel.git
cd ScientificApex-Compartilhavel
bash instalar.sh
```

Pass `--development` to install development dependencies or `--verify-only` to check an existing installation. These instructions have not yet been tested on Linux or macOS; optional integrations may require platform-specific setup.

The installers sync locked dependencies from `uv.lock` and check the CLI and strict operational audit. Internet access is needed while packages are installed. They do not install R, ML/DL, browser tools, Zotero, Quarto, external providers, or an AI model, and they do not configure an agent account or credentials.

## Create and prepare a project

Use the interpreter from this clone:

```powershell
.\.venv\Scripts\python.exe -m article_machine --help
.\.venv\Scripts\python.exe -m article_machine init "My study" --type systematic-review
.\.venv\Scripts\python.exe -m article_machine preflight projects/my-study
```

On Linux/macOS, replace the interpreter path with `.venv/bin/python`. Other project types include `prediction-model` and `network-meta-analysis`. Read `project.yaml`, `protocol.yaml`, `standards.yaml`, and `compute.yaml`; fill them with verified information and prepare a Task Packet before scientific work. Use `skills route --query "..."` to find relevant guidance, without assuming that software described by a skill is installed.

Start with planning and protocol preparation. Before corpus building, screening, extraction, analysis, discovery, or scientific drafting, satisfy the applicable final PROSPERO/OSF protocol registration gate for the study design and current rules. Planning and protocol preparation before registration are allowed. Local commands may compile or review metadata and evidence, but they do not register a study with an external service. Never invent IDs, ethics approval, authorship, or prospective-registration statements.

After the gates are satisfied, preserve source provenance and extraction decisions, run reproducible analyses, synchronize `evidence/claim_map.jsonl` and `drafts/references.bib`, and use Evidence Lock and Review Trinity at the required workflow gates. New scientific deliverables should have Portuguese and English versions, preserving numbers, citations, uncertainty, and truthful disclosure of tools used. An operational PASS does not validate methodology, clinical safety, or publication readiness.

## Optional environments

Configure only what the project needs and record the actual setup in `compute.yaml`.

- **R:** install the project-required version and restore its `renv.lock`. R and its libraries are not installed by the main installer.
- **ML/DL:** separate environments under `modelos/aprendizado_de_maquina_clinico/` have their own `pyproject.toml` files and locks. Example: `uv sync --directory modelos/aprendizado_de_maquina_clinico`.
- **Browser:** follow the lockfiles and instructions for the local Playwright environment; authenticated profiles are not distributed.
- **Quarto, Zotero, catalogs, plugins, and APIs:** install or configure these separately when needed. Use your own credentials, keep them out of Git, and check service permissions and terms.

A skill is written guidance, not an active integration or proof that the described service is available.

## Data, privacy, and limits

Use synthetic data or data you are authorized to process. Do not commit personal data, patient-level data, private manuscripts, credentials, or account profiles. Do not send human data to external services without authorization and applicable safeguards. Keep new projects under `projects/<id>/`; review contents before creating a separate repository to share them. Templates and demonstrations are software examples, not approved studies or evidence.

The verification report documents the scope and limits of its checks. Windows installation was validated; Linux/macOS, R and ML/DL environments, external integrations, and clinical validity were not verified by that report. The original layer uses Apache-2.0; third-party terms are retained in LICENSE_SCOPE.md and the per-skill policy. Check Actions for the remote CI status of the commit in use.

## Operational graph

When available, generate or update the graph for this clone and use it for navigation:

```powershell
.\.venv\Scripts\python.exe scripts/generate_workspace_graph.py
.\.venv\Scripts\python.exe -m article_machine graph query "protocol evidence gates" --limit 5
```

On Unix, use `.venv/bin/python`. The graph helps locate components; it does not prove scientific claims.

See also [AGENTS.md](../../AGENTS.md), [contributing](../../CONTRIBUTING.md), [Portuguese guide](../portugues/guia_de_uso.md), [credits](creditos_opensource.md), [third-party notices](../../THIRD_PARTY_NOTICES.md), and the [verification report](relatorio_validacao.md).
