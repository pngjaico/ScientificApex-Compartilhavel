from __future__ import annotations

import ast
from functools import lru_cache
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CRITICAL_SKILLS = [
    "hypothesis-tournament",
    "scientific-novelty-checker",
    "experimental-design-planner",
    "ro-crate-provenance-export",
    "nextflow-pipeline-runner",
    "snakemake-pipeline-runner",
    "cwl-workflow-bridge",
    "asreview-screening-bridge",
    "risk-of-bias-assistant",
    "grade-sof-table-builder",
    "openalex-literature-graph",
    "open-targets-drug-targeting",
    "chembl-bindingdb-miner",
    "alphafold-pdb-structure-router",
    "in-silico-validation-governor",
    "agent-benchmark-harness",
    "scientific-red-team-reviewer",
    "query-string-governor",
    "database-retrieval-governor",
    "topic-ideation-tournament",
    "evidence-lock-hardener",
    "stage-audit-governor",
    "author-identity-resolver",
    "guideline-router",
    "retraction-integrity-checker",
    "ptbr-article-writing",
    "anti-ai-writing-governor",
    "deep-thinking-governor",
    "zotero-reference-manager",
    "life-science-router",
    "ngs-analysis-router",
]

try:
    from article_machine.agent_skills import WORLD_CLASS_SKILLS as ARTICLE_MACHINE_SKILLS
except Exception:
    ARTICLE_MACHINE_SKILLS = ()

CRITICAL_SKILLS = list(dict.fromkeys([*CRITICAL_SKILLS, *ARTICLE_MACHINE_SKILLS, "meta-analise-medica", "metodos-ml-clinico", "publicacao-medica-organizada", "catalogos-cientificos-sob-demanda"]))

NAVIGATION_SKILLS = [
    "workspace-graph-navigator",
    "project-entry-navigator",
    "content-preservation-guardian",
]

DETAILED_DOCS = [
    ".AGENTES",
    "docs/ingles/AGENTES_DA_MAQUINA.md",
    "docs/portugues/GUIA_DA_MAQUINA.md",
    "docs/ingles/GUIA_DA_MAQUINA.md",
    "docs/portugues/ESTADO_E_LIMITES_DA_MAQUINA.md",
    "docs/ingles/ESTADO_E_LIMITES_DA_MAQUINA.md",
    "integracoes/catalogos_cientificos/portugues/catalogo_sob_demanda.md",
    "integracoes/catalogos_cientificos/ingles/catalogo_sob_demanda.md",
    "LEIA-ME_PRIMEIRO.md",
    "docs/ARQUITETURA_FINAL.md",
    "docs/FLUXOS_CIENTIFICOS.md",
    "docs/INVENTARIO_CODEX.md",
    "docs/MATRIZ_SKILLS.md",
    "docs/ORGANIZACAO_DAS_PUBLICACOES.md",
    ".agents/AGENTS.md",
    ".agents/GRAPH_FIRST.md",
    ".agents/README.md",
    ".codex/README.md",
    "AGENTS.md",
    "AGENT_MANIFEST.md",
    "README.md",
    "SKILL_INDEX.md",
    "SKILLS_CANON.md",
    "docs/AGENT_START_HERE.md",
    "docs/AGENT_OPERATION_MAP.md",
    "docs/ARTICLE_MACHINE_AGENT_PLAYBOOK.md",
    "docs/WORKSPACE_REORG_PLAN.md",
    "docs/SCIENTIFIC_WORKFLOWS.md",
    "docs/MIGRATION_0_3.md",
    "docs/INDICE_DO_WORKSPACE.md",
    "docs/ESTADO_DOS_PROJETOS.md",
    "docs/AMBIENTES_E_LOCKS.md",
    "docs/ORGANIZACAO_E_LIMPEZA.md",
    "docs/MIGRACAO_PARA_D.md",
    "docs/MIGRACAO_PARA_D_STATUS.md",
    "docs/GIT_E_WORKTREES.md",
    "graphify-out/LEIA-ME.md",
]

CODEX_AGENT_FILES = [
    ".codex/agents/workspace-explorer.toml",
    ".codex/agents/scientific-reviewer.toml",
    ".codex/agents/verification-runner.toml",
    ".codex/agents/worker.toml",
    ".codex/agents/luna-analyst.toml",
]

CODEX_PROFILE_FILES = [
    ".codex/profiles/xhigh-baseline.config.toml",
    ".codex/profiles/ultra-benchmark.config.toml",
]

PROJECT_CONTRACT_FILES = ["project.yaml", "protocol.yaml", "standards.yaml", "compute.yaml"]

PROJECT_ARTIFACT_DIRS = {
    "sources": "source registry and raw/converted intake",
    "context": "briefs, retrieval plans, and task packets",
    "evidence": "claim maps and evidence locks",
    "analysis": "analysis outputs and run envelopes",
    "drafts": "manuscripts and references",
    "reviews": "review reports and red-team notes",
    "figures": "figures and visual assets",
    "deliverables": "conference decks posters and submission packs",
}

GATEWAY_BRIDGES = {
    "deep-thinking-governor": {
        "target_id": "gate_deep_thinking_decision_quality",
        "target_label": "Decision quality gate for assumptions alternatives premortems",
        "target_type": "rationale",
        "relation": "guards",
        "artifact_id": "artifact_decision_risk_notes",
        "artifact_label": "decision notes residual-risk summaries",
        "artifact_relation": "documents",
    },
    "zotero-reference-manager": {
        "target_id": "plugin_zotero_reference_manager",
        "target_label": "Zotero plugin local library and attachment API",
        "target_type": "code",
        "relation": "bridges_to",
        "artifact_id": "artifact_project_references_bib",
        "artifact_label": "project drafts/references.bib",
        "artifact_relation": "syncs",
    },
    "life-science-router": {
        "target_id": "plugin_life_science_research_router",
        "target_label": "Life Science Research plugin router",
        "target_type": "code",
        "relation": "bridges_to",
        "artifact_id": "artifact_life_science_evidence",
        "artifact_label": "project evidence/life_science outputs",
        "artifact_relation": "writes",
    },
    "ngs-analysis-router": {
        "target_id": "plugin_ngs_analysis_router",
        "target_label": "Life Sciences NGS Analysis plugin router",
        "target_type": "code",
        "relation": "bridges_to",
        "artifact_id": "artifact_ngs_run_envelopes",
        "artifact_label": "project analysis/ngs run envelopes",
        "artifact_relation": "writes",
    },
}

LEGACY_ROOT_DIRS = [
    "Correção Orientador",
    "Doutorado",
    "Leitor de Artigos",
    "PDFS DR ANDRÉ",
    "REVISÃO LIGA",
    "Revisões Sistemáticas",
    "Submissão Final",
    "NMA_OSA_VPI",
]
# Keep source ASCII while preserving the real Windows directory names.
LEGACY_ROOT_DIRS = [
    "Corre\u00e7\u00e3o Orientador",
    "Doutorado",
    "Leitor de Artigos",
    "PDFS DR ANDR\u00c9",
    "REVIS\u00c3O LIGA",
    "Revis\u00f5es Sistem\u00e1ticas",
    "Submiss\u00e3o Final",
    "NMA_OSA_VPI",
]

HYGIENE_TARGETS = {
    ".agents": "local agent control plane; track only policy files and selected navigation skills",
    ".venv": "local virtual environment; never stage",
    ".pytest_cache": "pytest cache; generated",
    ".playwright-osf": "browser automation cache; generated",
    "tmp": "temporary workspace output",
    "sources": "shared source intake; review before staging raw data",
    "graphify-out": "generated operational graph outputs",
}

AGENT_FLOW_STEPS = [
    ("flow_start_here", "Read docs/AGENT_START_HERE.md"),
    ("flow_agents_control_plane", "Read .agents/AGENTS.md"),
    ("flow_machine_audit", "Run article_machine machine audit --strict"),
    ("flow_graph_report", "Open graphify-out/GRAPH_REPORT.md"),
    ("flow_graph_readme", "Read graphify-out/LEIA-ME.md for the generated file map"),
    ("flow_graph_first_query", "Query graph before broad navigation"),
    ("flow_project_select", "Select or create projects/<project_id>"),
    ("flow_project_contract", "Read project protocol standards compute files"),
    ("flow_skill_route", "Run article_machine skills route"),
    ("flow_task_packet", "Build context Task Packet"),
    ("flow_evidence_lock", "Validate Evidence Lock before ready claims"),
]

NATURAL_LANGUAGE_GATEWAYS = [
    {
        "id": "alias_pt_agent_new_workspace",
        "label": "pergunta: agente novo navegar workspace doutorado",
        "targets": [
            "skill_workspace_graph_navigator",
            "skill_project_entry_navigator",
            "flow_start_here",
            "flow_agents_control_plane",
            "flow_graph_report",
            "flow_graph_first_query",
            "flow_project_select",
        ],
    },
    {
        "id": "alias_pt_always_use_graph",
        "label": "regra: usar graph mesmo sem usuario pedir quando precisar",
        "targets": ["flow_agents_control_plane", "flow_graph_first_query", "skill_workspace_graph_navigator", "graphify_report"],
    },
    {
        "id": "alias_pt_graph_fluidity",
        "label": "pedido: atualizar graph melhorar fluidez graph html",
        "targets": ["skill_workspace_graph_navigator", "graphify_refresh_script", "graphify_html", "graphify_report"],
    },
    {
        "id": "alias_pt_project_active",
        "label": "pedido: escolher projeto ativo article machine",
        "targets": ["skill_project_entry_navigator", "flow_project_select", "hub_projects", "runtime_venv_article_machine"],
    },
    {
        "id": "alias_pt_content_preservation",
        "label": "pedido: reorganizar sem comprometer conteudo bruto",
        "targets": ["skill_content_preservation_guardian", "hub_legacy", "hub_git"],
    },
    {
        "id": "alias_pt_skill_route",
        "label": "pedido: rotear skill para pergunta cientifica",
        "targets": ["flow_skill_route", "runtime_skills_route", "hub_skills"],
    },
    {
        "id": "alias_pt_evidence_lock",
        "label": "pedido: validar evidence lock antes de draft pronto",
        "targets": ["flow_evidence_lock", "module_evidence", "module_zero_trust"],
    },
    {
        "id": "alias_pt_zotero_references",
        "label": "pedido: zotero referencias bibtex biblioteca local",
        "targets": ["skill_zotero_reference_manager", "plugin_zotero_reference_manager", "artifact_project_references_bib"],
    },
    {
        "id": "alias_pt_life_science",
        "label": "pedido: life science pesquisa biomedica descoberta",
        "targets": ["skill_life_science_router", "plugin_life_science_research_router", "artifact_life_science_evidence"],
    },
    {
        "id": "alias_pt_ngs",
        "label": "pedido: ngs fastq bam vcf sequenciamento",
        "targets": ["skill_ngs_analysis_router", "plugin_ngs_analysis_router", "artifact_ngs_run_envelopes"],
    },
    {
        "id": "alias_pt_deep_thinking",
        "label": "pedido: pensamento profundo decisao forte hipotese fragil",
        "targets": ["skill_deep_thinking_governor", "gate_deep_thinking_decision_quality", "artifact_decision_risk_notes"],
    },
    {
        "id": "alias_pt_ptbr_article",
        "label": "pedido: artigo pt br abnt vancouver sem cara de ia",
        "targets": ["skill_ptbr_article_writing", "skill_anti_ai_writing_governor", "module_ptbr_style"],
    },
    {
        "id": "alias_pt_model_orchestration",
        "label": "pedido: melhorar maquina sol medio luna trabalhos cientificos complexos ingles portugues",
        "targets": [
            "codex_project_config",
            "codex_agent_workspace_explorer",
            "codex_agent_scientific_reviewer",
            "codex_agent_verification_runner",
            "codex_profile_xhigh_baseline",
            "codex_profile_ultra_benchmark",
            "skill_skill_upgrade_governor",
            "skill_agent_benchmark_harness",
            "runtime_benchmark_validate",
            "runtime_machine_audit",
        ],
    },
    {
        "id": "alias_pt_workspace_index",
        "label": "pedido: indice do workspace painel de projetos estado atual",
        "targets": [
            "nav_workspace_index",
            "doc_docs_indice_do_workspace_md",
            "doc_docs_estado_dos_projetos_md",
            "hub_projects",
        ],
    },
    {
        "id": "alias_pt_environment_restore",
        "label": "pedido: restaurar ambiente r renv python uv lock quarto playwright",
        "targets": [
            "env_r_science",
            "env_python_root",
            "env_python_ml",
            "env_quarto",
            "env_playwright",
            "doc_docs_ambientes_e_locks_md",
        ],
    },
    {
        "id": "alias_pt_cleanup_no_delete",
        "label": "pedido: organizar limpar workspace sem excluir conteudo bruto",
        "targets": [
            "skill_content_preservation_guardian",
            "doc_docs_organizacao_e_limpeza_md",
            "doc_docs_git_e_worktrees_md",
            "hub_git",
        ],
    },
    {
        "id": "alias_pt_migration_c_d",
        "label": "pedido: migracao c para d backup legado archive",
        "targets": [
            "doc_docs_migracao_para_d_md",
            "doc_docs_migracao_para_d_status_md",
            "hub_legacy",
            "doc_docs_organizacao_e_limpeza_md",
        ],
    },
    {
        "id": "alias_pt_dirty_worktree",
        "label": "pedido: worktree sujo git status antes de commit",
        "targets": [
            "hub_git",
            "doc_docs_git_e_worktrees_md",
            "doc_docs_organizacao_e_limpeza_md",
        ],
    },
    {
        "id": "alias_pt_graph_files",
        "label": "pedido: abrir grafo operacional graph html graph report",
        "targets": [
            "doc_graphify_out_leia_me_md",
            "graphify_report",
            "graphify_html",
            "graphify_refresh_script",
            "hub_graphify",
        ],
    },
]

MODULE_GROUPS = {
    "module_group_entrypoints": {
        "label": "Article Machine entrypoints and CLI",
        "modules": {"__init__", "__main__", "cli"},
    },
    "module_group_project_runtime": {
        "label": "Project contracts context runs and serialization",
        "modules": {"projects", "context", "ingest", "runs", "serialization", "standards"},
    },
    "module_group_evidence_gates": {
        "label": "Evidence Lock retrieval journal review and zero-trust gates",
        "modules": {"benchmarks", "evidence", "zero_trust", "review", "journals"},
    },
    "module_group_discovery_analysis": {
        "label": "Analysis discovery and life-science planning",
        "modules": {"analysis", "discovery", "life_science"},
    },
    "module_group_deliverables": {
        "label": "Deck poster visual and Playwright deliverables",
        "modules": {"deliverables", "deliverable_contracts", "congress_profiles", "pptx_bridge", "playwright_ops", "visuals"},
    },
    "module_group_skills_style": {
        "label": "Skill routing and PT-BR style gates",
        "modules": {"agent_skills", "ptbr_style"},
    },
}

COMMUNITY_COLORS = [
    "#4E79A7",
    "#F28E2B",
    "#59A14F",
    "#E15759",
    "#B07AA1",
    "#76B7B2",
    "#EDC948",
    "#9C755F",
    "#BAB0AC",
]


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in normalized)
    return "_".join(part for part in cleaned.split("_") if part) or "node"


def read_structured(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        from article_machine.serialization import load_structured_file

        payload = load_structured_file(path)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def markdown_headings(path: Path, max_count: int | None = None) -> list[tuple[int, str]]:
    if not path.exists():
        return []
    headings: list[tuple[int, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        marker, _, title = stripped.partition(" ")
        if not title or any(character != "#" for character in marker):
            continue
        level = len(marker)
        if level > 3:
            continue
        headings.append((level, title.strip()))
        if max_count and len(headings) >= max_count:
            break
    return headings


def direct_child_count(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    try:
        return sum(1 for _child in path.iterdir())
    except OSError:
        return 0


def write_utf8_lf(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize_utf8_lf(path: Path) -> None:
    write_utf8_lf(path, path.read_text(encoding="utf-8"))


def add_node(nodes: dict[str, dict[str, Any]], node_id: str, label: str, file_type: str, source_file: str = "") -> None:
    nodes[node_id] = {
        "id": node_id,
        # Graphify may canonicalize semantic node IDs from source_file during
        # build_from_json. Keep our stable ID as data so the hand-authored
        # community contract can be reconciled with the built graph.
        "operational_id": node_id,
        "label": label,
        "file_type": file_type,
        "source_file": source_file,
        "source_location": None,
        "source_url": None,
        "captured_at": None,
        "author": None,
        "contributor": None,
    }


def add_edge(
    edges: list[dict[str, Any]],
    source: str,
    target: str,
    relation: str,
    confidence: str = "EXTRACTED",
    source_file: str = "",
    weight: float = 1.0,
) -> None:
    edges.append(
        {
            "source": source,
            "target": target,
            "relation": relation,
            "confidence": confidence,
            "confidence_score": 1.0 if confidence == "EXTRACTED" else 0.75,
            "source_file": source_file,
            "source_location": None,
            "weight": weight,
        }
    )


def cli_commands() -> list[str]:
    cli_path = ROOT / "article_machine" / "cli.py"
    tree = ast.parse(cli_path.read_text(encoding="utf-8"))
    commands: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        attr = getattr(node.func, "attr", "")
        if attr != "add_parser" or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            commands.append(first.value)
    ignored = {"register", "build", "import", "plan", "qa", "dry-run", "run", "catalog", "audit", "route"}
    return sorted({cmd for cmd in commands if cmd not in ignored})


def project_dirs() -> list[Path]:
    projects_root = ROOT / "projects"
    if not projects_root.exists():
        return []
    return sorted(
        p
        for p in projects_root.iterdir()
        if p.is_dir()
        and all((p / name).exists() for name in ["project.yaml", "protocol.yaml", "standards.yaml", "compute.yaml"])
    )


@lru_cache(maxsize=1)
def git_generation_state() -> dict[str, Any]:
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip()
        status_lines = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=normal"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return {
            "available": False,
            "head_commit": None,
            "worktree_dirty": None,
            "status_entry_count": None,
        }
    return {
        "available": True,
        "head_commit": head or None,
        "worktree_dirty": bool(status_lines),
        "status_entry_count": len(status_lines),
    }


def build_extraction() -> tuple[dict[str, Any], dict[int, list[str]], dict[int, str], dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    detail_counts = {
        "doc_sections": 0,
        "project_contracts": 0,
        "project_artifact_areas": 0,
        "skill_sections": 0,
        "navigation_skills": 0,
        "codex_agents": 0,
        "codex_profiles": 0,
    }

    add_node(nodes, "workspace_doutorado", "Doutorado Workspace", "document", ".")
    hubs = {
        "hub_runtime": "Runtime And Commands",
        "hub_article_machine": "Article Machine Package",
        "hub_projects": "Article Machine Projects",
        "hub_skills": "Critical Scientific Skills",
        "hub_docs": "Agent Documentation",
        "hub_legacy": "Legacy And Raw Sources",
        "hub_graphify": "Graphify Operational Map",
        "hub_git": "Git Hygiene",
    }
    for node_id, label in hubs.items():
        add_node(nodes, node_id, label, "rationale", ".")
        add_edge(edges, "workspace_doutorado", node_id, "contains", "EXTRACTED", ".")

    # Every top-level area is represented without reading its scientific content.
    for directory in sorted((p for p in ROOT.iterdir() if p.is_dir()), key=lambda p: p.name):
        rel = directory.name
        node_id = "tree_area_" + slug(rel)
        add_node(nodes, node_id, "Área / Area: " + rel, "directory", rel)
        add_edge(edges, "workspace_doutorado", node_id, "contains_area", "EXTRACTED", rel)
        add_edge(edges, "hub_graphify", node_id, "structural_navigation", "EXTRACTED", rel)
    for rel, label in {
        "graphify-out/arvore_da_maquina/graph.json": "Grafo estrutural da pasta inteira / Whole-root structural graph",
        "graphify-out/arvore_da_maquina/arvore_navegavel.html": "Árvore navegável / Navigable tree",
        "integracoes/catalogos_cientificos/manifesto_das_fontes.json": "Cinco fontes fixadas / Five pinned sources",
        "integracoes/catalogos_cientificos/inventario_de_habilidades.json": "Catálogo completo de nomes / Full name catalog",
        "modelos/publicacao_em_revistas/portugues/LEIA-ME.md": "Kit editorial PT / Editorial kit PT",
        "modelos/publicacao_em_revistas/ingles/LEIA-ME.md": "Kit editorial EN / Editorial kit EN",
        "modelos/publicacao_em_revistas/perfis_de_revistas/catalogo_revistas.json": "Seis perfis de revistas / Six journal profiles",
        "modelos/registro_de_protocolo/portugues/LEIA-ME.md": "Protocolo e registro / Protocol registration",
        "modelos/estatistica_e_figuras/portugues/LEIA-ME.md": "R, estatística e figuras / R statistics and figures",
    }.items():
        if (ROOT / rel).exists():
            node_id = "graphify_new_" + slug(rel)
            add_node(nodes, node_id, label, "document", rel)
            add_edge(edges, "hub_graphify", node_id, "navigates_to", "EXTRACTED", rel)
            add_edge(edges, "tree_area_" + slug(rel.split("/")[0]), node_id,
                     "stores_artifact", "EXTRACTED", rel)

    runtime_nodes = {
        "runtime_venv_article_machine": ".venv python -m article_machine",
        "runtime_venv_graphify": ".venv python -m graphify",
        "runtime_global_graphify": "global python -m graphify",
        "runtime_pytest": ".venv python -m pytest",
        "runtime_machine_audit": "article_machine machine audit --strict",
        "runtime_benchmark_validate": "article_machine benchmark validate",
        "runtime_skills_route": "article_machine skills route",
        "runtime_skills_audit": "article_machine skills audit",
    }
    for node_id, label in runtime_nodes.items():
        add_node(nodes, node_id, label, "code", "docs/AGENT_START_HERE.md")
        add_edge(edges, "hub_runtime", node_id, "documents", "EXTRACTED", "docs/AGENT_START_HERE.md")
    add_edge(edges, "runtime_venv_article_machine", "hub_article_machine", "runs", "EXTRACTED", "docs/AGENT_START_HERE.md")
    add_edge(edges, "runtime_venv_graphify", "hub_graphify", "runs", "EXTRACTED", "docs/AGENT_START_HERE.md")
    add_edge(edges, "runtime_global_graphify", "hub_graphify", "runs", "EXTRACTED", "docs/AGENT_START_HERE.md")
    add_edge(edges, "runtime_pytest", "hub_article_machine", "validates", "EXTRACTED", "tests/test_agent_skills.py")
    add_edge(edges, "runtime_machine_audit", "hub_article_machine", "audits", "EXTRACTED", "article_machine/cli.py")
    add_edge(edges, "runtime_benchmark_validate", "hub_article_machine", "validates", "EXTRACTED", "article_machine/benchmarks.py")
    add_edge(edges, "runtime_skills_audit", "hub_skills", "audits", "EXTRACTED", "article_machine/agent_skills.py")

    for doc in DETAILED_DOCS:
        path = ROOT / doc
        if path.exists():
            node_id = "doc_" + slug(doc)
            add_node(nodes, node_id, doc, "document", doc)
            add_edge(edges, "hub_docs", node_id, "documents", "EXTRACTED", doc)
            add_edge(edges, node_id, "hub_article_machine", "references", "INFERRED", doc, 0.8)
            previous_section_id = ""
            for index, (level, title) in enumerate(markdown_headings(path), start=1):
                section_id = "doc_section_" + slug(f"{doc}_{index}_{title}")
                add_node(nodes, section_id, f"{doc} :: {title}", "document", doc)
                nodes[section_id]["section_level"] = level
                add_edge(edges, node_id, section_id, "has_section", "EXTRACTED", doc)
                if previous_section_id:
                    add_edge(edges, previous_section_id, section_id, "next_section", "EXTRACTED", doc)
                previous_section_id = section_id
                detail_counts["doc_sections"] += 1

    # Environment and lock nodes: restoration must be discoverable by intent.
    environment_nodes = {
        "env_python_root": ("Python 3.13 root uv environment", "uv.lock"),
        "env_python_ml": ("Clinical ML Python uv environments", "modelos/aprendizado_de_maquina_clinico/uv.lock"),
        "env_r_science": ("R 4.6.1 renv scientific environment", "modelos/meta_analise_em_r/renv.lock"),
        "env_quarto": ("Quarto 1.10.20 portable toolchain", "ferramentas/quarto-1.10.20/bin/quarto.exe"),
        "env_playwright": ("Playwright 1.61.1 browser tooling", "tools/playwright/package-lock.json"),
    }
    environments_doc = ROOT / "docs" / "AMBIENTES_E_LOCKS.md"
    for node_id, (label, source) in environment_nodes.items():
        add_node(nodes, node_id, label, "code", source)
        add_edge(edges, "hub_runtime", node_id, "documents", "EXTRACTED", source)
        if environments_doc.exists():
            add_edge(
                edges,
                node_id,
                "doc_docs_ambientes_e_locks_md",
                "documented_by",
                "EXTRACTED",
                str(environments_doc.relative_to(ROOT)),
            )

    lock_nodes = {
        "env_root_lock": ("Root Python lock (uv.lock)", "uv.lock", "env_python_root"),
        "env_ml_lock": (
            "Clinical ML lock (uv.lock)",
            "modelos/aprendizado_de_maquina_clinico/uv.lock",
            "env_python_ml",
        ),
        "env_r_lock": (
            "Scientific R lock (renv.lock)",
            "modelos/meta_analise_em_r/renv.lock",
            "env_r_science",
        ),
        "env_playwright_lock": (
            "Playwright lock (package-lock.json)",
            "tools/playwright/package-lock.json",
            "env_playwright",
        ),
    }
    for node_id, (label, source, owner) in lock_nodes.items():
        if (ROOT / source).exists():
            add_node(nodes, node_id, label, "document", source)
            add_edge(edges, node_id, owner, "locks", "EXTRACTED", source)
            add_edge(edges, owner, node_id, "locked_by", "EXTRACTED", source)

    r_updater = ROOT / "scripts" / "atualizar_ambiente_meta_analise.R"
    if r_updater.exists():
        add_node(
            nodes,
            "env_r_updater",
            "R environment updater and lock validator",
            "code",
            "scripts/atualizar_ambiente_meta_analise.R",
        )
        add_edge(
            edges,
            "env_r_updater",
            "env_r_science",
            "updates",
            "EXTRACTED",
            "scripts/atualizar_ambiente_meta_analise.R",
        )
        add_edge(
            edges,
            "env_r_updater",
            "env_r_lock",
            "writes",
            "EXTRACTED",
            "scripts/atualizar_ambiente_meta_analise.R",
        )

    # One navigation hub for humans and agents entering the workspace.
    add_node(
        nodes,
        "nav_workspace_index",
        "Workspace Navigation Index",
        "rationale",
        "docs/INDICE_DO_WORKSPACE.md",
    )
    add_edge(
        edges,
        "workspace_doutorado",
        "nav_workspace_index",
        "starts_at",
        "EXTRACTED",
        "docs/INDICE_DO_WORKSPACE.md",
    )
    add_edge(
        edges,
        "hub_docs",
        "nav_workspace_index",
        "documents",
        "EXTRACTED",
        "docs/INDICE_DO_WORKSPACE.md",
    )
    navigation_targets = {
        "doc_docs_indice_do_workspace_md": "workspace map",
        "doc_docs_estado_dos_projetos_md": "project dashboard",
        "doc_docs_ambientes_e_locks_md": "environments and locks",
        "doc_docs_organizacao_e_limpeza_md": "organization and cleanup policy",
        "doc_docs_git_e_worktrees_md": "git and worktree hygiene",
        "doc_docs_migracao_para_d_status_md": "migration status",
    }
    for target_id, relation in navigation_targets.items():
        if target_id in nodes:
            add_edge(
                edges,
                "nav_workspace_index",
                target_id,
                "routes_to",
                "EXTRACTED",
                "docs/INDICE_DO_WORKSPACE.md",
            )
            add_edge(
                edges,
                target_id,
                "nav_workspace_index",
                relation.replace(" ", "_"),
                "INFERRED",
                "docs/INDICE_DO_WORKSPACE.md",
                0.8,
            )
    add_edge(
        edges,
        "nav_workspace_index",
        "hub_projects",
        "routes_to",
        "EXTRACTED",
        "docs/ESTADO_DOS_PROJETOS.md",
    )
    add_edge(
        edges,
        "nav_workspace_index",
        "hub_runtime",
        "routes_to",
        "EXTRACTED",
        "docs/AMBIENTES_E_LOCKS.md",
    )

    codex_readme = ".codex/README.md"
    if (ROOT / codex_readme).exists():
        add_node(nodes, "codex_control_plane", "Codex project control plane", "document", codex_readme)
        add_edge(edges, "hub_docs", "codex_control_plane", "documents", "EXTRACTED", codex_readme)
        add_edge(edges, "codex_control_plane", "doc_codex_readme_md", "explained_by", "EXTRACTED", codex_readme)
        for section_id in [node_id for node_id in nodes if node_id.startswith("doc_section_codex_readme_md_")]:
            add_edge(edges, section_id, "codex_control_plane", "summarizes", "EXTRACTED", codex_readme)
    codex_config = ".codex/config.toml"
    if (ROOT / codex_config).exists():
        add_node(nodes, "codex_project_config", "Codex project configuration", "document", codex_config)
        add_edge(edges, "codex_control_plane", "codex_project_config", "configures", "EXTRACTED", codex_config)
        add_edge(edges, "codex_project_config", "runtime_machine_audit", "preserves_project_gates", "INFERRED", codex_config, 0.8)
    for agent_file in CODEX_AGENT_FILES:
        path = ROOT / agent_file
        if not path.exists():
            continue
        agent_id = "codex_agent_" + slug(path.stem)
        add_node(nodes, agent_id, f"Codex role: {path.stem}", "document", agent_file)
        relation = "declares_read_only_role" if 'sandbox_mode = "read-only"' in path.read_text(encoding="utf-8") else "declares_bounded_worker_role"
        add_edge(edges, "codex_project_config", agent_id, relation, "EXTRACTED", agent_file)
        add_edge(edges, agent_id, "codex_control_plane", "governed_by", "EXTRACTED", agent_file)
        detail_counts["codex_agents"] += 1
    for profile_file in CODEX_PROFILE_FILES:
        path = ROOT / profile_file
        if not path.exists():
            continue
        profile_id = "codex_profile_" + slug(path.stem.replace(".config", ""))
        add_node(nodes, profile_id, f"Codex read-only profile: {path.stem}", "document", profile_file)
        add_edge(edges, "codex_control_plane", profile_id, "provides_benchmark_profile", "EXTRACTED", profile_file)
        add_edge(edges, profile_id, "runtime_machine_audit", "must_respect", "INFERRED", profile_file, 0.8)
        detail_counts["codex_profiles"] += 1

    previous_flow_id = ""
    for flow_id, label in AGENT_FLOW_STEPS:
        add_node(nodes, flow_id, label, "rationale", "docs/AGENT_OPERATION_MAP.md")
        add_edge(edges, "hub_docs", flow_id, "operationalizes", "EXTRACTED", "docs/AGENT_OPERATION_MAP.md")
        if previous_flow_id:
            add_edge(edges, previous_flow_id, flow_id, "next_step", "EXTRACTED", "docs/AGENT_OPERATION_MAP.md")
        previous_flow_id = flow_id
    add_edge(edges, "flow_skill_route", "runtime_skills_route", "uses", "EXTRACTED", "docs/AGENT_OPERATION_MAP.md")
    add_edge(edges, "flow_machine_audit", "runtime_machine_audit", "uses", "EXTRACTED", "docs/AGENT_OPERATION_MAP.md")
    add_edge(edges, "flow_graph_report", "hub_graphify", "uses", "EXTRACTED", "docs/AGENT_OPERATION_MAP.md")

    for module in sorted((ROOT / "article_machine").rglob("*.py")):
        module_name = module.relative_to(ROOT / "article_machine").with_suffix("").as_posix().replace("/", ".")
        node_id = "module_" + slug(module_name)
        rel = module.relative_to(ROOT).as_posix()
        add_node(nodes, node_id, f"article_machine.{module_name}", "code", rel)
        add_edge(edges, "hub_article_machine", node_id, "contains", "EXTRACTED", rel)
        for group_id, group in MODULE_GROUPS.items():
            if module.stem in group["modules"]:
                add_node(nodes, group_id, str(group["label"]), "rationale", "scripts/generate_workspace_graph.py")
                add_edge(edges, "hub_article_machine", group_id, "organizes", "EXTRACTED", "scripts/generate_workspace_graph.py")
                add_edge(edges, group_id, node_id, "contains_module", "EXTRACTED", rel)
                break

    for command in cli_commands():
        node_id = "cli_" + slug(command)
        add_node(nodes, node_id, f"article-machine {command}", "code", "article_machine/cli.py")
        add_edge(edges, "module_cli", node_id, "defines_cli", "EXTRACTED", "article_machine/cli.py")
        add_edge(edges, "hub_runtime", node_id, "exposes", "EXTRACTED", "article_machine/cli.py")

    for project_dir in project_dirs():
        project = read_structured(project_dir / "project.yaml")
        protocol = read_structured(project_dir / "protocol.yaml")
        rel = project_dir.relative_to(ROOT).as_posix()
        label = project.get("name") or project_dir.name
        node_id = "project_" + slug(project_dir.name)
        add_node(nodes, node_id, str(label), "document", f"{rel}/project.yaml")
        add_edge(edges, "hub_projects", node_id, "contains", "EXTRACTED", f"{rel}/project.yaml")
        lane = str(project.get("lane") or "unknown")
        mode = str(project.get("state", {}).get("current_mode") or "unknown")
        ptype = str(project.get("project_type") or "unknown")
        for value, prefix, relation in [(lane, "lane", "uses_lane"), (mode, "mode", "current_mode"), (ptype, "type", "project_type")]:
            meta_id = f"{prefix}_{slug(value)}"
            add_node(nodes, meta_id, f"{prefix}: {value}", "rationale", f"{rel}/project.yaml")
            add_edge(edges, "hub_projects", meta_id, f"catalogs_{prefix}", "EXTRACTED", f"{rel}/project.yaml")
            add_edge(edges, node_id, meta_id, relation, "EXTRACTED", f"{rel}/project.yaml")
        for contract_file in PROJECT_CONTRACT_FILES:
            contract_path = project_dir / contract_file
            if not contract_path.exists():
                continue
            contract_rel = contract_path.relative_to(ROOT).as_posix()
            contract_id = f"project_contract_{slug(project_dir.name)}_{slug(contract_file)}"
            add_node(nodes, contract_id, f"{project_dir.name}/{contract_file}", "document", contract_rel)
            add_edge(edges, node_id, contract_id, "has_contract_file", "EXTRACTED", contract_rel)
            add_edge(edges, contract_id, "flow_project_contract", "satisfies_entry_check", "EXTRACTED", contract_rel)
            detail_counts["project_contracts"] += 1
        for artifact_dir, purpose in PROJECT_ARTIFACT_DIRS.items():
            artifact_path = project_dir / artifact_dir
            if not artifact_path.exists():
                continue
            artifact_rel = artifact_path.relative_to(ROOT).as_posix()
            artifact_id = f"project_artifact_{slug(project_dir.name)}_{slug(artifact_dir)}"
            count = direct_child_count(artifact_path)
            add_node(nodes, artifact_id, f"{project_dir.name}/{artifact_dir} ({count} direct items)", "document", artifact_rel)
            nodes[artifact_id]["artifact_purpose"] = purpose
            nodes[artifact_id]["direct_child_count"] = count
            add_edge(edges, node_id, artifact_id, "has_artifact_area", "EXTRACTED", artifact_rel)
            add_edge(edges, artifact_id, "flow_task_packet", "feeds_or_records_context", "INFERRED", artifact_rel, 0.7)
            detail_counts["project_artifact_areas"] += 1
        if not protocol.get("research_question"):
            add_edge(edges, node_id, "hub_git", "needs_review_missing_research_question", "INFERRED", f"{rel}/protocol.yaml", 0.6)

    skills_root = ROOT / "skills"
    for skill_name in CRITICAL_SKILLS:
        skill_path = skills_root / skill_name / "SKILL.md"
        if skill_path.exists():
            node_id = "skill_" + slug(skill_name)
            rel = skill_path.relative_to(ROOT).as_posix()
            add_node(nodes, node_id, skill_name, "document", rel)
            add_edge(edges, "hub_skills", node_id, "routes_to", "EXTRACTED", rel)
            add_edge(edges, "module_agent_skills", node_id, "routes_query_to", "EXTRACTED", "article_machine/agent_skills.py")
            add_edge(edges, "doc_SKILL_INDEX_md".lower(), node_id, "references", "INFERRED", "SKILL_INDEX.md", 0.8)
            if skill_name in NAVIGATION_SKILLS:
                detail_counts["navigation_skills"] += 1
                add_edge(edges, node_id, "hub_docs", "supports_navigation", "EXTRACTED", rel)
                add_edge(edges, node_id, "hub_legacy", "protects_or_scopes", "INFERRED", rel, 0.7)
            previous_skill_section_id = ""
            for index, (level, title) in enumerate(markdown_headings(skill_path, max_count=12), start=1):
                section_id = f"skill_section_{slug(skill_name)}_{index}_{slug(title)}"
                add_node(nodes, section_id, f"{skill_name} :: {title}", "document", rel)
                nodes[section_id]["section_level"] = level
                add_edge(edges, node_id, section_id, "has_instruction_section", "EXTRACTED", rel)
                if previous_skill_section_id:
                    add_edge(edges, previous_skill_section_id, section_id, "next_section", "EXTRACTED", rel)
                previous_skill_section_id = section_id
                detail_counts["skill_sections"] += 1
            bridge = GATEWAY_BRIDGES.get(skill_name)
            if bridge:
                target_id = str(bridge["target_id"])
                artifact_id = str(bridge["artifact_id"])
                add_node(nodes, target_id, str(bridge["target_label"]), str(bridge["target_type"]), rel)
                add_node(nodes, artifact_id, str(bridge["artifact_label"]), "document", rel)
                add_edge(edges, node_id, target_id, str(bridge["relation"]), "EXTRACTED", rel)
                add_edge(edges, node_id, artifact_id, str(bridge["artifact_relation"]), "EXTRACTED", rel)
                add_edge(edges, target_id, artifact_id, "feeds", "INFERRED", rel, 0.7)
                add_edge(edges, "runtime_skills_route", node_id, "selects", "EXTRACTED", "article_machine/agent_skills.py")

    for dirname in LEGACY_ROOT_DIRS:
        path = ROOT / dirname
        if path.exists():
            node_id = "legacy_" + slug(dirname)
            add_node(nodes, node_id, f"legacy: {dirname}", "rationale", dirname)
            add_edge(edges, "hub_legacy", node_id, "needs_triage", "INFERRED", dirname, 0.7)
            add_edge(edges, node_id, "hub_git", "review_before_staging", "INFERRED", dirname, 0.7)

    for dirname, label in HYGIENE_TARGETS.items():
        if (ROOT / dirname).exists():
            node_id = "hygiene_" + slug(dirname)
            add_node(nodes, node_id, label, "rationale", dirname)
            add_edge(edges, "hub_git", node_id, "exclude_or_review", "EXTRACTED", ".gitignore")
            add_edge(edges, node_id, "doc_docs_workspace_reorg_plan_md", "documented_by", "EXTRACTED", "docs/WORKSPACE_REORG_PLAN.md")

    if (ROOT / "projects" / "projects").exists():
        add_node(nodes, "defect_nested_projects", "projects/projects nested directory", "rationale", "projects/projects")
        add_edge(edges, "hub_projects", "defect_nested_projects", "needs_review", "INFERRED", "projects/projects", 0.8)
        add_edge(edges, "defect_nested_projects", "hub_git", "hygiene_risk", "INFERRED", "projects/projects", 0.8)

    add_node(nodes, "graphify_refresh_script", "scripts/generate_workspace_graph.py", "code", "scripts/generate_workspace_graph.py")
    add_node(nodes, "graphify_report", "graphify-out/GRAPH_REPORT.md", "document", "graphify-out/GRAPH_REPORT.md")
    add_node(nodes, "graphify_html", "graphify-out/graph.html", "document", "graphify-out/graph.html")
    add_node(nodes, "graphify_json", "graphify-out/graph.json", "document", "graphify-out/graph.json")
    add_edge(edges, "hub_graphify", "graphify_refresh_script", "uses", "EXTRACTED", "scripts/generate_workspace_graph.py")
    add_edge(edges, "graphify_refresh_script", "graphify_report", "produces", "EXTRACTED", "scripts/generate_workspace_graph.py")
    add_edge(edges, "graphify_refresh_script", "graphify_html", "produces", "EXTRACTED", "scripts/generate_workspace_graph.py")
    add_edge(edges, "graphify_refresh_script", "graphify_json", "produces", "EXTRACTED", "scripts/generate_workspace_graph.py")
    add_edge(edges, "graphify_report", "hub_docs", "supports_agent_navigation", "INFERRED", "docs/AGENT_START_HERE.md", 0.8)
    add_edge(edges, "graphify_html", "graphify_report", "renders", "EXTRACTED", "scripts/generate_workspace_graph.py")
    add_edge(edges, "graphify_json", "graphify_report", "backs", "EXTRACTED", "scripts/generate_workspace_graph.py")

    add_node(nodes, "hub_gateway_phrases", "Natural Language Gateway Phrases", "rationale", "docs/AGENT_OPERATION_MAP.md")
    add_edge(edges, "hub_docs", "hub_gateway_phrases", "documents", "EXTRACTED", "docs/AGENT_OPERATION_MAP.md")
    for gateway in NATURAL_LANGUAGE_GATEWAYS:
        alias_id = str(gateway["id"])
        add_node(nodes, alias_id, str(gateway["label"]), "rationale", "docs/AGENT_OPERATION_MAP.md")
        add_edge(edges, "hub_gateway_phrases", alias_id, "matches_user_phrase", "EXTRACTED", "docs/AGENT_OPERATION_MAP.md")
        for target_id in gateway["targets"]:
            if target_id in nodes:
                add_edge(edges, alias_id, target_id, "routes_to", "EXTRACTED", "docs/AGENT_OPERATION_MAP.md")

    communities = {
        0: ["workspace_doutorado", "hub_runtime"]
        + [n for n in nodes if n.startswith(("runtime_", "env_"))],
        1: ["hub_article_machine"] + [n for n in nodes if n.startswith("module_") or n.startswith("cli_")],
        2: ["hub_projects"] + [
            n
            for n in nodes
            if n.startswith("project_")
            or n.startswith("project_contract_")
            or n.startswith("project_artifact_")
            or n.startswith("lane_")
            or n.startswith("mode_")
            or n.startswith("type_")
            or n == "defect_nested_projects"
        ],
        3: ["hub_skills"] + [
            n
            for n in nodes
            if n.startswith("skill_")
            or n.startswith("skill_section_")
            or n.startswith("plugin_")
            or n.startswith("artifact_")
            or n.startswith("gate_")
        ],
        4: [
            "hub_docs",
            "nav_workspace_index",
        ]
        + [
            n
            for n in nodes
            if n.startswith("doc_")
            or n.startswith("doc_section_")
            or n.startswith("flow_")
            or n.startswith("alias_")
            or n.startswith("codex_")
            or n == "hub_gateway_phrases"
        ],
        5: ["hub_legacy"] + [n for n in nodes if n.startswith("legacy_")],
        6: ["hub_graphify"] + [n for n in nodes if n.startswith("graphify_") or n.startswith("tree_area_")],
        7: ["hub_git"] + [n for n in nodes if n.startswith("hygiene_")],
    }
    communities = {cid: [n for n in members if n in nodes] for cid, members in communities.items()}
    labels = {
        0: "Runtime Commands",
        1: "Article Machine",
        2: "Projects And Modes",
        3: "Scientific Skills",
        4: "Agent Docs",
        5: "Legacy Sources",
        6: "Graphify Map",
        7: "Git Hygiene",
    }
    manifest = {
        "root": str(ROOT),
        "project_count": len(project_dirs()),
        "critical_skill_count": sum(1 for s in CRITICAL_SKILLS if (skills_root / s / "SKILL.md").exists()),
        "legacy_dirs_present": [d for d in LEGACY_ROOT_DIRS if (ROOT / d).exists()],
        "query_alias_count": sum(1 for gateway in NATURAL_LANGUAGE_GATEWAYS if str(gateway["id"]) in nodes),
        "git_state": git_generation_state(),
        "detail_counts": detail_counts,
        "html_mode": {
            "layout": "fixed-community",
            "physics_default": False,
            "labels_default": "hubs-only",
            "intended_use": "fast agent navigation, search, and community focus",
        },
        "limitations": [
            "Operational graph only; full root semantic graph timed out and would mix caches, PDFs, and raw data.",
            "Edges marked INFERRED are navigation/risk inferences, not scientific evidence.",
            "Use project-specific graphify runs for manuscript evidence graphs.",
        ],
    }
    # This distribution omits historical projects and workspace documents.
    # Keep relationships only when both entities actually exist in this clone.
    present_edges = [edge for edge in edges if edge["source"] in nodes and edge["target"] in nodes]
    manifest["omitted_absent_endpoint_edges"] = len(edges) - len(present_edges)
    extraction = {"nodes": list(nodes.values()), "edges": present_edges, "hyperedges": [], "input_tokens": 0, "output_tokens": 0}
    return extraction, communities, labels, manifest


def _graphify_operational_id_map(graph: Any) -> dict[str, str]:
    canonical_by_operational_id: dict[str, str] = {}
    for canonical_id, attributes in graph.nodes(data=True):
        if not isinstance(canonical_id, str):
            raise ValueError(f"Graphify emitted a non-string node ID: {canonical_id!r}")
        operational_id = attributes.get("operational_id")
        if not isinstance(operational_id, str) or not operational_id:
            raise ValueError(
                f"Graphify node {canonical_id!r} is missing its stable operational_id"
            )
        previous = canonical_by_operational_id.get(operational_id)
        if previous is not None and previous != canonical_id:
            raise ValueError(
                "Graphify mapped one operational node to multiple canonical IDs: "
                f"{operational_id!r} -> {previous!r}, {canonical_id!r}"
            )
        canonical_by_operational_id[operational_id] = canonical_id
    return canonical_by_operational_id


def reconcile_graphify_communities(graph: Any, communities: dict[int, list[str]]) -> dict[int, list[str]]:
    """Map operational community members to Graphify's canonical node IDs.

    ``graphify.build.build_from_json`` canonicalizes IDs for non-AST nodes from
    their source paths. The external community mapping is not part of the
    extraction payload, so Graphify cannot update it at the same time. This
    function restores that contract through the stable ``operational_id`` node
    attribute and rejects incomplete, duplicate, or ambiguous memberships.
    """

    canonical_by_operational_id = _graphify_operational_id_map(graph)
    graph_node_ids = set(canonical_by_operational_id.values())

    community_by_operational_id: dict[str, int] = {}
    for community_id, members in communities.items():
        for operational_id in members:
            previous = community_by_operational_id.get(operational_id)
            if previous is not None:
                raise ValueError(
                    "Operational node belongs to multiple communities: "
                    f"{operational_id!r} -> {previous}, {community_id}"
                )
            community_by_operational_id[operational_id] = community_id

    expected_ids = set(community_by_operational_id)
    available_ids = set(canonical_by_operational_id)
    missing = sorted(expected_ids - available_ids)
    unassigned = sorted(available_ids - expected_ids)
    if missing or unassigned:
        raise ValueError(
            "Operational community contract does not match the Graphify graph: "
            f"missing={missing[:5]!r}, unassigned={unassigned[:5]!r}"
        )

    reconciled = {
        community_id: [canonical_by_operational_id[operational_id] for operational_id in members]
        for community_id, members in communities.items()
    }
    reconciled_node_ids = [node_id for members in reconciled.values() for node_id in members]
    if len(reconciled_node_ids) != len(set(reconciled_node_ids)):
        raise ValueError("Graphify canonicalization collapsed distinct operational community members")
    if set(reconciled_node_ids) != graph_node_ids:
        raise ValueError("Reconciled communities do not form an exact partition of the Graphify graph")
    return reconciled


def _build_graphify_graph_in_memory(extraction: dict[str, Any]) -> Any:
    """Build the Graphify graph without touching the generated graph artifacts."""

    from graphify.build import build_from_json

    return build_from_json(extraction)


def validate_operational_graph(workspace_root: Path | None = None) -> dict[str, Any]:
    """Validate the operational graph contract entirely in memory.

    This is deliberately separate from :func:`write_graph`: strict machine
    audits must detect a broken extraction, Graphify canonicalization, or
    community contract without refreshing files under ``graphify-out``.
    """

    requested_root = Path(workspace_root or ROOT).resolve()
    issues: list[str] = []
    checks: dict[str, Any] = {}
    if requested_root != ROOT.resolve():
        issues.append(
            "Operational graph validator is bound to "
            f"{str(ROOT)!r}, not requested workspace {str(requested_root)!r}."
        )

    try:
        extraction, communities, labels, _manifest = build_extraction()
        raw_nodes = extraction.get("nodes")
        raw_edges = extraction.get("edges")
        if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
            raise ValueError("Operational extraction must contain node and edge lists")

        node_ids = [node.get("id") for node in raw_nodes if isinstance(node, dict)]
        if len(node_ids) != len(raw_nodes) or any(not isinstance(node_id, str) or not node_id for node_id in node_ids):
            raise ValueError("Every operational node must have a non-empty string ID")
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Operational extraction contains duplicate node IDs")
        for node in raw_nodes:
            if node.get("operational_id") != node.get("id"):
                raise ValueError(f"Node {node.get('id')!r} lost its stable operational_id")
        checks["extraction_nodes"] = {"status": "pass", "count": len(node_ids)}

        node_id_set = set(node_ids)
        invalid_edges = [
            edge
            for edge in raw_edges
            if not isinstance(edge, dict)
            or edge.get("source") not in node_id_set
            or edge.get("target") not in node_id_set
        ]
        if invalid_edges:
            raise ValueError(f"Operational extraction has {len(invalid_edges)} edge(s) with unknown endpoints")
        checks["edge_endpoints"] = {"status": "pass", "count": len(raw_edges)}

        members = [member for community in communities.values() for member in community]
        if len(members) != len(set(members)) or set(members) != node_id_set:
            raise ValueError("Operational communities must form an exact partition of extraction node IDs")
        if set(communities) != set(labels):
            raise ValueError("Every operational community must have exactly one label")
        checks["operational_communities"] = {"status": "pass", "count": len(communities)}

        graph = _build_graphify_graph_in_memory(extraction)
        reconciled = reconcile_graphify_communities(graph, communities)
        canonical_ids = _graphify_operational_id_map(graph)
        if len(canonical_ids) != len(node_ids):
            raise ValueError("Graphify node count differs from the operational extraction")
        checks["graphify_build"] = {
            "status": "pass",
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
        }
        checks["graphify_id_community_reconciliation"] = {
            "status": "pass",
            "operational_ids": len(canonical_ids),
            "canonical_ids": len(set(canonical_ids.values())),
            "communities": len(reconciled),
        }
    except Exception as exc:
        issues.append(f"operational graph validation failed: {exc}")

    return {
        "contract": "OperationalGraphAuditReport",
        "status": "pass" if not issues else "block",
        "workspace_root": str(requested_root),
        "read_only": True,
        "checks": checks,
        "issues": issues,
    }


def _community_lookup(communities: dict[int, list[str]]) -> dict[str, int]:
    lookup: dict[str, int] = {}
    for community_id, members in communities.items():
        for member in members:
            lookup[member] = community_id
    return lookup


def _fixed_positions(graph: Any, communities: dict[int, list[str]]) -> dict[str, dict[str, float]]:
    positions: dict[str, dict[str, float]] = {}
    ordered_communities = [(cid, [n for n in members if n in graph]) for cid, members in sorted(communities.items())]
    ordered_communities = [(cid, members) for cid, members in ordered_communities if members]
    if not ordered_communities:
        return positions

    outer_radius = max(520.0, 150.0 * len(ordered_communities))
    for community_index, (_community_id, members) in enumerate(ordered_communities):
        angle = (2.0 * math.pi * community_index / len(ordered_communities)) - (math.pi / 2.0)
        center_x = outer_radius * math.cos(angle)
        center_y = outer_radius * math.sin(angle)

        def member_key(node_id: str) -> tuple[int, int, str]:
            degree = graph.degree(node_id)
            is_hub = node_id.startswith("hub_") or node_id == "workspace_doutorado"
            return (0 if is_hub else 1, -degree, str(graph.nodes[node_id].get("label", node_id)).lower())

        ordered_members = sorted(members, key=member_key)
        if len(ordered_members) == 1:
            positions[ordered_members[0]] = {"x": center_x, "y": center_y}
            continue

        local_radius = max(95.0, 32.0 * math.sqrt(len(ordered_members)))
        for member_index, node_id in enumerate(ordered_members):
            if member_index == 0:
                positions[node_id] = {"x": center_x, "y": center_y}
                continue
            local_angle = 2.0 * math.pi * (member_index - 1) / max(1, len(ordered_members) - 1)
            radius_adjustment = 0.82 + (0.12 * (member_index % 3))
            positions[node_id] = {
                "x": center_x + local_radius * radius_adjustment * math.cos(local_angle),
                "y": center_y + local_radius * radius_adjustment * math.sin(local_angle),
            }
    return positions


def write_fluid_html(graph: Any, communities: dict[int, list[str]], labels: dict[int, str], output_path: Path) -> None:
    community_by_node = _community_lookup(communities)
    positions = _fixed_positions(graph, communities)
    max_degree = max((graph.degree(node_id) for node_id in graph.nodes), default=1)

    node_payload: list[dict[str, Any]] = []
    for node_id, data in graph.nodes(data=True):
        community_id = int(community_by_node.get(node_id, data.get("community", 0) or 0))
        label = str(data.get("label", node_id))
        degree = int(graph.degree(node_id))
        is_hub = node_id.startswith("hub_") or node_id == "workspace_doutorado" or degree >= 12
        position = positions.get(node_id, {"x": 0.0, "y": 0.0})
        color = COMMUNITY_COLORS[community_id % len(COMMUNITY_COLORS)]
        node_payload.append(
            {
                "id": node_id,
                "label": label if is_hub else "",
                "baseLabel": label if is_hub else "",
                "fullLabel": label,
                "title": label,
                "community": community_id,
                "communityLabel": labels.get(community_id, f"Community {community_id}"),
                "degree": degree,
                "sourceFile": data.get("source_file") or "",
                "fileType": data.get("file_type") or "",
                "x": round(float(position["x"]), 2),
                "y": round(float(position["y"]), 2),
                "fixed": True,
                "size": round(10 + 20 * math.sqrt(degree / max_degree), 2),
                "color": {
                    "background": color,
                    "border": "#f4f4f5" if is_hub else color,
                    "highlight": {"background": "#ffffff", "border": color},
                },
                "font": {"color": "#f8fafc", "size": 13 if is_hub else 11, "strokeWidth": 4, "strokeColor": "#111827"},
            }
        )

    edge_payload: list[dict[str, Any]] = []
    for index, (source, target, data) in enumerate(graph.edges(data=True)):
        relation = str(data.get("relation", "related_to"))
        confidence = str(data.get("confidence", "EXTRACTED"))
        edge_payload.append(
            {
                "id": f"e{index}",
                "from": source,
                "to": target,
                "label": "",
                "title": f"{relation} [{confidence}]",
                "relation": relation,
                "confidence": confidence,
                "color": {"color": "rgba(148, 163, 184, 0.34)", "highlight": "#f8fafc"},
                "width": 2 if confidence == "EXTRACTED" else 1,
            }
        )

    community_payload = [
        {
            "id": cid,
            "label": labels.get(cid, f"Community {cid}"),
            "count": len([node_id for node_id in members if node_id in graph]),
            "color": COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)],
        }
        for cid, members in sorted(communities.items())
    ]
    stats = {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "communities": len(community_payload),
        "layout": "fixed-community",
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Doutorado Operational Graph</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; height: 100vh; overflow: hidden; background: #111827; color: #f8fafc; font-family: Arial, Helvetica, sans-serif; }}
  #app {{ display: grid; grid-template-columns: minmax(0, 1fr) 320px; height: 100vh; }}
  #graph {{ min-width: 0; height: 100vh; }}
  #panel {{ border-left: 1px solid #334155; background: #0f172a; display: flex; flex-direction: column; min-width: 0; }}
  #toolbar {{ display: grid; gap: 8px; padding: 12px; border-bottom: 1px solid #334155; }}
  #search, #community {{ width: 100%; border: 1px solid #475569; background: #111827; color: #f8fafc; border-radius: 6px; padding: 8px 10px; font-size: 13px; outline: none; }}
  #search:focus, #community:focus {{ border-color: #93c5fd; }}
  .buttons {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }}
  button {{ border: 1px solid #475569; background: #1f2937; color: #f8fafc; border-radius: 6px; padding: 7px 8px; font-size: 12px; cursor: pointer; }}
  button:hover {{ background: #273449; }}
  #results {{ max-height: 190px; overflow-y: auto; border-bottom: 1px solid #334155; display: none; }}
  .result {{ padding: 7px 12px; cursor: pointer; border-left: 3px solid transparent; font-size: 12px; line-height: 1.3; }}
  .result:hover {{ background: #1f2937; border-left-color: #93c5fd; }}
  .muted {{ color: #94a3b8; }}
  #details {{ padding: 13px; border-bottom: 1px solid #334155; min-height: 178px; font-size: 13px; line-height: 1.45; }}
  #details h2 {{ margin: 0 0 8px; font-size: 14px; line-height: 1.25; }}
  #details .row {{ margin: 5px 0; overflow-wrap: anywhere; }}
  #legend {{ overflow-y: auto; padding: 10px 12px; flex: 1; }}
  .legend-item {{ display: flex; align-items: center; gap: 8px; padding: 6px 0; font-size: 12px; cursor: pointer; }}
  .legend-item:hover {{ color: #bfdbfe; }}
  .dot {{ width: 11px; height: 11px; border-radius: 999px; flex: 0 0 auto; }}
  .count {{ margin-left: auto; color: #64748b; }}
  #stats {{ border-top: 1px solid #334155; padding: 10px 12px; color: #94a3b8; font-size: 11px; line-height: 1.4; }}
  @media (max-width: 900px) {{
    #app {{ grid-template-columns: 1fr; grid-template-rows: minmax(0, 1fr) 310px; }}
    #panel {{ border-left: 0; border-top: 1px solid #334155; }}
    #graph {{ height: calc(100vh - 310px); }}
  }}
</style>
</head>
<body>
<div id="app">
  <div id="graph"></div>
  <aside id="panel">
    <div id="toolbar">
      <input id="search" placeholder="Search node or file" autocomplete="off">
      <select id="community">
        <option value="all">All communities</option>
      </select>
      <div class="buttons">
        <button id="fit">Fit</button>
        <button id="labels">Labels</button>
        <button id="physics">Physics</button>
      </div>
    </div>
    <div id="results"></div>
    <div id="details"><h2>Select a node</h2><div class="muted">Use search, a community filter, or click in the graph.</div></div>
    <div id="legend"></div>
    <div id="stats"></div>
  </aside>
</div>
<script>
const RAW_NODES = {json.dumps(node_payload, ensure_ascii=False)};
const RAW_EDGES = {json.dumps(edge_payload, ensure_ascii=False)};
const COMMUNITIES = {json.dumps(community_payload, ensure_ascii=False)};
const STATS = {json.dumps(stats, ensure_ascii=False)};

let labelsVisible = false;
let currentCommunity = "all";
const nodes = new vis.DataSet([]);
const edges = new vis.DataSet([]);
const container = document.getElementById("graph");
const network = new vis.Network(container, {{ nodes, edges }}, {{
  autoResize: true,
  layout: {{ improvedLayout: false }},
  physics: {{ enabled: false }},
  interaction: {{ hover: true, tooltipDelay: 80, hideEdgesOnDrag: true, hideNodesOnDrag: false, navigationButtons: true, keyboard: true }},
  nodes: {{ shape: "dot", borderWidth: 1, chosen: true }},
  edges: {{ smooth: false, selectionWidth: 2, arrows: {{ to: {{ enabled: false }} }} }},
}});

function escapeHtml(value) {{
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }}[char]));
}}

function visibleNode(raw) {{
  return currentCommunity === "all" || String(raw.community) === currentCommunity;
}}

function materializeNode(raw) {{
  return {{ ...raw, label: labelsVisible ? raw.fullLabel : raw.baseLabel }};
}}

function applyFilter() {{
  const allowed = new Set(RAW_NODES.filter(visibleNode).map((node) => node.id));
  nodes.clear();
  edges.clear();
  nodes.add(RAW_NODES.filter(visibleNode).map(materializeNode));
  edges.add(RAW_EDGES.filter((edge) => allowed.has(edge.from) && allowed.has(edge.to)));
  requestAnimationFrame(() => network.fit({{ animation: {{ duration: 250, easingFunction: "easeInOutQuad" }} }}));
  updateStats();
}}

function nodeById(id) {{
  return RAW_NODES.find((node) => node.id === id);
}}

function adjacentEdges(id) {{
  return RAW_EDGES.filter((edge) => edge.from === id || edge.to === id);
}}

function focusNode(id) {{
  const raw = nodeById(id);
  if (!raw) return;
  if (!nodes.get(id)) {{
    currentCommunity = "all";
    document.getElementById("community").value = "all";
    applyFilter();
  }}
  network.selectNodes([id]);
  network.focus(id, {{ scale: 1.35, animation: {{ duration: 300, easingFunction: "easeInOutQuad" }} }});
  showDetails(id);
}}

function showDetails(id) {{
  const raw = nodeById(id);
  const panel = document.getElementById("details");
  if (!raw) {{
    panel.innerHTML = '<h2>Select a node</h2><div class="muted">Use search, a community filter, or click in the graph.</div>';
    return;
  }}
  const related = adjacentEdges(id).slice(0, 10).map((edge) => {{
    const other = edge.from === id ? edge.to : edge.from;
    const otherNode = nodeById(other);
    return `<div class="row muted">${{escapeHtml(edge.relation)}} -> <button onclick="focusNode('${{escapeHtml(other)}}')">${{escapeHtml(otherNode ? otherNode.fullLabel : other)}}</button></div>`;
  }}).join("");
  panel.innerHTML = `
    <h2>${{escapeHtml(raw.fullLabel)}}</h2>
    <div class="row"><span class="muted">Community:</span> ${{escapeHtml(raw.communityLabel)}}</div>
    <div class="row"><span class="muted">Source:</span> ${{escapeHtml(raw.sourceFile || "n/a")}}</div>
    <div class="row"><span class="muted">Type:</span> ${{escapeHtml(raw.fileType || "n/a")}}</div>
    <div class="row"><span class="muted">Degree:</span> ${{raw.degree}}</div>
    <div class="row"><span class="muted">Neighbors:</span></div>
    ${{related || '<div class="muted">No visible neighbors.</div>'}}
  `;
}}

function updateStats() {{
  document.getElementById("stats").textContent =
    `${{nodes.length}}/${{STATS.nodes}} nodes, ${{edges.length}}/${{STATS.edges}} edges, ${{STATS.communities}} communities. Layout: ${{STATS.layout}}, physics off by default.`;
}}

function search() {{
  const query = document.getElementById("search").value.trim().toLowerCase();
  const resultBox = document.getElementById("results");
  if (!query) {{
    resultBox.style.display = "none";
    resultBox.innerHTML = "";
    return;
  }}
  const hits = RAW_NODES.filter((node) =>
    node.fullLabel.toLowerCase().includes(query) ||
    node.id.toLowerCase().includes(query) ||
    String(node.sourceFile).toLowerCase().includes(query)
  ).slice(0, 18);
  resultBox.innerHTML = hits.map((node) =>
    `<div class="result" onclick="focusNode('${{escapeHtml(node.id)}}')">${{escapeHtml(node.fullLabel)}}<br><span class="muted">${{escapeHtml(node.communityLabel)}}</span></div>`
  ).join("") || '<div class="result muted">No matches</div>';
  resultBox.style.display = "block";
}}

document.getElementById("search").addEventListener("input", search);
document.getElementById("fit").addEventListener("click", () => network.fit({{ animation: {{ duration: 250, easingFunction: "easeInOutQuad" }} }}));
document.getElementById("labels").addEventListener("click", () => {{
  labelsVisible = !labelsVisible;
  nodes.update(RAW_NODES.filter(visibleNode).map(materializeNode));
}});
document.getElementById("physics").addEventListener("click", () => {{
  network.setOptions({{ physics: {{ enabled: true, solver: "forceAtlas2Based", stabilization: {{ iterations: 40, fit: false }} }} }});
  setTimeout(() => network.setOptions({{ physics: {{ enabled: false }} }}), 1800);
}});
network.on("selectNode", (event) => showDetails(event.nodes[0]));

const communitySelect = document.getElementById("community");
COMMUNITIES.forEach((community) => {{
  const option = document.createElement("option");
  option.value = String(community.id);
  option.textContent = `${{community.label}} (${{community.count}})`;
  communitySelect.appendChild(option);
}});
communitySelect.addEventListener("change", (event) => {{
  currentCommunity = event.target.value;
  applyFilter();
}});

const legend = document.getElementById("legend");
legend.innerHTML = COMMUNITIES.map((community) =>
  `<div class="legend-item" onclick="communitySelect.value='${{community.id}}'; currentCommunity='${{community.id}}'; applyFilter();">
    <span class="dot" style="background:${{community.color}}"></span>
    <span>${{escapeHtml(community.label)}}</span>
    <span class="count">${{community.count}}</span>
  </div>`
).join("");

applyFilter();
</script>
</body>
</html>
"""
    write_utf8_lf(output_path, html)


def write_graph() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    extraction, communities, labels, manifest = build_extraction()
    write_utf8_lf(OUT / ".graphify_python", sys.executable)
    write_utf8_lf(OUT / ".graphify_root", str(ROOT))
    write_utf8_lf(OUT / ".graphify_extract.json", json.dumps(extraction, ensure_ascii=False, indent=2))
    write_utf8_lf(OUT / "workspace_graph_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    from graphify.analyze import god_nodes, suggest_questions, surprising_connections
    from graphify.build import build_from_json
    from graphify.cluster import score_all
    from graphify.export import to_json
    from graphify.report import generate

    graph = build_from_json(extraction)
    communities = reconcile_graphify_communities(graph, communities)
    canonical_node_ids = _graphify_operational_id_map(graph)
    cohesion = score_all(graph, communities)
    questions = [
        {
            "question": "How should a new agent choose an active Article Machine project?",
            "why": "Connects runtime commands, project modes, and required project files.",
        },
        {
            "question": "Which parts of the workspace are hygiene risks before committing?",
            "why": "Highlights untracked/generated areas, legacy folders, and nested projects.",
        },
        {
            "question": "How do Graphify and Article Machine runtimes differ in this checkout?",
            "why": "Shows the reproducible venv runtimes and the diagnosed global Graphify fallback.",
        },
        {
            "question": "How should GPT-6.1 Sol medium and GPT-6 Luna coordinate bilingual scientific work?",
            "why": "Routes model orchestration to the project-scoped Codex roles, strict audit, and benchmark gate.",
        },
        {
            "question": "Which skills are mandatory before strong scientific claims?",
            "why": "Bridges critical scientific skills to the Article Machine gates.",
        },
        {
            "question": "When should a user request route to Zotero, Life Science Research, NGS, or deep-thinking gates?",
            "why": "Shows plugin gateways, expected project artifacts, and the local routing surface.",
        },
    ]
    detection = {
        "total_files": manifest["project_count"]
        + manifest["critical_skill_count"]
        + len(manifest["legacy_dirs_present"])
        + len(DETAILED_DOCS)
        + sum(manifest["detail_counts"].values()),
        "total_words": 0,
        "warning": "Root semantic graph was not run: the workspace is too broad and detection timed out. This is an operational navigation graph.",
    }
    report = generate(
        graph,
        communities,
        cohesion,
        labels,
        god_nodes(graph),
        surprising_connections(graph, communities),
        detection,
        {"input": 0, "output": 0},
        str(ROOT),
        suggested_questions=questions,
    )
    report = report.replace(
        "\n\n## Corpus Check",
        "\n\n> **Start here:** [`graphify-out/LEIA-ME.md`](LEIA-ME.md) maps every "
        "generated file.\n> The agent quickstart and query recipes are at the end "
        "of this report.\n\n## Corpus Check",
        1,
    )
    report += "\n\n## Agent Operating Flow\n"
    for index, (_flow_id, label) in enumerate(AGENT_FLOW_STEPS, start=1):
        report += f"{index}. {label}\n"
    report += "\n## Agent Quickstart By Intent\n"
    for intent, entry in (
        (
            "Open the operational graph",
            "graphify-out/LEIA-ME.md -> graphify-out/GRAPH_REPORT.md -> graphify-out/graph.html",
        ),
        (
            "New agent entering the workspace",
            "docs/INDICE_DO_WORKSPACE.md -> docs/AGENT_START_HERE.md -> .agents/AGENTS.md",
        ),
        ("Choose or resume a project", "docs/ESTADO_DOS_PROJETOS.md -> projects/<project_id>/project.yaml"),
        ("Restore an environment", "docs/AMBIENTES_E_LOCKS.md -> uv.lock or renv.lock"),
        ("Organize or clean without deleting", "docs/ORGANIZACAO_E_LIMPEZA.md"),
        ("Check Git or worktrees", "docs/GIT_E_WORKTREES.md"),
        ("Migrate or audit the C: legacy", "docs/MIGRACAO_PARA_D_STATUS.md -> archive/legado_C_2026-11/LEIA-ME.md"),
        ("Claim something as ready", "evidence/claim_map.jsonl -> Review Trinity"),
    ):
        report += f"- **{intent}**: {entry}\n"
    report += "\n## Agent Query Recipes\n"
    report += "- `graphify query \"onde esta o painel de projetos\" --budget 1200`\n"
    report += "- `graphify query \"como restaurar o ambiente R\" --budget 1200`\n"
    report += "- `graphify query \"como organizar sem excluir conteudo bruto\" --budget 1200`\n"
    report += "- `graphify query \"qual projeto esta no modo analysis\" --budget 1200`\n"
    report += "\n## Plugin Gateway Map\n"
    for skill_name, bridge in GATEWAY_BRIDGES.items():
        if (ROOT / "skills" / skill_name / "SKILL.md").exists():
            report += f"- `{skill_name}` -> {bridge['target_label']} -> {bridge['artifact_label']}\n"
    report += "\n## Installed Navigation Skills\n"
    for skill_name in NAVIGATION_SKILLS:
        if (ROOT / "skills" / skill_name / "SKILL.md").exists():
            report += f"- `{skill_name}` -> `skills/{skill_name}/SKILL.md`\n"
    report += "\n## Detailed Navigation Layers\n"
    report += f"- Markdown sections indexed: {manifest['detail_counts']['doc_sections']}\n"
    report += f"- Project contract files indexed: {manifest['detail_counts']['project_contracts']}\n"
    report += f"- Project artifact areas indexed: {manifest['detail_counts']['project_artifact_areas']}\n"
    report += f"- Skill instruction sections indexed: {manifest['detail_counts']['skill_sections']}\n"
    report += f"- Navigation/preservation skills installed: {manifest['detail_counts']['navigation_skills']}\n"
    report += f"- Project-scoped Codex agent roles indexed: {manifest['detail_counts']['codex_agents']}\n"
    report += f"- Read-only Codex benchmark profiles indexed: {manifest['detail_counts']['codex_profiles']}\n"
    report += "\n## Generation Provenance\n"
    git_state = manifest["git_state"]
    if git_state["available"]:
        report += f"- Git HEAD: `{git_state['head_commit']}`\n"
        report += f"- Dirty worktree at generation: `{str(git_state['worktree_dirty']).lower()}`\n"
        report += f"- Porcelain status entries at generation: {git_state['status_entry_count']}\n"
    else:
        report += "- Git provenance unavailable; do not treat this graph as clean-checkout evidence.\n"
    report += "\n## Natural Language Gateway Phrases\n"
    report += "These nodes make Portuguese and operational user phrasing easier for `graphify query` to match.\n"
    for gateway in NATURAL_LANGUAGE_GATEWAYS:
        alias_id = str(gateway["id"])
        if alias_id not in canonical_node_ids:
            continue
        targets = [
            str(graph.nodes[canonical_node_ids[target_id]].get("label", target_id))
            for target_id in gateway["targets"]
            if target_id in canonical_node_ids
        ]
        report += f"- `{gateway['label']}` -> {', '.join(targets)}\n"
    report += "\n## Legacy And Hygiene Map\n"
    if manifest["legacy_dirs_present"]:
        report += "Legacy folders requiring manual triage before moves or staging:\n"
        for dirname in manifest["legacy_dirs_present"]:
            report += f"- `{dirname}/`\n"
    report += "\nGit hygiene targets:\n"
    for dirname, label in HYGIENE_TARGETS.items():
        if (ROOT / dirname).exists():
            report += f"- `{dirname}/`: {label}\n"
    report += "\n\n## Operational Limitations\n"
    for item in manifest["limitations"]:
        report += f"- {item}\n"
    report += "\n## Graph HTML Fluidity\n"
    report += "- `graph.html` uses a fixed community layout with physics off by default, so pan/zoom/search stays responsive.\n"
    report += "- Non-hub labels are hidden by default; use the Labels toggle when inspecting a focused area.\n"
    report += "- Community filtering is intentional: agents should narrow to the active operating layer instead of scanning every node at once.\n"
    to_json(graph, communities, str(OUT / "graph.json"))
    normalize_utf8_lf(OUT / "graph.json")
    write_fluid_html(graph, communities, labels, OUT / "graph.html")
    write_utf8_lf(OUT / "GRAPH_REPORT.md", report)
    print(json.dumps({"status": "written", "nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    write_graph()
