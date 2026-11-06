from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from .projects import load_project
from .serialization import save_structured_file
from .services.plugins import resolve_scientific_plugin


PLUGIN_NAME = "life-science-research"
DEFAULT_PLUGIN_CACHE = Path.home() / ".codex" / "plugins" / "cache" / "openai-curated" / PLUGIN_NAME


@dataclass(frozen=True)
class Lane:
    name: str
    triggers: tuple[str, ...]
    skills: tuple[str, ...]
    objective: str


LANES: tuple[Lane, ...] = (
    Lane(
        name="target-disease-evidence",
        triggers=("target", "disease", "therapeutic", "gene", "protein", "crohn", "ibd", "inflammation", "pathway"),
        skills=(
            "opentargets-skill",
            "uniprot-skill",
            "human-protein-atlas-skill",
            "reactome-skill",
            "string-skill",
        ),
        objective="Prioritize target-disease evidence, tissue context, pathways, and network support.",
    ),
    Lane(
        name="chemistry-pharmacology",
        triggers=("drug", "compound", "molecule", "ligand", "inhibitor", "binding", "activity", "small-molecule", "pharmacology"),
        skills=(
            "chembl-skill",
            "bindingdb-skill",
            "pubchem-pug-skill",
            "chebi-skill",
            "pharmgkb-skill",
        ),
        objective="Collect molecule, activity, binding, mechanism, and pharmacogenomic evidence.",
    ),
    Lane(
        name="genetics-variant-interpretation",
        triggers=("variant", "rs", "snp", "clinvar", "gnomad", "gwas", "phewas", "eqtl", "locus"),
        skills=(
            "clinvar-variation-skill",
            "gnomad-graphql-skill",
            "gwas-catalog-skill",
            "gtex-eqtl-skill",
            "finngen-phewas-skill",
            "ukb-topmed-phewas-skill",
            "biobankjapan-phewas-skill",
        ),
        objective="Interpret variant, frequency, association, PheWAS, and eQTL evidence with cohort caveats.",
    ),
    Lane(
        name="protein-structure-mechanism",
        triggers=("structure", "alphafold", "pdb", "domain", "binding pocket", "protein structure", "mechanism"),
        skills=("alphafold-skill", "rcsb-pdb-skill", "uniprot-skill", "reactome-skill"),
        objective="Assess structure, domains, experimentally solved structures, and mechanism hypotheses.",
    ),
    Lane(
        name="omics-datasets",
        triggers=("dataset", "omics", "single-cell", "scrna", "rnaseq", "expression", "proteomics", "metabolomics", "cell"),
        skills=(
            "cellxgene-skill",
            "encode-skill",
            "biostudies-arrayexpress-skill",
            "pride-skill",
            "proteomexchange-skill",
            "metabolights-skill",
            "bgee-skill",
        ),
        objective="Discover public expression, single-cell, proteomics, metabolomics, and functional genomics datasets.",
    ),
    Lane(
        name="microbiome-metabolite-context",
        triggers=("gut", "intestinal", "intestine", "microbiome", "microbiota", "metabolite", "metabolic"),
        skills=("mgnify-skill", "hmdb-skill", "metabolights-skill", "rhea-skill", "bgee-skill", "cellxgene-skill"),
        objective="Collect microbiome, metabolite, reaction, and gut tissue/cell context for in silico models.",
    ),
    Lane(
        name="clinical-translational-evidence",
        triggers=("clinical", "trial", "recruiting", "cancer", "oncology", "therapy", "patient", "translational"),
        skills=("clinicaltrials-skill", "opentargets-skill", "cbioportal-skill", "civic-skill", "pharmgkb-skill"),
        objective="Check clinical trial, translational, oncology, and pharmacogenomic evidence.",
    ),
    Lane(
        name="literature-dataset-discovery",
        triggers=("literature", "pubmed", "pmc", "preprint", "biorxiv", "medrxiv", "article", "paper", "review"),
        skills=("ncbi-entrez-skill", "ncbi-pmc-skill", "biorxiv-skill", "ncbi-datasets-skill"),
        objective="Find literature, open full text, preprints, and public datasets that can support evidence mapping.",
    ),
)


def _discover_plugin_root() -> Path | None:
    try:
        return resolve_scientific_plugin(PLUGIN_NAME)
    except (OSError, ValueError):
        return None


def _parse_skill_frontmatter(skill_path: Path) -> dict[str, Any]:
    text = skill_path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            payload: dict[str, str] = {}
            for line in parts[1].splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                key = key.strip()
                if key in {"name", "description"}:
                    payload[key] = value.strip().strip('"').strip("'")
            if payload:
                return payload
    name = skill_path.parent.name
    description = ""
    for line in text.splitlines()[:20]:
        if line.startswith("description:"):
            description = line.split(":", 1)[1].strip()
            break
    return {"name": name, "description": description}


def catalog_life_science_skills(plugin_root: Path | None = None) -> dict:
    root = Path(plugin_root) if plugin_root else _discover_plugin_root()
    if root is None or not (root / "skills").exists():
        return {
            "status": "missing",
            "plugin": {"name": PLUGIN_NAME, "path": str(root) if root else None},
            "skills": {},
            "message": "Life Science Research plugin was not found in the local Codex plugin cache.",
        }

    skills: dict[str, dict] = {}
    for skill_md in sorted((root / "skills").glob("*/SKILL.md")):
        meta = _parse_skill_frontmatter(skill_md)
        name = str(meta.get("name") or skill_md.parent.name)
        skills[name] = {
            "name": name,
            "description": str(meta.get("description") or ""),
            "skill_dir": str(skill_md.parent),
            "skill_file": str(skill_md),
        }

    return {
        "status": "available",
        "plugin": {"name": PLUGIN_NAME, "path": str(root)},
        "skills": skills,
        "skill_count": len(skills),
    }


def _normalize_question(question: str) -> str:
    from .agent_skills import _normalize_text

    return re.sub(r"\s+", " ", _normalize_text(question or "").strip())


def _lane_matches(question: str, lane: Lane) -> list[str]:
    matches: list[str] = []
    for trigger in lane.triggers:
        pattern = re.escape(trigger.lower()).replace("\\ ", r"\s+")
        if re.search(rf"\b{pattern}\b", question):
            matches.append(trigger)
    portuguese = {
        "target-disease-evidence": ("alvo", "alvos", "doenca", "inflamacao", "proteina", "via biologica"),
        "chemistry-pharmacology": ("farmaco", "farmacos", "composto", "compostos", "molecula", "ligante", "farmacologia"),
        "genetics-variant-interpretation": ("variante", "variantes", "ancestralidade", "frequencia alelica"),
        "protein-structure-mechanism": ("estrutura proteica", "mecanismo", "dominio"),
        "omics-datasets": ("dados publicos", "expressao", "proteomica", "metabolomica", "celula"),
        "microbiome-metabolite-context": ("intestino", "microbiota", "metabolito"),
        "clinical-translational-evidence": ("ensaio clinico", "ensaios clinicos", "paciente", "oncologia", "translacional"),
        "literature-dataset-discovery": ("literatura", "artigo", "artigos", "revisao"),
    }
    from .agent_skills import _trigger_matches

    matches.extend(trigger for trigger in portuguese.get(lane.name, ()) if _trigger_matches(question, trigger))
    return matches


def route_life_science_lanes(question: str, project_type: str = "") -> list[dict]:
    normalized = _normalize_question(question)
    project_type_normalized = (project_type or "").lower()
    routed: list[dict] = []
    for lane in LANES:
        matches = _lane_matches(normalized, lane)
        if project_type_normalized == "drug-discovery" and lane.name in {"target-disease-evidence", "chemistry-pharmacology"}:
            matches.append("project-type:drug-discovery")
        if project_type_normalized == "intestinal-digital-twin" and lane.name in {"microbiome-metabolite-context", "omics-datasets"}:
            matches.append("project-type:intestinal-digital-twin")
        if matches:
            routed.append(
                {
                    "name": lane.name,
                    "objective": lane.objective,
                    "matched_triggers": sorted(set(matches)),
                    "skills": list(lane.skills),
                }
            )

    if not routed:
        routed.append(
            {
                "name": "literature-dataset-discovery",
                "objective": "Start with literature and dataset discovery because no specialized biomedical lane matched confidently.",
                "matched_triggers": ["fallback"],
                "skills": ["ncbi-entrez-skill", "ncbi-pmc-skill", "biorxiv-skill", "ncbi-datasets-skill"],
            }
        )

    return routed[:4]


def _selected_skills(lanes: list[dict], catalog: dict) -> list[dict]:
    catalog_skills = catalog.get("skills", {})
    selected: list[dict] = []
    seen: set[str] = set()
    for lane in lanes:
        for skill_name in lane["skills"]:
            if skill_name in seen:
                continue
            seen.add(skill_name)
            skill = catalog_skills.get(skill_name, {})
            selected.append(
                {
                    "name": skill_name,
                    "lane": lane["name"],
                    "description": skill.get("description", ""),
                    "skill_file": skill.get("skill_file", ""),
                    "reason": lane["objective"],
                }
            )
    return selected


def _write_agent_packet(project_dir: Path, plan: dict) -> Path:
    packet_path = project_dir / "context" / "life_science" / "agent_retrieval_packet.md"
    lines = [
        "# Life Science Retrieval Packet",
        "",
        f"Question: {plan['question']}",
        "",
        "## Lanes",
    ]
    for lane in plan["lane_details"]:
        lines.append(f"- {lane['name']}: {lane['objective']}")
    lines.extend(["", "## Selected Skills"])
    for skill in plan["selected_skills"]:
        file_label = f" ({skill['skill_file']})" if skill.get("skill_file") else ""
        lines.append(f"- {skill['name']}{file_label}: {skill['reason']}")
    lines.extend(
        [
            "",
            "## Evidence Rules",
            "- Save raw or summarized outputs under `evidence/life_science/` before using them in manuscript, discovery, deck, or poster claims.",
            "- Structured database evidence is hypothesis-generating until validated by protocol, statistics, experiments, or clinical evidence.",
            "- Add any factual output to `evidence/claim_map.jsonl` before drafting or dissemination.",
        ]
    )
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return packet_path


def plan_life_science_retrieval(project_dir: Path, question: str, plugin_root: Path | None = None) -> dict:
    project_dir = Path(project_dir)
    project = load_project(project_dir)
    catalog = catalog_life_science_skills(plugin_root)
    lanes = route_life_science_lanes(question, project.get("project_type", ""))
    selected = _selected_skills(lanes, catalog)
    lane_names = [lane["name"] for lane in lanes]
    plan = {
        "schema_version": 1,
        "status": "planned",
        "question": question,
        "project": {
            "id": project.get("id"),
            "name": project.get("name"),
            "project_type": project.get("project_type"),
            "lane": project.get("lane"),
        },
        "plugin": catalog.get("plugin", {}),
        "lanes": lane_names,
        "lane_details": lanes,
        "selected_skills": selected,
        "queries": [
            {
                "lane": lane["name"],
                "objective": lane["objective"],
                "skills": lane["skills"],
                "query_seed": question,
                "output_dir": "evidence/life_science",
            }
            for lane in lanes
        ],
        "evidence_policy": {
            "label": "hypothesis-generating-until-validated",
            "claim_lock_required": True,
            "raw_outputs_dir": "evidence/life_science",
            "citation_rule": "No database-derived claim may enter a manuscript or deliverable until mapped into evidence/claim_map.jsonl.",
        },
        "agent_notes": [
            "Use Life Science Research skills as retrieval/orchestration helpers, not as final proof.",
            "Prefer narrow database queries and save raw outputs when a result may support a claim.",
            "State cohort, ancestry, assay, tissue, and study-design limitations when relevant.",
        ],
    }

    plan_path = project_dir / "context" / "life_science" / "retrieval_plan.yaml"
    evidence_readme = project_dir / "evidence" / "life_science" / "README.md"
    save_structured_file(plan_path, plan)
    packet_path = _write_agent_packet(project_dir, plan)
    evidence_readme.parent.mkdir(parents=True, exist_ok=True)
    evidence_readme.write_text(
        "# Life Science Evidence\n\n"
        "Store raw outputs, compact summaries, and source metadata from Life Science Research skills here. "
        "Promote only checked findings into `evidence/claim_map.jsonl`.\n",
        encoding="utf-8",
    )
    return {
        "status": "planned",
        "project_dir": str(project_dir),
        "plan_path": str(plan_path),
        "agent_packet": str(packet_path),
        "lanes": lane_names,
        "selected_skills": selected,
        "plugin_status": catalog.get("status"),
    }
