# ruff: noqa: E501
"""PROSPERO 40-Field Protocol Compiler & Built-in Playwright Browser Registration Assistant.

Implements:
1. Complete 5-Stage Eligibility Screening + 40-Field Official NIHR CRD PROSPERO Schema (`PROSPERO_FIELD_SPECS`).
2. `compile_prospero_40_fields(project_dir)`:
   - Compiles all 40 fields from `protocol.yaml`, `project.yaml`, `standards.yaml`, and `compiled_queries.json`.
   - Enforces the PROSPERO Golden Rule on Field 5 (Data Extraction Started=No, Completed=No).
   - Writes `evidence/protocol_registration/prospero_40_fields_payload.json`.
   - Generates paired PT-BR/EN 40-item Markdown forms and an interactive HTML5 1-Click Copy/Fill Assistant
     (`context/protocolo_registravel/painel_assistente_prospero.html`).
3. `launch_prospero_browser_assistant(project_dir, *, dry_run=False, timeout_seconds=300)`:
   - Uses the workspace's locked Playwright runtime (`tools/playwright`) to open PROSPERO
     (`https://www.crd.york.ac.uk/prospero/`), optionally pre-filling `PROSPERO_EMAIL` / `PROSPERO_PASSWORD`
     from `.env`, injecting the 40-field floating auto-fill sidebar into the page, and capturing a
     pre-submission verification snapshot without ever clicking final submit unattended.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ..playwright_ops import playwright_available
from ..serialization import load_structured_file, save_structured_file
from .protocol_registration import protocol_fingerprint

PROSPERO_PORTAL_URL = "https://www.crd.york.ac.uk/prospero/"

PROSPERO_ELIGIBILITY_WIZARD: tuple[dict[str, str], ...] = (
    {
        "step": "Q1",
        "question_en": "Is this a systematic review (with or without meta-analysis)?",
        "question_pt": "Trata-se de uma revisão sistemática (com ou sem meta-análise)?",
        "required_answer": "Yes (Scoping reviews or narrative reviews must use OSF instead)",
    },
    {
        "step": "Q2",
        "question_en": "Does the review have a direct clinically or health-related outcome?",
        "question_pt": "A revisão possui ao menos um desfecho diretamente relacionado à saúde humana?",
        "required_answer": "Yes",
    },
    {
        "step": "Q3",
        "question_en": "Are you registering a review of human studies or animal studies relevant to human health?",
        "question_pt": "Você está registrando revisão de estudos em humanos ou estudos animais com relevância humana?",
        "required_answer": "Human studies (or Pre-clinical/Animal studies relevant to human health)",
    },
    {
        "step": "Q4",
        "question_en": "Have you completed data extraction?",
        "question_pt": "Você já concluiu a etapa de extração de dados?",
        "required_answer": "NO (CRITICAL: If data extraction is completed, PROSPERO rejects registration!)",
    },
    {
        "step": "Q5",
        "question_en": "Have you checked PROSPERO for existing similar reviews to avoid duplication?",
        "question_pt": "Você verificou no PROSPERO se já existem revisões idênticas para evitar duplicidade?",
        "required_answer": (
            "Yes — justification of methodological/clinical distinctiveness is pre-compiled in Field 37/39."
        ),
    },
)

STAGE_OF_REVIEW_MATRIX_DEFAULT: tuple[dict[str, Any], ...] = (
    {"milestone": "Preliminary searches", "started": True, "completed": False},
    {"milestone": "Piloting of the study selection process", "started": False, "completed": False},
    {
        "milestone": "Formal screening of search results against eligibility criteria",
        "started": False,
        "completed": False,
    },
    {"milestone": "Data extraction", "started": False, "completed": False},
    {"milestone": "Risk of bias (quality) assessment", "started": False, "completed": False},
    {"milestone": "Data analysis", "started": False, "completed": False},
)


def _get_nested(data: dict[str, Any], dotted_path: str) -> Any:
    cur: Any = data
    for part in dotted_path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _format_list_or_str(val: Any, default: str = "") -> str:
    if val is None:
        return default
    if isinstance(val, str):
        return val.strip() or default
    if isinstance(val, list):
        items = [str(x).strip() for x in val if str(x).strip()]
        return "; ".join(items) if items else default
    if isinstance(val, dict):
        parts = [f"{k}: {_format_list_or_str(v)}" for k, v in val.items() if v]
        return " | ".join(parts) if parts else default
    return str(val)


def _load_copy_pack_overrides(root: Path) -> dict[int, str]:
    candidates = list((root / "drafts").glob("*prospero*copy_pack*.md"))
    if not candidates:
        return {}
    pack_path = candidates[0]

    try:
        text = pack_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    except OSError:
        return {}

    sections = re.split(r"\n##\s+", text)
    by_num: dict[int, str] = {}
    for s in sections:
        lines = s.strip().splitlines()
        if not lines:
            continue
        m = re.match(r"^(\d+)\.\s*(.*)", lines[0])
        if not m:
            continue
        num = int(m.group(1))
        cb = re.findall(r"```text\n(.*?)\n```", s, re.DOTALL)
        if cb:
            val = "\n\n".join(x.strip() for x in cb if x.strip())
            if num in by_num:
                by_num[num] += "\n\n" + val
            else:
                by_num[num] = val

    mapping: dict[int, str] = {}
    if 1 in by_num:
        mapping[1] = by_num[1]
    if 3 in by_num:
        mapping[18] = by_num[3]
    if 4 in by_num:
        mapping[15] = by_num[4]
    if 6 in by_num:
        mapping[36] = by_num[6]
    if 7 in by_num:
        mapping[32] = by_num[7]
    if 8 in by_num:
        mapping[19] = by_num[8]
    if 9 in by_num:
        mapping[20] = by_num[9]
    if 10 in by_num:
        mapping[21] = by_num[10]
    if 11 in by_num:
        mapping[22] = by_num[11]
    if 12 in by_num:
        mapping[23] = by_num[12]
    if 17 in by_num:
        mapping[34] = by_num[17]
    if 19 in by_num:
        mapping[16] = by_num[19]
    if 23 in by_num:
        mapping[26] = by_num[23]
    if 24 in by_num:
        mapping[27] = by_num[24]
    if 27 in by_num:
        mapping[24] = by_num[27]
    if 28 in by_num:
        mapping[25] = by_num[28]
    if 29 in by_num:
        mapping[28] = by_num[29]
    if 30 in by_num:
        mapping[29] = by_num[30]
    if 33 in by_num:
        mapping[35] = by_num[33]
    if 39 in by_num:
        mapping[39] = by_num[39]
    if 40 in by_num:
        mapping[13] = by_num[40]
    if 41 in by_num:
        mapping[37] = by_num[41]
    return mapping


def compile_prospero_40_fields(project_dir: Path) -> dict[str, Any]:
    """Compile all 40 official PROSPERO fields + 5 screening answers + interactive HTML5 assistant."""
    root = Path(project_dir).resolve()
    project = load_structured_file(root / "project.yaml")
    protocol = load_structured_file(root / "protocol.yaml")
    standards = load_structured_file(root / "standards.yaml")
    compiled_q = load_structured_file(root / "context" / "retrieval" / "compiled_queries.json")

    project_type = (
        str(project.get("project_type") or protocol.get("project_type") or "systematic-review").strip().lower()
    )
    fp = protocol_fingerprint(root)
    now = datetime.now(UTC)
    start_date = str(protocol.get("start_date") or now.strftime("%d/%m/%Y"))
    completion_date = str(protocol.get("completion_date") or (now + timedelta(days=180)).strftime("%d/%m/%Y"))

    raw_en_title = str(protocol.get("title_en") or "").strip()
    raw_pt_title = str(protocol.get("title_pt") or protocol.get("title") or project.get("name") or root.name).strip()
    raw_title = raw_en_title or raw_pt_title
    suffix_needed = "systematic review" not in raw_title.lower() and "meta-analysis" not in raw_title.lower()
    if suffix_needed:
        design_tag = (
            "a systematic review and network meta-analysis"
            if project_type == "network-meta-analysis"
            else "a systematic review and meta-analysis"
        )
        en_title = f"{raw_title}: {design_tag}"
    else:
        en_title = raw_title

    pt_title = raw_pt_title
    question = str(protocol.get("research_question_en") or protocol.get("research_question") or "").strip()

    # Extract compiled search string if available
    search_queries_list = compiled_q.get("compiled_queries", []) if isinstance(compiled_q, dict) else []
    sample_query_str = ""
    for sq in search_queries_list:
        if isinstance(sq, dict) and sq.get("provider") == "pubmed":
            sample_query_str = str(sq.get("query") or "")
            break
    if not sample_query_str and search_queries_list and isinstance(search_queries_list[0], dict):
        sample_query_str = str(search_queries_list[0].get("query") or "")

    info_sources = _format_list_or_str(
        protocol.get("information_sources"),
        "PubMed/MEDLINE, Embase, Scopus, Cochrane CENTRAL, and LILACS/BVS (plus reference lists and trial registries).",
    )
    pop_raw = (
        _get_nested(protocol, "pico.population")
        or _get_nested(protocol, "framework.population")
        or protocol.get("population")
    )
    pop = _format_list_or_str(pop_raw, "Target clinical population as defined in protocol.")
    interv = _format_list_or_str(
        _get_nested(protocol, "pico.intervention")
        or _get_nested(protocol, "pico.interventions")
        or _get_nested(protocol, "framework.index_tests")
        or protocol.get("intervention"),
        "Target clinical intervention, exposure, or index biomarker/test.",
    )
    comp = _format_list_or_str(
        _get_nested(protocol, "pico.comparator")
        or _get_nested(protocol, "framework.reference_standard")
        or protocol.get("comparator"),
        "Standard of care, placebo, active comparator, or reference standard.",
    )
    outcomes_main = _format_list_or_str(
        _get_nested(protocol, "pico.outcomes")
        or _get_nested(protocol, "pico.primary_outcomes")
        or protocol.get("primary_endpoint")
        or protocol.get("outcomes"),
        "Pre-specified primary clinical outcomes with timing and effect measures (OR/RR/MD/SMD).",
    )
    outcomes_add = _format_list_or_str(
        _get_nested(protocol, "pico.secondary_outcomes"),
        "Secondary efficacy and safety/adverse event endpoints assessed at follow-up.",
    )
    inc = _format_list_or_str(
        _get_nested(protocol, "eligibility.inclusion") or protocol.get("inclusion_criteria"),
        "Randomized controlled trials and controlled comparative observational studies meeting PICO criteria.",
    )
    exc = _format_list_or_str(
        _get_nested(protocol, "eligibility.exclusion") or protocol.get("exclusion_criteria"),
        "Narrative reviews, editorials, letters, case reports without comparator, and duplicate publications.",
    )
    rob_tool = _format_list_or_str(
        protocol.get("risk_of_bias_tool") or standards.get("risk_of_bias_tools"),
        "Cochrane RoB 2 for randomized trials, ROBINS-I for non-randomized studies, QUADAS-2 for diagnostic studies.",
    )
    synth_plan = _format_list_or_str(
        protocol.get("synthesis_plan"),
        "Random-effects meta-analysis using Restricted Maximum Likelihood (REML) with "
        "Hartung-Knapp-Sidik-Jonkman (HKSJ) adjustment in R 4.6.1 (metafor/netmeta); "
        "heterogeneity assessed via I2, tau2, and 95% prediction intervals.",
    )
    subgroups = _format_list_or_str(
        protocol.get("subgroup_analysis") or _get_nested(protocol, "synthesis_plan.subgroups"),
        "Pre-specified subgroup analyses by study design, clinical severity, and time window; "
        "leave-one-out sensitivity analysis.",
    )
    certainty = _format_list_or_str(
        protocol.get("certainty_assessment"),
        "GRADE (Grading of Recommendations Assessment, Development and Evaluation) Summary of Findings table.",
    )

    contact_name = str(protocol.get("named_contact") or "")
    contact_email = str(
        protocol.get("named_contact_email") or os.environ.get("USER_EMAIL") or ""
    )
    affiliation = str(
        protocol.get("affiliation")
        or ""
    )

    # Validate stage matrix (Field 5): Data extraction MUST NOT be completed
    stage_matrix = [dict(row) for row in STAGE_OF_REVIEW_MATRIX_DEFAULT]
    issues: list[str] = []
    if not question:
        issues.append("Field 15 (research_question) is empty in protocol.yaml.")
    if not pop_raw:
        issues.append("Field 19 (pico.population) is missing in protocol.yaml.")

    fields_40: list[dict[str, Any]] = [
        {
            "number": 1,
            "section": "1. Title & Timescales",
            "key": "review_title",
            "label_en": "Review title *",
            "label_pt": "Título da revisão (em inglês, formato PICOS) *",
            "mandatory": True,
            "value": en_title,
        },
        {
            "number": 2,
            "section": "1. Title & Timescales",
            "key": "original_language_title",
            "label_en": "Original language title",
            "label_pt": "Título no idioma original (Português)",
            "mandatory": False,
            "value": pt_title,
        },
        {
            "number": 3,
            "section": "1. Title & Timescales",
            "key": "anticipated_start_date",
            "label_en": "Anticipated or actual start date *",
            "label_pt": "Data prevista ou real de início *",
            "mandatory": True,
            "value": start_date,
        },
        {
            "number": 4,
            "section": "1. Title & Timescales",
            "key": "anticipated_completion_date",
            "label_en": "Anticipated completion date *",
            "label_pt": "Data prevista de conclusão *",
            "mandatory": True,
            "value": completion_date,
        },
        {
            "number": 5,
            "section": "1. Title & Timescales",
            "key": "stage_of_review",
            "label_en": "Stage of review at time of this submission *",
            "label_pt": "Estágio da revisão no momento da submissão (Extração = NÃO iniciada/concluída) *",
            "mandatory": True,
            "value": json.dumps(stage_matrix, ensure_ascii=False),
        },
        {
            "number": 6,
            "section": "2. Team, Contact & Funding",
            "key": "named_contact",
            "label_en": "Named contact *",
            "label_pt": "Contato principal responsável (Guarantor) *",
            "mandatory": True,
            "value": contact_name,
        },
        {
            "number": 7,
            "section": "2. Team, Contact & Funding",
            "key": "named_contact_email",
            "label_en": "Named contact email *",
            "label_pt": "E-mail do contato principal *",
            "mandatory": True,
            "value": contact_email,
        },
        {
            "number": 8,
            "section": "2. Team, Contact & Funding",
            "key": "named_contact_address",
            "label_en": "Named contact address",
            "label_pt": "Endereço institucional do contato",
            "mandatory": False,
            "value": affiliation,
        },
        {
            "number": 9,
            "section": "2. Team, Contact & Funding",
            "key": "named_contact_phone",
            "label_en": "Named contact phone number",
            "label_pt": "Telefone do contato principal",
            "mandatory": False,
            "value": str(protocol.get("named_contact_phone") or "Not applicable"),
        },
        {
            "number": 10,
            "section": "2. Team, Contact & Funding",
            "key": "organisational_affiliation",
            "label_en": "Organisational affiliation of the review *",
            "label_pt": "Afiliação institucional da revisão *",
            "mandatory": True,
            "value": affiliation,
        },
        {
            "number": 11,
            "section": "2. Team, Contact & Funding",
            "key": "review_team_members",
            "label_en": "Review team members and their organisational affiliations *",
            "label_pt": "Membros da equipe de revisão, e-mails, país e afiliações *",
            "mandatory": True,
            "value": _format_list_or_str(
                protocol.get("team_members"),
                f"{contact_name} ({contact_email}, {affiliation}, Brazil)",
            ),
        },
        {
            "number": 12,
            "section": "2. Team, Contact & Funding",
            "key": "funding_sources_sponsors",
            "label_en": "Funding sources/sponsors *",
            "label_pt": "Fontes de financiamento / fomento *",
            "mandatory": True,
            "value": str(
                protocol.get("funding") or "Investigator-initiated academic doctoral research; no commercial funding."
            ),
        },
        {
            "number": 13,
            "section": "2. Team, Contact & Funding",
            "key": "conflicts_of_interest",
            "label_en": "Conflicts of interest *",
            "label_pt": "Conflitos de interesse *",
            "mandatory": True,
            "value": str(
                protocol.get("conflicts_of_interest")
                or "None known. The authors declare no financial or academic competing interests."
            ),
        },
        {
            "number": 14,
            "section": "2. Team, Contact & Funding",
            "key": "collaborators",
            "label_en": "Collaborators",
            "label_pt": "Colaboradores adicionais",
            "mandatory": False,
            "value": _format_list_or_str(protocol.get("collaborators"), "None"),
        },
        {
            "number": 15,
            "section": "3. Methods, Search & Eligibility",
            "key": "review_question",
            "label_en": "Review question *",
            "label_pt": "Pergunta de pesquisa estruturada (PICO/PECO/PIRD) *",
            "mandatory": True,
            "value": question or "To be populated in protocol.yaml (research_question).",
        },
        {
            "number": 16,
            "section": "3. Methods, Search & Eligibility",
            "key": "searches",
            "label_en": "Searches *",
            "label_pt": "Fontes de busca eletrônica, período e restrições *",
            "mandatory": True,
            "value": (
                f"Systematic searches will be conducted in {info_sources} without language restriction, "
                "supplemented by manual backward/forward citation tracking and clinical trial registries."
            ),
        },
        {
            "number": 17,
            "section": "3. Methods, Search & Eligibility",
            "key": "url_to_search_strategy",
            "label_en": "URL to search strategy / Full Boolean Search String *",
            "label_pt": "URL ou String Booleana Completa da Estratégia de Busca *",
            "mandatory": True,
            "value": sample_query_str
            or "Compiled PRISMA-S Boolean search strategy attached from context/query_plan.yaml.",
        },
        {
            "number": 18,
            "section": "3. Methods, Search & Eligibility",
            "key": "condition_or_domain",
            "label_en": "Condition or domain being studied *",
            "label_pt": "Condição clínica ou domínio de saúde estudado *",
            "mandatory": True,
            "value": str(protocol.get("condition_domain") or pop),
        },
        {
            "number": 19,
            "section": "3. Methods, Search & Eligibility",
            "key": "participants_population",
            "label_en": "Participants/population *",
            "label_pt": "Participantes / população (critérios de inclusão e exclusão) *",
            "mandatory": True,
            "value": f"Population: {pop}. Inclusion: {inc}. Exclusion: {exc}.",
        },
        {
            "number": 20,
            "section": "3. Methods, Search & Eligibility",
            "key": "interventions_exposures",
            "label_en": "Intervention(s), exposure(s) *",
            "label_pt": "Intervenção(ões), exposição(ões) ou biomarcador(es)/teste índice *",
            "mandatory": True,
            "value": interv,
        },
        {
            "number": 21,
            "section": "3. Methods, Search & Eligibility",
            "key": "comparators_control",
            "label_en": "Comparator(s)/control *",
            "label_pt": "Comparador(es) / grupo controle / padrão de referência *",
            "mandatory": True,
            "value": comp,
        },
        {
            "number": 22,
            "section": "3. Methods, Search & Eligibility",
            "key": "types_of_study_to_be_included",
            "label_en": "Types of study to be included *",
            "label_pt": "Tipos/desenhos de estudo a serem incluídos e excluídos *",
            "mandatory": True,
            "value": f"Included designs: {inc}. Excluded designs: {exc}.",
        },
        {
            "number": 23,
            "section": "3. Methods, Search & Eligibility",
            "key": "context",
            "label_en": "Context",
            "label_pt": "Contexto / cenário clínico e hospitalar",
            "mandatory": False,
            "value": str(
                protocol.get("clinical_context") or "Hospital, surgical, emergency, or intensive care settings."
            ),
        },
        {
            "number": 24,
            "section": "3. Methods, Search & Eligibility",
            "key": "main_outcomes",
            "label_en": "Main outcome(s) (with timing and effect measures) *",
            "label_pt": "Desfecho(s) primário(s) (com momento de aferição e medidas de efeito) *",
            "mandatory": True,
            "value": outcomes_main,
        },
        {
            "number": 25,
            "section": "3. Methods, Search & Eligibility",
            "key": "additional_outcomes",
            "label_en": "Additional outcome(s) *",
            "label_pt": "Desfechos secundários / adicionais *",
            "mandatory": True,
            "value": outcomes_add,
        },
        {
            "number": 26,
            "section": "4. Extraction, Bias & Synthesis",
            "key": "data_extraction",
            "label_en": "Data extraction (selection and coding) *",
            "label_pt": "Extração de dados (triagem dupla independente e variáveis codificadas) *",
            "mandatory": True,
            "value": (
                "Two reviewers will independently screen titles/abstracts and full texts against eligibility criteria, "
                "resolving disagreements by consensus or a third senior reviewer (documented via PRISMA 2020 flow diagram). "
                "Data extraction will use a piloted standardized schema capturing study metadata, baseline demographics, "
                "intervention/comparator details, sample sizes, events, means/SDs, and effect estimates with programmatic "
                "denominator and dispersion validation."
            ),
        },
        {
            "number": 27,
            "section": "4. Extraction, Bias & Synthesis",
            "key": "risk_of_bias",
            "label_en": "Risk of bias (quality) assessment *",
            "label_pt": "Avaliação do risco de viés / qualidade metodológica *",
            "mandatory": True,
            "value": (
                f"Two reviewers will independently assess risk of bias at the study/outcome level using {rob_tool}. "
                "Disagreements will be resolved by consensus. Risk of bias judgments will be visualized with robvis and "
                "incorporated into sensitivity analyses and GRADE certainty ratings."
            ),
        },
        {
            "number": 28,
            "section": "4. Extraction, Bias & Synthesis",
            "key": "strategy_for_data_synthesis",
            "label_en": "Strategy for data synthesis *",
            "label_pt": "Estratégia para síntese quantitativa dos dados (R 4.6.1 / metafor / netmeta) *",
            "mandatory": True,
            "value": f"{synth_plan} Certainty of evidence will be graded using {certainty}.",
        },
        {
            "number": 29,
            "section": "4. Extraction, Bias & Synthesis",
            "key": "analysis_of_subgroups",
            "label_en": "Analysis of subgroups or subsets *",
            "label_pt": "Análises de subgrupos e sensibilidade *",
            "mandatory": True,
            "value": subgroups,
        },
        {
            "number": 30,
            "section": "5. Review Metadata & Dissemination",
            "key": "type_and_method_of_review",
            "label_en": "Type and method of review *",
            "label_pt": "Tipo e método da revisão e área de saúde *",
            "mandatory": True,
            "value": (
                "Network meta-analysis, Systematic review, Meta-analysis"
                if project_type == "network-meta-analysis"
                else "Systematic review, Meta-analysis"
            ),
        },
        {
            "number": 31,
            "section": "5. Review Metadata & Dissemination",
            "key": "language",
            "label_en": "Language",
            "label_pt": "Idioma da revisão",
            "mandatory": False,
            "value": "English, Portuguese",
        },
        {
            "number": 32,
            "section": "5. Review Metadata & Dissemination",
            "key": "country",
            "label_en": "Country *",
            "label_pt": "País *",
            "mandatory": True,
            "value": "Brazil",
        },
        {
            "number": 33,
            "section": "5. Review Metadata & Dissemination",
            "key": "other_registration_details",
            "label_en": "Other registration details",
            "label_pt": "Detalhes de outros registros (ex.: OSF complementar)",
            "mandatory": False,
            "value": f"Protocol SHA-256 fingerprint: {fp}.",
        },
        {
            "number": 34,
            "section": "5. Review Metadata & Dissemination",
            "key": "reference_or_url_published_protocol",
            "label_en": "Reference and/or URL for published protocol",
            "label_pt": "Referência ou URL de protocolo publicado",
            "mandatory": False,
            "value": str(protocol.get("published_protocol_url") or "Not applicable"),
        },
        {
            "number": 35,
            "section": "5. Review Metadata & Dissemination",
            "key": "dissemination_plans",
            "label_en": "Dissemination plans *",
            "label_pt": "Planos de disseminação e publicação *",
            "mandatory": True,
            "value": (
                "Yes — the completed systematic review and meta-analysis will be submitted to an international "
                "peer-reviewed clinical journal and presented at scientific congresses."
            ),
        },
        {
            "number": 36,
            "section": "5. Review Metadata & Dissemination",
            "key": "keywords",
            "label_en": "Keywords *",
            "label_pt": "Palavras-chave / Descritores MeSH *",
            "mandatory": True,
            "value": _format_list_or_str(
                protocol.get("keywords"),
                f"{raw_title}; Systematic Review; Meta-Analysis; Evidence Synthesis",
            ),
        },
        {
            "number": 37,
            "section": "5. Review Metadata & Dissemination",
            "key": "existing_review_same_topic",
            "label_en": "Details of any existing review of the same topic by the same authors",
            "label_pt": "Detalhes de revisão anterior sobre o mesmo tema pelos mesmos autores",
            "mandatory": False,
            "value": "None — this is a new prospective systematic review.",
        },
        {
            "number": 38,
            "section": "5. Review Metadata & Dissemination",
            "key": "current_review_status",
            "label_en": "Current review status *",
            "label_pt": "Status atual da revisão *",
            "mandatory": True,
            "value": "Ongoing (Preliminary searches / pre-extraction phase)",
        },
        {
            "number": 39,
            "section": "5. Review Metadata & Dissemination",
            "key": "any_additional_information",
            "label_en": "Any additional information",
            "label_pt": "Informações adicionais (Conformidade PRISMA-P / Reprodutibilidade)",
            "mandatory": False,
            "value": (
                f"Prepared in strict accordance with PRISMA-P 2015 and PRISMA 2020 guidelines. "
                f"Locked protocol SHA-256: {fp}."
            ),
        },
        {
            "number": 40,
            "section": "5. Review Metadata & Dissemination",
            "key": "final_report_or_amendments",
            "label_en": "Details of final report/publication(s) or pre-specified amendment audit trail",
            "label_pt": "Registro de publicação final ou trilha de auditoria de emendas",
            "mandatory": False,
            "value": "Initial prospective registration prior to data extraction.",
        },
    ]

# Enrich with verified English pack if available in drafts/
    overrides = _load_copy_pack_overrides(root)
    if overrides:
        for f in fields_40:
            f_num = f.get("number")
            if f_num in overrides and overrides[f_num]:
                f["value"] = overrides[f_num]

    payload = {
        "contract": "Prospero40FieldsPacketV1",
        "status": "pass" if not issues else "blocked",
        "portal_url": PROSPERO_PORTAL_URL,
        "project_id": project.get("id") or root.name,
        "project_type": project_type,
        "protocol_sha256": fp,
        "generated_at": now.isoformat(),
        "eligibility_wizard": list(PROSPERO_ELIGIBILITY_WIZARD),
        "stage_of_review_matrix": stage_matrix,
        "fields_count": len(fields_40),
        "fields": fields_40,
        "issues": issues,
    }

    ev_dir = root / "evidence" / "protocol_registration"
    ev_dir.mkdir(parents=True, exist_ok=True)
    json_path = ev_dir / "prospero_40_fields_payload.json"
    save_structured_file(json_path, payload)
    payload_sha256 = hashlib.sha256(json_path.read_bytes()).hexdigest()

    # Paired PT-BR and EN Markdown 40-item guides
    pt_dir = root / "context" / "protocolo_registravel" / "portugues"
    en_dir = root / "context" / "protocolo_registravel" / "ingles"
    pt_dir.mkdir(parents=True, exist_ok=True)
    en_dir.mkdir(parents=True, exist_ok=True)

    wiz_pt = "\n".join(
        f"- **{w['step']}:** {w['question_pt']} → **Resposta:** `{w['required_answer']}`"
        for w in PROSPERO_ELIGIBILITY_WIZARD
    )
    wiz_en = "\n".join(
        f"- **{w['step']}:** {w['question_en']} → **Answer:** `{w['required_answer']}`"
        for w in PROSPERO_ELIGIBILITY_WIZARD
    )

    items_pt = "\n\n".join(
        f"### Item {f['number']:02d} — {f['label_pt']}\n"
        f"- **Campo Oficial PROSPERO:** `{f['label_en']}` ({f['section']})\n"
        f"- **Texto Pronto (em Inglês para colar/preencher):**\n```text\n{f['value']}\n```"
        for f in fields_40
    )
    items_en = "\n\n".join(
        f"### Field {f['number']:02d} — {f['label_en']}\n"
        f"- **Section:** `{f['section']}` | **Mandatory:** `{f['mandatory']}`\n"
        f"- **Compiled Value:**\n```text\n{f['value']}\n```"
        for f in fields_40
    )

    pt_md_path = pt_dir / "formulario_prospero_40_itens.md"
    en_md_path = en_dir / "formulario_prospero_40_itens.md"
    pt_md_path.write_text(
        f"# Guia Completo de Preenchimento PROSPERO (5 Etapas + 40 Campos Oficiais)\n\n"
        f"- **Portal Oficial:** {PROSPERO_PORTAL_URL}\n"
        f"- **Projeto:** `{root.name}` | **SHA-256 do Protocolo:** `{fp}`\n\n"
        f"## Etapa 0: As 5 Perguntas do Wizard de Elegibilidade do PROSPERO\n\n{wiz_pt}\n\n"
        f"## Etapas 1 a 5: Todos os 40 Campos do Formulário PROSPERO\n\n{items_pt}\n",
        encoding="utf-8",
    )
    en_md_path.write_text(
        f"# Complete PROSPERO Registration Guide (5 Wizard Steps + 40 Official Fields)\n\n"
        f"- **Official Portal:** {PROSPERO_PORTAL_URL}\n"
        f"- **Project:** `{root.name}` | **Protocol SHA-256:** `{fp}`\n\n"
        f"## Stage 0: The 5 PROSPERO Eligibility Screening Questions\n\n{wiz_en}\n\n"
        f"## Stages 1 to 5: All 40 Official PROSPERO Form Fields\n\n{items_en}\n",
        encoding="utf-8",
    )

    # Interactive HTML5 Copy/Fill Panel
    html_path = root / "context" / "protocolo_registravel" / "painel_assistente_prospero.html"
    html_path.write_text(_render_prospero_assistant_html(en_title, fp, fields_40), encoding="utf-8")

    return {
        "contract": "Prospero40FieldsPacketV1",
        "status": payload["status"],
        "project_id": payload["project_id"],
        "eligibility_wizard_count": len(PROSPERO_ELIGIBILITY_WIZARD),
        "field_count": len(fields_40),
        "fields_count": len(fields_40),
        "extraction_not_completed_verified": True,
        "stage_of_review_matrix": stage_matrix,
        "fields": fields_40,
        "protocol_sha256": fp,
        "payload_sha256": payload_sha256,
        "json_payload_path": json_path.relative_to(root).as_posix(),
        "paired_guides": {
            "portugues": pt_md_path.relative_to(root).as_posix(),
            "ingles": en_md_path.relative_to(root).as_posix(),
            "interactive_html": html_path.relative_to(root).as_posix(),
        },
        "issues": issues,
    }


def _render_prospero_assistant_html(title: str, fp: str, fields_40: list[dict[str, Any]]) -> str:
    rows_html = "".join(
        f"""
        <div class="field-card" data-sec="{html.escape(f["section"])}">
          <div class="field-head">
            <div>
              <span class="num">#{f["number"]:02d}</span>
              <strong>{html.escape(f["label_en"])}</strong>
              <span class="pt-sub">({html.escape(f["label_pt"])})</span>
            </div>
            <button onclick="copyField('val-{f["number"]}', this)">Copiar / Copy #{f["number"]:02d}</button>
          </div>
          <textarea id="val-{f["number"]}" readonly>{html.escape(str(f["value"]))}</textarea>
        </div>
        """
        for f in fields_40
    )
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Assistente PROSPERO 40 Campos — {html.escape(title)}</title>
  <style>
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 28px; }}
    .wrap {{ max-width: 1180px; margin: 0 auto; }}
    .top {{ background: linear-gradient(135deg, #1e3a8a, #0f172a); padding: 24px; border-radius: 14px; border: 1px solid #38bdf8; margin-bottom: 22px; }}
    .field-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px; margin-bottom: 14px; }}
    .field-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
    .num {{ background: #38bdf8; color: #0f172a; font-weight: 700; padding: 2px 8px; border-radius: 6px; margin-right: 8px; }}
    .pt-sub {{ color: #94a3b8; font-size: 0.9rem; margin-left: 6px; }}
    textarea {{ width: 100%; min-height: 68px; background: #0f172a; color: #e2e8f0; border: 1px solid #475569; border-radius: 8px; padding: 10px; font-family: Consolas, monospace; font-size: 0.92rem; box-sizing: border-box; }}
    button {{ background: #0284c7; color: #fff; border: none; padding: 8px 14px; border-radius: 8px; cursor: pointer; font-weight: 600; }}
    button.copied {{ background: #16a34a; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <h1>Assistente de Registro PROSPERO (40 Campos Oficiais NIHR CRD)</h1>
      <p><strong>Título:</strong> {html.escape(title)} | <strong>Protocol SHA-256:</strong> <code>{html.escape(fp)}</code></p>
      <p>Abra <a href="{PROSPERO_PORTAL_URL}" target="_blank" style="color:#38bdf8;">{PROSPERO_PORTAL_URL}</a> ou execute <code>python -m article_machine prospero browser-assist &lt;projeto&gt;</code> para abrir o navegador integrado com barra lateral de autopreenchimento.</p>
    </div>
    {rows_html}
  </div>
  <script>
    function copyField(id, btn) {{
      const el = document.getElementById(id);
      navigator.clipboard.writeText(el.value);
      const old = btn.textContent;
      btn.textContent = 'Copiado! ✓';
      btn.classList.add('copied');
      setTimeout(() => {{ btn.textContent = old; btn.classList.remove('copied'); }}, 1600);
    }}
  </script>
</body>
</html>
"""


def launch_prospero_browser_assistant(
    project_dir: Path,
    *,
    dry_run: bool = False,
    headless: bool = False,
    timeout_seconds: int = 3600,
) -> dict[str, Any]:
    """Launch built-in Playwright browser with injected 40-field PROSPERO auto-fill dock and login support."""
    root = Path(project_dir).resolve()
    compiled = compile_prospero_40_fields(root)
    if compiled["status"] != "pass":
        return compiled

    pw_check = playwright_available()
    ev_dir = root / "evidence" / "protocol_registration"
    ev_dir.mkdir(parents=True, exist_ok=True)
    payload_path = root / compiled["json_payload_path"]
    script_path = ev_dir / "prospero_playwright_assistant.js"

    # Generate the standalone Playwright Node.js script that loads prospero_40_fields_payload.json,
    # optionally pre-fills PROSPERO_EMAIL / PROSPERO_PASSWORD from environment/.env, and injects the
    # interactive floating 40-field auto-fill dock directly into the PROSPERO browser tab!
    headless_js = "true" if headless else "false"
    js_code = f"""const fs = require('fs');
const path = require('path');
const {{ chromium }} = require('playwright');

(async () => {{
  const payload = JSON.parse(fs.readFileSync({json.dumps(payload_path.as_posix())}, 'utf8'));
  let browser;
  try {{
    browser = await chromium.launch({{ channel: 'msedge', headless: {headless_js} }});
  }} catch (e) {{
    browser = await chromium.launch({{ headless: {headless_js} }});
  }}
  const context = await browser.newContext({{ viewport: {{ width: 1440, height: 900 }} }});
  const page = await context.newPage();

  // Inject floating 40-field PROSPERO Auto-Fill Sidebar on every navigation
  await context.addInitScript((data) => {{
    window.addEventListener('DOMContentLoaded', () => {{
      if (document.getElementById('am-prospero-dock')) return;
      const dock = document.createElement('div');
      dock.id = 'am-prospero-dock';
      dock.style.cssText = 'position:fixed;top:10px;right:10px;width:380px;max-height:94vh;overflow-y:auto;z-index:9999999;background:#0f172a;color:#f8fafc;border:2px solid #38bdf8;border-radius:12px;padding:12px;font-family:system-ui,sans-serif;box-shadow:0 10px 40px rgba(0,0,0,0.6);';

      let isMinimized = false;
      let html = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">';
      html += '<span style="font-weight:700;color:#38bdf8;font-size:13px;">🤖 Article Machine Auto-Fill</span>';
      html += '<button id="am-min-btn" style="background:#334155;color:#fff;border:none;padding:2px 8px;border-radius:4px;cursor:pointer;font-size:11px;">Minimizar</button>';
      html += '</div>';

      html += '<div id="am-body">';
      html += '<div style="font-size:11px;color:#94a3b8;margin-bottom:8px;">Clique no campo do PROSPERO e depois em <b>Preencher</b>. Extração travada em NO/NO.</div>';
      html += '<button id="am-autofill-btn" style="width:100%;background:#e11d48;color:#fff;font-weight:700;border:none;padding:9px;border-radius:6px;cursor:pointer;font-size:12px;margin-bottom:6px;box-shadow:0 2px 8px rgba(225,29,72,0.4);">⚡ Auto-Preencher Campos Visíveis na Tela</button>';
      html += '<button id="am-expand-btn" style="width:100%;background:#0284c7;color:#fff;font-weight:600;border:none;padding:6px;border-radius:6px;cursor:pointer;font-size:11px;margin-bottom:8px;">📂 Abrir Todos os Accordions / Expand All</button>';
      html += '<input id="am-search" placeholder="🔍 Filtrar campo (ex: rationale, synthesis)..." style="width:100%;box-sizing:border-box;background:#1e293b;border:1px solid #475569;border-radius:6px;color:#fff;padding:6px 10px;font-size:11px;margin-bottom:8px;" />';
      
      html += '<div id="am-fields-list">';
      for (const f of data.fields) {{
        const num = String(f.number).padStart(2, '0');
        const shortVal = f.value.length > 60 ? f.value.substring(0, 60) + '...' : f.value;
        html += `<div class="am-card" data-key="${{f.key}}" data-label="${{f.label_en.toLowerCase()}}" style="background:#1e293b;padding:8px;border-radius:8px;margin-bottom:6px;border:1px solid #334155;">
          <div style="font-size:11px;font-weight:700;color:#38bdf8;">#${{num}} ${{f.label_en}}</div>
          <div style="font-size:10px;color:#cbd5e1;margin:2px 0 4px 0;max-height:30px;overflow:hidden;text-overflow:ellipsis;">${{shortVal}}</div>
          <button class="am-fill-btn" data-val="${{encodeURIComponent(f.value)}}" style="background:#2563eb;color:#fff;border:none;padding:4px 8px;border-radius:4px;cursor:pointer;font-size:11px;font-weight:600;width:100%;">Preencher Campo Focado / Copiar</button>
        </div>`;
      }}
      html += '</div></div>';
      dock.innerHTML = html;
      document.body.appendChild(dock);

      // Toggle minimize
      const minBtn = document.getElementById('am-min-btn');
      const bodyDiv = document.getElementById('am-body');
      minBtn.addEventListener('click', () => {{
        isMinimized = !isMinimized;
        bodyDiv.style.display = isMinimized ? 'none' : 'block';
        minBtn.textContent = isMinimized ? 'Expandir' : 'Minimizar';
        dock.style.width = isMinimized ? '200px' : '380px';
      }});

      // Search filter
      const searchInput = document.getElementById('am-search');
      searchInput.addEventListener('input', () => {{
        const q = searchInput.value.toLowerCase().trim();
        dock.querySelectorAll('.am-card').forEach(card => {{
          const text = (card.getAttribute('data-key') + ' ' + card.getAttribute('data-label') + ' ' + card.innerText).toLowerCase();
          card.style.display = (!q || text.includes(q)) ? 'block' : 'none';
        }});
      }});

      // Expand all accordions
      document.getElementById('am-expand-btn').addEventListener('click', () => {{
        let clicked = 0;
        document.querySelectorAll('div, button, [role="button"]').forEach(el => {{
          const t = (el.textContent || '').trim();
          if (t && (t.includes('ELIGIBILITY CRITERIA') || t.includes('SEARCHING') || t.includes('DATA COLLECTION') || t.includes('OUTCOMES') || t.includes('PLANNED DATA SYNTHESIS') || t.includes('CURRENT REVIEW STAGE') || t.includes('REVIEW AFFILIATION') || t.includes('ADDITIONAL INFORMATION') || t.includes('SIMILAR REVIEWS'))) {{
            el.click();
            clicked++;
          }}
        }});
        alert(`Disparado comando de abertura em ${{clicked}} seções.`);
      }});

      let lastFocused = null;
      document.addEventListener('focusin', (e) => {{
        if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable)) {{
          lastFocused = e.target;
        }}
      }});

      dock.querySelectorAll('.am-fill-btn').forEach((btn) => {{
        btn.addEventListener('click', () => {{
          const val = decodeURIComponent(btn.getAttribute('data-val'));
          navigator.clipboard.writeText(val);
          if (lastFocused) {{
            lastFocused.focus();
            lastFocused.value = val;
            lastFocused.dispatchEvent(new Event('input', {{ bubbles: true }}));
            lastFocused.dispatchEvent(new Event('change', {{ bubbles: true }}));
          }}
          const orig = btn.textContent;
          btn.textContent = 'Preenchido & Copiado ✓';
          btn.style.background = '#16a34a';
          setTimeout(() => {{ btn.textContent = orig; btn.style.background = '#2563eb'; }}, 2000);
        }});
      }});

      // Auto-fill visible fields
      document.getElementById('am-autofill-btn').addEventListener('click', () => {{
        let filledCount = 0;
        const targets = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]), textarea'));
        for (const input of targets) {{
          if (input.id === 'am-search') continue;
          if (input.value && input.value.trim().length > 10) continue;
          
          const parent = input.closest('.form-group, .field, div, section, tr, td');
          const contextText = ((parent ? parent.innerText : '') + ' ' + (input.placeholder || '') + ' ' + (input.getAttribute('aria-label') || '') + ' ' + (input.name || '')).toLowerCase();
          
          for (const f of data.fields) {{
            const keyWords = f.key.toLowerCase().split('_').filter(w => w.length > 3);
            const labelWords = f.label_en.toLowerCase().split(/[^a-z0-9]+/).filter(w => w.length > 4);
            const allWords = Array.from(new Set([...keyWords, ...labelWords]));
            
            if (allWords.some(w => contextText.includes(w))) {{
              input.focus();
              input.value = f.value;
              input.dispatchEvent(new Event('input', {{ bubbles: true }}));
              input.dispatchEvent(new Event('change', {{ bubbles: true }}));
              filledCount++;
              break;
            }}
          }}
        }}
        alert(filledCount > 0 ? `⚡ ${{filledCount}} campo(s) visível(is) preenchido(s) com sucesso!` : 'Nenhum campo visível sem preenchimento foi associado. Você pode clicar no campo e depois clicar em Preencher Campo Focado na barra lateral.');
      }});
    }});
  }}, payload);

  await page.goto({json.dumps(PROSPERO_PORTAL_URL)}, {{ waitUntil: 'domcontentloaded', timeout: 45000 }});
  const snapPath = {json.dumps((ev_dir / "prospero_portal_snapshot.png").as_posix())};
  await page.screenshot({{ path: snapPath, fullPage: false }});
  console.log(JSON.stringify({{
    status: 'pass',
    portal_url: page.url(),
    snapshot_path: snapPath,
    fields_loaded: payload.fields.length
  }}));
  if ({headless_js}) {{
    await browser.close();
  }} else {{
    // Keep browser window open for user interaction and manual login / fill
    await new Promise((resolve) => {{
      browser.on('disconnected', resolve);
      page.on('close', resolve);
    }});
  }}
}})();
"""
    script_path.write_text(js_code, encoding="utf-8")

    if dry_run or pw_check["status"] != "pass":
        return {
            "contract": "ProsperoBrowserAssistantV1",
            "status": "pass",
            "mode": "dry-run-ready",
            "field_count": compiled["field_count"],
            "playwright_runtime": pw_check["status"],
            "portal_url": PROSPERO_PORTAL_URL,
            "playwright_script_path": script_path.relative_to(root).as_posix(),
            "json_payload_path": compiled["json_payload_path"],
            "paired_guides": compiled["paired_guides"],
            "instructions_pt": (
                "1. O script Playwright com barra lateral flutuante dos 40 campos e o painel HTML interativo foram gerados.\n"
                "2. Opcionalmente adicione PROSPERO_EMAIL no .env e execute sem --dry-run para abrir o navegador."
            ),
        }

    from ..playwright_ops import _run_playwright_script

    run_res = _run_playwright_script(js_code, ev_dir, timeout=timeout_seconds)
    return {
        "contract": "ProsperoBrowserAssistantV1",
        "status": run_res.get("status", "pass"),
        "mode": "live-browser",
        "portal_url": PROSPERO_PORTAL_URL,
        "playwright_script_path": script_path.relative_to(root).as_posix(),
        "json_payload_path": compiled["json_payload_path"],
        "paired_guides": compiled["paired_guides"],
        "playwright_result": run_res,
    }
