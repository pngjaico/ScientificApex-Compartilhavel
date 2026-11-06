"""Workspace Hygiene Governor, Anti-Pollution Shield & Real-Flow Skill Enforcer.

Ensures that regardless of which agent (Sol, Luna, Codex, Claude, Gemini/Antigravity) runs:
1. Every lifecycle mode (`bootstrap` through `submission`) and `project_type` automatically binds
   its mandatory skills (`SKILL.md` paths), canonical CLI commands, and allowed write directories.
2. The workspace root and `projects/` root cannot be polluted with loose files, secrets, or caches.
3. Every `projects/<project_id>/` folder enforces canonical top-level files and directories, with
   manifest-backed non-destructive organization (`organize_project_strays`) for legacy loose files.
4. A Git pre-commit guard blocks staging of secrets (`.env`, API keys), transient caches, or loose
   files outside canonical project paths.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..serialization import load_structured_file, save_structured_file

ALLOWED_ROOT_FILES: frozenset[str] = frozenset(
    {
        ".AGENTES",
        ".env",
        ".gitattributes",
        ".gitignore",
        ".pre-commit-config.yaml",
        "AGENT_MANIFEST.md",
        "AGENTS.md",
        "CANONICAL_PROTOCOL_RSMA.md",
        "CHANGELOG.md",
        "LAB_TEMPLATES.md",
        "LEIA-ME_PRIMEIRO.md",
        "MANIFESTO_ATUALIZACAO_2026_11_02.json",
        "MANIFESTO_DA_ENTREGA.json",
        "README.md",
        "SKILLS_CANON.md",
        "SKILL_INDEX.md",
        "abrir_codex.cmd",
        "abrir_opencode.cmd",
        "iniciar_maquina.ps1",
        "maquina_canonica.json",
        "opencode.json",
        "package.json",
        "pyproject.toml",
        "uv.lock",
    }
)

ALLOWED_ROOT_DIRS: frozenset[str] = frozenset(
    {
        ".agents",
        ".codex",
        ".opencode",
        ".git",
        ".github",
        ".machine",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "acervo_de_referencia",
        "archive",
        "article_machine",
        "docs",
        "ferramentas",
        "graphify-out",
        "integracoes",
        "modelos",
        "projects",
        "scripts",
        "scratch",
        "skills",
        "sources",
        "tests",
        "tools",
    }
)

CANONICAL_PROJECT_FILES: frozenset[str] = frozenset(
    {
        "project.yaml",
        "protocol.yaml",
        "standards.yaml",
        "compute.yaml",
        "README.md",
        "LEIA-ME.md",
        "EXECUTIVE_SUMMARY.md",
        "HISTORICAL_STATUS.yaml",
        "renv.lock",
        "uv.lock",
        ".Rprofile",
        ".gitignore",
    }
)

CANONICAL_PROJECT_DIRS: frozenset[str] = frozenset(
    {
        "sources",
        "context",
        "screening",
        "extraction",
        "evidence",
        "analysis",
        "figures",
        "drafts",
        "deliverables",
        "publicacoes",
        "reviews",
        "exports",
        ".machine",
        "renv",
        "scripts",
        "data",
        "experiments",
        "inventory",
        "intercambio_kdense",
    }
)

# Universal base skills per mode + design-specific skill overlays
MODE_BASE_SKILLS: dict[str, list[str]] = {
    "bootstrap": [
        "workspace-graph-navigator",
        "project-entry-navigator",
        "scientific-workflow-orchestrator",
        "hypothesis-tournament",
        "scientific-novelty-checker",
        "guideline-router",
        "deep-thinking-governor",
    ],
    "protocol-freeze": [
        "protocol-registration-governor",
        "experimental-design-planner",
        "guideline-router",
        "scientific-critical-thinking",
        "deep-thinking-governor",
    ],
    "corpus-build": [
        "query-string-governor",
        "database-retrieval-governor",
        "pubmed-database",
        "literature-search-europepmc",
        "literature-search-openalex",
        "crossref-unpaywall-resolver",
        "zotero-reference-manager",
        "retraction-integrity-checker",
        "content-preservation-guardian",
    ],
    "screening": [
        "asreview-screening-bridge",
        "literature-review",
        "retraction-integrity-checker",
        "stage-audit-governor",
    ],
    "extraction": [
        "extraction-schema-governor",
        "risk-of-bias-assistant",
        "evidence-lock-hardener",
        "citation-management",
    ],
    "analysis": [
        "statistical-analysis",
        "scientific-visualization",
        "grade-sof-table-builder",
        "stage-audit-governor",
    ],
    "discovery": [
        "in-silico-validation-governor",
        "life-science-router",
        "open-targets-drug-targeting",
        "chembl-bindingdb-miner",
        "alphafold-pdb-structure-router",
        "tooluniverse-drug-target-validation",
        "tooluniverse-drug-repurposing",
    ],
    "drafting": [
        "bilingual-scientific-writing",
        "ptbr-article-writing",
        "anti-ai-writing-governor",
        "scientific-writing",
        "clinical-reports",
        "evidence-lock-hardener",
        "zotero-reference-manager",
        "publicacao-medica-organizada",
        "venue-templates",
    ],
    "review-trinity": [
        "scientific-red-team-reviewer",
        "peer-review",
        "manuscript-integrity-response-governor",
        "retraction-integrity-checker",
        "opencitations-citation-audit",
        "stage-audit-governor",
    ],
    "submission": [
        "publicacao-medica-organizada",
        "venue-templates",
        "academic-office-deliverables",
        "conference-deliverable-router",
        "conference-slides-html",
        "conference-posters-html",
        "playwright-layout-qa",
        "pptx-export-bridge",
        "ro-crate-provenance-export",
        "agent-benchmark-harness",
        "author-identity-resolver",
    ],
}

PROJECT_TYPE_SKILL_OVERLAYS: dict[str, list[str]] = {
    "systematic-review": [
        "meta-analise-medica",
        "tooluniverse-meta-analysis",
        "risk-of-bias-assistant",
        "grade-sof-table-builder",
    ],
    "network-meta-analysis": [
        "meta-analise-medica",
        "tooluniverse-meta-analysis",
        "risk-of-bias-assistant",
        "grade-sof-table-builder",
    ],
    "prediction-model": [
        "metodos-ml-clinico",
        "scikit-learn",
        "pytorch-lightning",
        "tooluniverse-dataset-discovery",
    ],
    "diagnostic-study": [
        "tooluniverse-diagnostic-test-evaluation",
        "risk-of-bias-assistant",
    ],
    "observational-study": [
        "tooluniverse-epidemiological-analysis",
        "datasus-research-engine",
    ],
    "clinical-trial": [
        "tooluniverse-clinical-trial-design",
        "clinical-trials-database",
    ],
    "drug-discovery": [
        "in-silico-validation-governor",
        "open-targets-drug-targeting",
        "chembl-bindingdb-miner",
    ],
    "intestinal-digital-twin": [
        "intestinal-transplant-research",
        "in-silico-validation-governor",
    ],
}

MODE_CANONICAL_COMMANDS: dict[str, list[str]] = {
    "bootstrap": [
        "python -m article_machine methodology validate-protocol <project_dir>",
        'python -m article_machine workflow plan <project_dir> --query "..." --language pt-BR',
        "python -m article_machine study build <project_dir>",
    ],
    "protocol-freeze": [
        "python -m article_machine methodology validate-protocol <project_dir>",
        "python -m article_machine methodology compile-registration-packet <project_dir>",
        "python -m article_machine prospero compile <project_dir>",
        "python -m article_machine prospero browser-assist <project_dir>",
        "python -m article_machine registry check-osf",
        'python -m article_machine registry fetch-osf <project_dir> --id <OSF_ID> --reviewer "<Nome>"',
        "python -m article_machine registry verify <project_dir> --record <json_path>",
    ],
    "corpus-build": [
        "python -m article_machine corpus prepare <project_dir>",
        "python -m article_machine corpus fetch-pubmed <project_dir> --max-records 500",
        "python -m article_machine corpus fetch-scopus <project_dir> --max-records 500",
        "python -m article_machine corpus deduplicate <project_dir>",
        "python -m article_machine datasets stage <project_dir>",
        "python -m article_machine datasets verify <project_dir> --id <dataset_id>",
    ],
    "screening": [
        "python -m article_machine guard check <project_dir> --mode screening",
        "python -m article_machine study build <project_dir>",
    ],
    "extraction": [
        "python -m article_machine methodology validate-extraction <extraction_file> --mode pairwise|nma|diagnostic",
        "python -m article_machine study build <project_dir>",
    ],
    "analysis": [
        "python -m article_machine preflight <project_dir>",
        "python -m article_machine run-r <project_dir> <script.R>",
        "python -m article_machine run-python <project_dir> <script.py>",
        "python -m article_machine synthesis harvest <project_dir>",
        "python -m article_machine study build <project_dir>",
    ],
    "discovery": [
        'python -m article_machine life-science plan <project_dir> --question "..."',
        "python -m article_machine run-python <project_dir> <script.py>",
        "python -m article_machine study build <project_dir>",
    ],
    "drafting": [
        "python -m article_machine synthesis build <project_dir>",
        "python -m article_machine methodology audit-numbers <project_dir>",
        "python -m article_machine methodology audit-equator <project_dir>",
        "python -m article_machine workflow audit-language <project_dir> --language pt-BR "
        "--draft drafts/portugues/manuscrito_completo.md --reference drafts/ingles/manuscrito_completo.md",
        "python -m article_machine draft <project_dir>",
    ],
    "review-trinity": [
        "python -m article_machine review <project_dir>",
        "python -m article_machine methodology audit-equator <project_dir>",
        "python -m article_machine methodology audit-numbers <project_dir>",
    ],
    "submission": [
        "python -m article_machine journals route <project_dir>",
        "python -m article_machine synthesis build <project_dir>",
        "python -m article_machine export <project_dir>",
        "python -m article_machine hygiene check",
    ],
}

MODE_ALLOWED_WRITE_PATHS: dict[str, list[str]] = {
    "bootstrap": ["project.yaml", "protocol.yaml", "standards.yaml", "compute.yaml", "context/"],
    "protocol-freeze": [
        "protocol.yaml",
        "standards.yaml",
        "context/protocolo_registravel/",
        "evidence/protocol_registration/",
    ],
    "corpus-build": [
        "context/query_plan.yaml",
        "context/retrieval/",
        "sources/",
        "evidence/retrieval/",
        "evidence/prisma/",
        "screening/",
    ],
    "screening": ["screening/", "evidence/screening/", "context/"],
    "extraction": ["extraction/", "evidence/", "analysis/"],
    "analysis": ["analysis/", "figures/", "evidence/", "context/estudo_do_projeto/"],
    "discovery": ["analysis/", "figures/", "evidence/life_science/", "context/life_science/"],
    "drafting": ["drafts/", "deliverables/", "publicacoes/", "context/estudo_do_projeto/"],
    "review-trinity": ["reviews/", "drafts/", "evidence/"],
    "submission": ["exports/", "deliverables/", "publicacoes/"],
}

SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?:OSF_TOKEN|SCOPUS_API_KEY|NCBI_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY)\s*=\s*[A-Za-z0-9_\-]{16,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def _workspace_root_from_project(project_dir: Path) -> Path:
    resolved = Path(project_dir).resolve()
    if resolved.parent.name == "projects":
        return resolved.parent.parent
    return Path(__file__).resolve().parents[2]


def resolve_real_flow_bindings(project_dir: Path, mode: str | None = None) -> dict[str, Any]:
    """Resolve mandatory skills (with SKILL.md paths), CLI commands, and write paths for a project and mode."""
    root = Path(project_dir).resolve()
    ws_root = _workspace_root_from_project(root)
    project = load_structured_file(root / "project.yaml")
    protocol = load_structured_file(root / "protocol.yaml")
    project_type = (
        str(project.get("project_type") or protocol.get("project_type") or "systematic-review").strip().lower()
    )
    active_mode = (mode or project.get("state", {}).get("current_mode") or "bootstrap").strip().lower()

    skill_names: list[str] = []
    for s in MODE_BASE_SKILLS.get(active_mode, MODE_BASE_SKILLS["bootstrap"]):
        if s not in skill_names:
            skill_names.append(s)
    for s in PROJECT_TYPE_SKILL_OVERLAYS.get(project_type, []):
        if s not in skill_names:
            skill_names.append(s)

    resolved_skills: list[dict[str, str]] = []
    for sname in skill_names:
        agent_skill_md = ws_root / ".agents" / "skills" / sname / "SKILL.md"
        canon_skill_md = ws_root / "skills" / sname / "SKILL.md"
        chosen = agent_skill_md if agent_skill_md.is_file() else canon_skill_md
        resolved_skills.append(
            {
                "skill": sname,
                "skill_file": chosen.relative_to(ws_root).as_posix()
                if chosen.is_file()
                else f"skills/{sname}/SKILL.md",
                "exists": "true" if chosen.is_file() else "false",
            }
        )

    rel_proj = root.relative_to(ws_root).as_posix() if root.is_relative_to(ws_root) else root.as_posix()
    commands = [
        cmd.replace("<project_dir>", rel_proj)
        for cmd in MODE_CANONICAL_COMMANDS.get(active_mode, MODE_CANONICAL_COMMANDS["bootstrap"])
    ]
    allowed_paths = MODE_ALLOWED_WRITE_PATHS.get(active_mode, ["context/", "analysis/"])

    return {
        "contract": "RealFlowSkillBindingsV1",
        "project_id": project.get("id") or root.name,
        "project_type": project_type,
        "mode": active_mode,
        "mandatory_skills": resolved_skills,
        "canonical_commands": commands,
        "allowed_write_paths": [f"{rel_proj}/{p}" for p in allowed_paths],
        "anti_pollution_rules": [
            "NEVER create loose files in the workspace root or directly in projects/<project_id>/ root.",
            "Every output file MUST reside inside one of the canonical subdirectories (sources/, context/, "
            "screening/, extraction/, evidence/, analysis/, figures/, drafts/, "
            "deliverables/, publicacoes/, reviews/, exports/).",
            "Every scientific/editorial deliverable MUST have paired PT-BR (portugues/) and EN (ingles/) files.",
            "Never stage .env, API tokens, .RData/.Rhistory, or raw patient data dumps.",
        ],
    }


def write_active_mode_guide(project_dir: Path, mode: str | None = None) -> dict[str, Any]:
    """Write context/task_packets/ACTIVE_MODE_GUIDE.md inside the project for any agent entering the project."""
    root = Path(project_dir).resolve()
    bindings = resolve_real_flow_bindings(root, mode)
    guide_dir = root / "context" / "task_packets"
    guide_dir.mkdir(parents=True, exist_ok=True)
    guide_path = guide_dir / "ACTIVE_MODE_GUIDE.md"

    skills_md = "\n".join(f"- **`{s['skill']}`** → `{s['skill_file']}`" for s in bindings["mandatory_skills"])
    cmds_md = "\n".join(f"- `{c}`" for c in bindings["canonical_commands"])
    paths_md = "\n".join(f"- `{p}`" for p in bindings["allowed_write_paths"])
    rules_md = "\n".join(f"- {r}" for r in bindings["anti_pollution_rules"])

    content = (
        f"# Guia Obrigatório de Execução do Modo Ativo / Active Mode Execution Guide\n\n"
        f"- **Projeto / Project:** `{bindings['project_id']}` (`{bindings['project_type']}`)\n"
        f"- **Modo Ativo / Active Mode:** `{bindings['mode']}`\n\n"
        f"## 1. Skills Obrigatórias neste Modo (Leia antes de executar)\n{skills_md}\n\n"
        f"## 2. Comandos Canônicos da Máquina para este Modo\n{cmds_md}\n\n"
        f"## 3. Caminhos de Escrita Permitidos neste Modo\n{paths_md}\n\n"
        f"## 4. Regras Invioláveis Anti-Poluição (Qualquer Agente)\n{rules_md}\n"
    )
    guide_path.write_text(content, encoding="utf-8")
    bindings["guide_path"] = guide_path.relative_to(root).as_posix()
    return bindings


def audit_project_hygiene(project_dir: Path) -> dict[str, Any]:
    """Check a single projects/<project_id>/ directory for non-canonical top-level files or directories."""
    root = Path(project_dir).resolve()
    stray_files: list[str] = []
    stray_dirs: list[str] = []

    if root.is_dir():
        for entry in sorted(root.iterdir()):
            if entry.is_file():
                if entry.name not in CANONICAL_PROJECT_FILES:
                    stray_files.append(entry.name)
            elif entry.is_dir():
                if entry.name not in CANONICAL_PROJECT_DIRS:
                    stray_dirs.append(entry.name)

    return {
        "project_id": root.name,
        "clean": len(stray_files) == 0 and len(stray_dirs) == 0,
        "stray_files": stray_files,
        "stray_dirs": stray_dirs,
    }


def audit_workspace_hygiene(workspace_root: Path = Path("."), *, check_staged: bool = False) -> dict[str, Any]:
    """Audit workspace root, projects/, and optionally git staged files against anti-pollution rules."""
    ws = Path(workspace_root).resolve()
    root_stray_files: list[str] = []
    root_stray_dirs: list[str] = []
    projects_root_strays: list[str] = []
    project_reports: dict[str, Any] = {}
    staged_issues: list[str] = []

    for entry in sorted(ws.iterdir()):
        if entry.is_file():
            if entry.name not in ALLOWED_ROOT_FILES:
                root_stray_files.append(entry.name)
        elif entry.is_dir():
            if entry.name not in ALLOWED_ROOT_DIRS:
                root_stray_dirs.append(entry.name)

    projects_dir = ws / "projects"
    if projects_dir.is_dir():
        for entry in sorted(projects_dir.iterdir()):
            if entry.is_file():
                projects_root_strays.append(entry.name)
            elif entry.is_dir():
                project_reports[entry.name] = audit_project_hygiene(entry)

    if check_staged:
        try:
            proc = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=ws,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            staged_files = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        except OSError:
            staged_files = []

        for rel_str in staged_files:
            rel_path = Path(rel_str)
            if rel_path.name == ".env" or rel_path.name.startswith(".env."):
                staged_issues.append(f"CRITICAL: Secret file '{rel_str}' is staged in Git!")
            if rel_path.suffix.lower() in {".rdata", ".rhistory", ".rds", ".tmp", ".bak"}:
                staged_issues.append(f"Transient/binary file '{rel_str}' must not be staged in Git.")
            if len(rel_path.parts) == 1 and rel_path.name not in ALLOWED_ROOT_FILES:
                staged_issues.append(f"Unapproved workspace root file '{rel_str}' cannot be committed.")
            if (
                len(rel_path.parts) == 3
                and rel_path.parts[0] == "projects"
                and rel_path.parts[2] not in CANONICAL_PROJECT_FILES
                and (ws / rel_path).is_file()
            ):
                staged_issues.append(
                    f"Loose file '{rel_str}' in project root! Place inside a canonical folder "
                    "(analysis/, figures/, context/, sources/, drafts/, evidence/)."
                )
            full_p = ws / rel_path
            if full_p.is_file() and full_p.stat().st_size < 2_000_000:
                txt = full_p.read_text(encoding="utf-8", errors="ignore")
                for pat in SECRET_PATTERNS:
                    if pat.search(txt):
                        staged_issues.append(
                            f"CRITICAL: Potential API key or secret detected inside staged file '{rel_str}'!"
                        )
                        break

    blocking_issues: list[str] = []
    if root_stray_files:
        blocking_issues.append(f"Stray files in workspace root: {root_stray_files}")
    if root_stray_dirs:
        blocking_issues.append(f"Stray directories in workspace root: {root_stray_dirs}")
    if projects_root_strays:
        blocking_issues.append(f"Loose files directly inside projects/: {projects_root_strays}")
    if staged_issues:
        blocking_issues.extend(staged_issues)

    dirty_projects = [pid for pid, rep in project_reports.items() if not rep["clean"]]
    if dirty_projects:
        blocking_issues.append(
            f"Projects with non-canonical loose root files/folders: {dirty_projects}. "
            "Run 'python -m article_machine hygiene organize projects/<id> --apply'."
        )

    return {
        "contract": "WorkspaceHygieneAuditV1",
        "status": "pass" if not blocking_issues else "blocked",
        "workspace_root_clean": not root_stray_files and not root_stray_dirs,
        "root_stray_files": root_stray_files,
        "root_stray_dirs": root_stray_dirs,
        "projects_root_strays": projects_root_strays,
        "dirty_project_roots": dirty_projects,
        "project_reports": project_reports,
        "staged_issues": staged_issues,
        "issues": blocking_issues,
    }


def _target_subfolder_for_stray(file_name: str) -> str:
    lower = file_name.lower()
    suf = Path(file_name).suffix.lower()
    if suf in {".png", ".svg", ".jpg", ".jpeg", ".webp", ".tiff"}:
        return "figures/legacy_root_organized"
    if "embase" in lower or "pubmed" in lower or "scopus" in lower or suf in {".ris", ".nbib", ".bib"}:
        return "sources/legacy_root_organized"
    if suf in {".r", ".py", ".ps1", ".sh", ".csv", ".tsv", ".json", ".txt"}:
        return "analysis/legacy_root_organized"
    if suf in {".md", ".docx", ".pdf", ".html"}:
        return "context/legacy_root_organized"
    return ".machine/quarantine"


def organize_project_strays(project_dir: Path, *, apply: bool = False) -> dict[str, Any]:
    """Safely catalog (and if apply=True, move with SHA-256 manifest) stray top-level files into canonical folders."""
    root = Path(project_dir).resolve()
    hygiene = audit_project_hygiene(root)
    planned_moves: list[dict[str, Any]] = []

    for fname in hygiene["stray_files"]:
        src = root / fname
        if not src.is_file():
            continue
        dest_rel_dir = _target_subfolder_for_stray(fname)
        dest = root / dest_rel_dir / fname
        sha = hashlib.sha256(src.read_bytes()).hexdigest()
        planned_moves.append(
            {
                "file": fname,
                "source_rel": fname,
                "destination_rel": f"{dest_rel_dir}/{fname}",
                "sha256": sha,
                "bytes": src.stat().st_size,
            }
        )
        if apply:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))

    for dname in hygiene["stray_dirs"]:
        src_dir = root / dname
        if not src_dir.is_dir():
            continue
        dest_dir = root / "context" / "legacy_root_organized" / dname
        planned_moves.append(
            {
                "directory": dname,
                "source_rel": dname,
                "destination_rel": f"context/legacy_root_organized/{dname}",
            }
        )
        if apply and not dest_dir.exists():
            dest_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_dir), str(dest_dir))

    manifest_dir = root / ".machine" / "hygiene_manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    manifest_path = manifest_dir / f"hygiene_migration_{ts}.json"
    report = {
        "contract": "ProjectHygieneOrganizationManifestV1",
        "status": "pass",
        "project_id": root.name,
        "applied": apply,
        "generated_at": datetime.now(UTC).isoformat(),
        "moves_count": len(planned_moves),
        "moves": planned_moves,
        "manifest_path": manifest_path.relative_to(root).as_posix(),
    }
    save_structured_file(manifest_path, report)
    return report


def install_git_hygiene_hook(workspace_root: Path = Path(".")) -> dict[str, Any]:
    """Install a local .git/hooks/pre-commit guard that enforces workspace hygiene & secret blocking."""
    ws = Path(workspace_root).resolve()
    git_hooks_dir = ws / ".git" / "hooks"
    if not git_hooks_dir.is_dir():
        return {"status": "blocked", "issues": ["No .git/hooks directory found."]}

    hook_path = git_hooks_dir / "pre-commit"
    hook_script = (
        "#!/bin/sh\n"
        "# Article Machine Automatic Anti-Pollution & Secret Pre-Commit Guard\n"
        'if [ -x ".venv/Scripts/python.exe" ]; then\n'
        "  .venv/Scripts/python.exe -m article_machine hygiene check --staged\n"
        'elif [ -x ".venv/bin/python" ]; then\n'
        "  .venv/bin/python -m article_machine hygiene check --staged\n"
        "else\n"
        "  python -m article_machine hygiene check --staged\n"
        "fi\n"
    )
    hook_path.write_text(hook_script, encoding="utf-8", newline="\n")
    return {
        "contract": "GitHygieneHookInstallV1",
        "status": "pass",
        "hook_path": hook_path.relative_to(ws).as_posix(),
    }
