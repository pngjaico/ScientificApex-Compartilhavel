# Repository instructions for coding agents

These instructions apply to agents working in this repository. They describe the shared workflow; a user may also work directly through the CLI. No particular agent, model, AI provider, or account is required.

## Before work

1. Read the relevant usage guide and inspect the current Git status. Preserve existing user changes.
2. Use the repository root as the distribution root. Keep research projects and their artifacts under `projects/<project_id>/`; keep changes for the distribution itself in their appropriate source directories.
3. For a scientific task, inspect the active project's `project.yaml`, `protocol.yaml`, `standards.yaml`, and `compute.yaml`, then prepare a task packet and follow the project's permitted workflow mode. Do not infer a project or reuse another project's data or identity.
4. Use the operational graph for repository navigation when it is present and current. The graph aids navigation; it is not scientific evidence.

## Scientific integrity and gates

- Follow the protocol and registration requirements for the study design before corpus building, screening, extraction, analysis, discovery, or scientific drafting. Planning and protocol preparation may proceed earlier. A local registry command does not itself register a study with PROSPERO, OSF, or another provider.
- Preserve source provenance and link factual manuscript claims to reviewed evidence. Keep `evidence/claim_map.jsonl` and `drafts/references.bib` synchronized where those project artifacts apply. Use Evidence Lock and Review Trinity at the required workflow gates.
- Never invent results, citations, registration identifiers, ethics approvals, authorship, consent, or tool use. Keep unknown identity fields empty until the user supplies verified information.
- Report operational PASS, FAIL, and SKIPPED outcomes with their scope. They do not establish scientific validity or publication readiness.
- Treat outputs from hypothesis-generating workflows as hypotheses until independently validated.

## Data, external services, and optional tools

- Use only data the user is authorized to process. Do not commit credentials, personal data, patient-level data, private source documents, or account profiles.
- Do not upload human data, contact people, use paid services, publish, or change external systems without explicit user authorization and appropriate safeguards.
- Install only the optional runtime needed for the project. A skill is instructions, not proof that its software, database, plugin, or service is installed or accessible.
- The core CLI does not require a particular AI provider. Respect the active agent's available tools and configuration; do not claim settings or model capabilities that were not verified.

## Commands and changes

Use the clone's environment. On Windows:

```powershell
.\.venv\Scripts\python.exe -m article_machine --help
.\.venv\Scripts\python.exe -m article_machine machine audit --workspace-root . --strict
```

On Unix-like systems:

```sh
.venv/bin/python -m article_machine --help
.venv/bin/python -m article_machine machine audit --workspace-root . --strict
```

Use focused tests for code changes and report the exact command and result. Do not modify generated files, project data, or unrelated areas to make a check pass. Do not stage or commit changes unless the user explicitly asks.

For the complete installation, optional-stack, and contribution guidance, see the [Portuguese guide](docs/portugues/guia_de_uso.md), [English guide](docs/ingles/guia_de_uso.md), and [contribution guide](CONTRIBUTING.md).

---

## Referência Cloud & Google Drive (Atualizado 2026-11-08)

- **Guia Completo de Agentes na Nuvem:** Consulte [`.agents/CLOUD_GUIDE.md`](.agents/CLOUD_GUIDE.md).
- **Google Drive do Projeto (`Projetos/ScientificApex-Compartilhavel/`):** https://drive.google.com/drive/folders/1u0oiPf1uVC10uBP7sCIhi-66q3lIWK_S (`docs`, `dados`, `assets`, `backups`)
- **Google Drive Restrito (`Projetos/_Restrito/ScientificApex-Compartilhavel/`):** https://drive.google.com/drive/folders/1OpCGq67uYpJbxjiaILsZ9b27CVysWtQ7
- **Branches no Repositório:** `main`
