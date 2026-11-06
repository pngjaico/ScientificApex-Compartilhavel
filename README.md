# ScientificApex / Article Machine

ScientificApex distributes Article Machine, an open-source, agent-neutral scientific research environment. It combines a Python command-line application, project contracts, evidence and review gates, workflow guidance, and a curated skill collection. Use it from a terminal, with a coding agent that can read repository instructions, or with both. No particular AI provider, model, account, or agent is required by the core.

The repository is a source distribution. Clone it to get the complete machine, including its skills, templates, documentation, and operational files. Installing a Python wheel alone does not provide that full environment.

## What it provides

- Project scaffolding and workflow commands for protocol, corpus, analysis, drafting, review, and publication preparation.
- Project contracts that describe the question, protocol, standards, and computational environment.
- Provenance and evidence controls, including claim tracking, Evidence Lock, and Review Trinity gates.
- Optional scientific skills and integrations. A skill is guidance; it does not install or validate the external software or service it describes.
- Optional R, clinical ML/DL, browser, Quarto, Zotero, and external data-provider workflows, configured and validated for each project as needed.

These controls improve traceability. Passing an operational check does not establish methodological validity, clinical safety, reproducibility on another computer, or publication readiness.

## Quick start

Install Git and [uv](https://docs.astral.sh/uv/), clone the repository, and enter the clone. The development team documents Windows and Unix-like setup paths below. The core passed 84 tests and installer verification on Windows and Ubuntu/Linux in [GitHub Actions](https://github.com/pngjaico/ScientificApex-Compartilhavel/actions/runs/42286830255). macOS has not been tested.

### Windows (PowerShell)

```powershell
git clone https://github.com/pngjaico/ScientificApex-Compartilhavel.git
cd ScientificApex-Compartilhavel
powershell -NoProfile -ExecutionPolicy Bypass -File .\instalar.ps1
```

For development dependencies, pass `-Development`. To check an existing local installation without syncing packages, pass `-VerifyOnly`.

### Linux or macOS (Bash)

```sh
git clone https://github.com/pngjaico/ScientificApex-Compartilhavel.git
cd ScientificApex-Compartilhavel
bash instalar.sh
```

For development dependencies, pass `--development`. To check an existing local installation without syncing packages, pass `--verify-only`. The Unix verification path passed on Ubuntu/Linux CI; macOS remains untested. Optional integrations require separate platform-specific checks.

### Create a project

Use the interpreter in this clone so the command uses its locked environment:

```powershell
.\.venv\Scripts\python.exe -m article_machine init "My study" --type systematic-review
.\.venv\Scripts\python.exe -m article_machine --help
```

On Linux/macOS, use `.venv/bin/python` in place of the Windows interpreter path. Review the generated `project.yaml`, `protocol.yaml`, `standards.yaml`, and `compute.yaml` before work proceeds. Start with planning, and follow the project's protocol and registration requirements before scientific execution. Local registration commands prepare or verify artifacts; they do not register a study with an external registry.

## Scientific gates and responsible use

Record sources and extraction decisions, preserve the link between claims and evidence, and keep references synchronized with the project. Evidence Lock and Review Trinity are required gates for applicable drafting and submission workflows. Do not invent registration IDs, ethics approvals, authorship, results, or prospective-registration statements. An audit can report pass, fail, or skipped checks; report its scope and limitations.

Use synthetic or authorized data. Do not place credentials or personal data in Git, and do not send human data to external services without authorization and applicable safeguards. Configure optional tools and providers explicitly for the project. The installer does not require an AI API key or configure an agent account.

## Documentation and contribution

- [Guia de uso em português](docs/portugues/guia_de_uso.md)
- [English usage guide](docs/ingles/guia_de_uso.md)
- [Contribuir](CONTRIBUTING.md) · [Contributing in English](docs/ingles/contribuir.md)
- [Agent-neutral repository instructions](AGENTS.md)
- [Gemini/Antigravity adapter](GEMINI.md) (optional)
- [Open-source credits in Portuguese](docs/portugues/creditos_opensource.md) · [English credits](docs/ingles/creditos_opensource.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md) · [NOTICE](NOTICE)
- [Distribution verification report](docs/portugues/relatorio_validacao.md)

The original machine layer is open source under **Apache-2.0**. Included third-party components retain their own terms, including MIT, BSD-3-Clause, Apache-2.0 and CC-BY-4.0 for documentation. See [license scope](LICENSE_SCOPE.md), [the per-skill policy](third_party/politica_licencas.json) and [third-party notices](THIRD_PARTY_NOTICES.md). The policy covers the current source distribution, not external research data or blanket relicensing of older history.

Pull requests and issues are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) and [CITATION.cff](CITATION.cff). Automated checks cover the core tests, operational gates and documentary license scope; they do not certify scientific validity or legal authenticity.
