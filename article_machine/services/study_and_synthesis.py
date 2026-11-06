"""Project Study Companion & R-Output-Driven Bilingual Synthesis Engine.

Provides:
1. Interactive & Markdown Bilingual Study Companion (`build_project_study_guide`):
   - Executive summary & clinical rationale (PT-BR & EN)
   - Step-by-step didactic explanation of the statistical/ML methodology (REML+HKSJ, I2/tau2/PI, NMA, GRADE,
   TRIPOD+AI, DCA, Conformal)
   - Guided interpretation of every R/Python output table, metric, and figure in `analysis/` and `figures/`
   - 12+ Defense & Peer-Review Q&A Flashcards (Thesis committee / Q1 Reviewer questions & answers in PT-BR and EN)
   - Interactive HTML5 Study & Flashcard Dashboard (`context/estudo_do_projeto/painel_estudo_interativo.html`)
2. Expanded Templates Catalog (`list_synthesis_templates`):
   - 6 Publication/Journal templates, 4 Slide Deck templates, 4 Poster templates, 4 Abstract templates (all paired
   PT-BR & EN)
3. R-Output Harvester & Complete Bilingual Deliverable Generator (`synthesize_from_r_outputs`):
   - Harvests CSV/TSV tables, JSON summaries, and PNG/SVG plots from `analysis/` and `figures/`
   - Updates `analysis/results_ledger.json`
   - Generates paired PT-BR and EN complete manuscripts, multi-format abstracts, HTML5 slide decks with speaker
   notes, and HTML5 posters
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ..serialization import load_structured_file, save_structured_file
from .scientific_execution import scientific_execution_gate

PUBLICATION_TEMPLATES: dict[str, dict[str, Any]] = {
    "jama-lancet-nejm-high-impact": {
        "id": "jama-lancet-nejm-high-impact",
        "name_pt": "Alto Impacto Clínico (JAMA / The Lancet / NEJM)",
        "name_en": "High-Impact Clinical (JAMA / The Lancet / NEJM)",
        "target_journals": ["JAMA", "JAMA Surgery", "The Lancet", "The Lancet Gastroenterology & Hepatology", "NEJM"],
        "max_words_main": 3500,
        "max_words_abstract": 350,
        "sections_pt": [
            "Pontos-Chave / Pesquisa em Contexto (Evidência anterior, Valor adicionado, Implicações)",
            (
                "Resumo Estruturado (Importância, Objetivo, Desenho/Cenário/Participantes, "
                "Intervenções/Exposições, Desfechos, Resultados, Conclusões, Registro)"
            ),
            "1. Introdução",
            (
                "2. Métodos (Protocolo e Registro, Fontes de Dados/Coorte, Desfechos, Análise "
                "Estatística em R e Sensibilidade, Ética/EQUATOR)"
            ),
            (
                "3. Resultados (Fluxo PRISMA/Coorte, Características Basais, Desfecho Primário, "
                "Desfechos Secundários e Subgrupos, Certeza GRADE / Calibração)"
            ),
            "4. Discussão (Achados Principais, Comparação com a Literatura, Implicações Clínicas, Forças e Limitações)",
            "5. Conclusões",
            (
                "Declarações Obrigatórias (Compartilhamento de Dados/Código, Financiamento, "
                "Conflitos de Interesse, Disclosure de IA)"
            ),
        ],
        "sections_en": [
            (
                "Key Points / Research in Context (Evidence before this study, Added value, "
                "Implications of all available evidence)"
            ),
            (
                "Structured Abstract (Importance, Objective, Design/Setting/Participants, "
                "Interventions/Exposures, Main Outcomes, Results, Conclusions, Registration)"
            ),
            "1. Introduction",
            (
                "2. Methods (Protocol & Registration, Data Sources/Cohort, Outcomes, R Statistical "
                "Analysis & Sensitivity, Ethics/EQUATOR)"
            ),
            (
                "3. Results (PRISMA/Cohort Flow, Baseline Characteristics, Primary Outcome, "
                "Secondary Outcomes & Subgroups, GRADE Certainty / Calibration)"
            ),
            (
                "4. Discussion (Principal Findings, Comparison with Prior Studies, Clinical "
                "Implications, Strengths & Limitations)"
            ),
            "5. Conclusions",
            "Mandatory Declarations (Data & Code Sharing, Funding, Competing Interests, AI Disclosure)",
        ],
    },
    "annals-wjes-bjs-surgical": {
        "id": "annals-wjes-bjs-surgical",
        "name_pt": "Cirurgia e Emergências Cirúrgicas (Annals of Surgery / WJES / BJS)",
        "name_en": "Surgery & Acute Care Surgery (Annals of Surgery / WJES / BJS)",
        "target_journals": [
            "Annals of Surgery",
            "World Journal of Emergency Surgery",
            "British Journal of Surgery",
            "Surgery",
        ],
        "max_words_main": 4000,
        "max_words_abstract": 300,
        "sections_pt": [
            "Mini-Resumo Cirúrgico (50 palavras) & Destaques Operatórios",
            "Resumo Estruturado (Introdução, Objetivo, Métodos, Resultados, Conclusão)",
            "1. Introdução eProblema Cirúrgico",
            (
                "2. Métodos (Desenho, Critérios de Elegibilidade/Coorte, Definições Operatórias, "
                "Modelagem Estatística em R)"
            ),
            "3. Resultados (Seleção/Coorte, Desfechos Cirúrgicos, Morbimortalidade, Tabelas e Figuras em R)",
            "4. Discussão Cirúrgica e Aplicabilidade à Beira do Leito",
            "5. Conclusão",
        ],
        "sections_en": [
            "Surgical Mini-Abstract (50 words) & Operative Highlights",
            "Structured Abstract (Background, Objective, Methods, Results, Conclusion)",
            "1. Introduction & Surgical Problem",
            "2. Methods (Design, Eligibility/Cohort, Operative Definitions, R Statistical Modeling)",
            "3. Results (Selection/Cohort, Operative Outcomes, Morbidity & Mortality, R Tables & Figures)",
            "4. Surgical Discussion & Bedside Applicability",
            "5. Conclusion",
        ],
    },
    "gastro-gut-cgh-digestive": {
        "id": "gastro-gut-cgh-digestive",
        "name_pt": "Gastroenterologia e Cirurgia Digestiva (Gastroenterology / Gut / CGH)",
        "name_en": "Gastroenterology & Digestive Surgery (Gastroenterology / Gut / CGH)",
        "target_journals": ["Gastroenterology", "Gut", "Clinical Gastroenterology and Hepatology", "Endoscopy"],
        "max_words_main": 4000,
        "max_words_abstract": 260,
        "sections_pt": [
            "O Que Você Precisa Saber (Contexto, Novos Achados, Impacto na Prática Clínica)",
            "Resumo Estruturado (Contexto e Objetivos, Métodos, Resultados, Conclusões)",
            "1. Introdução",
            "2. Materiais e Métodos",
            "3. Resultados",
            "4. Discussão",
            "5. Conclusão",
        ],
        "sections_en": [
            "What You Need to Know (Background, New Findings, Impact on Clinical Practice)",
            "Structured Abstract (Background & Aims, Methods, Results, Conclusions)",
            "1. Introduction",
            "2. Materials and Methods",
            "3. Results",
            "4. Discussion",
            "5. Conclusion",
        ],
    },
    "scielo-cbcd-acb-brasil": {
        "id": "scielo-cbcd-acb-brasil",
        "name_pt": "Periódicos Cirúrgicos Brasileiros Bilíngues (RCBC / ABCD / Acta Cir Bras)",
        "name_en": "Brazilian Bilingual Surgical Journals (RCBC / ABCD / Acta Cir Bras)",
        "target_journals": [
            "Revista do Colégio Brasileiro de Cirurgiões (RCBC)",
            "ABCD - Arquivos Brasileiros de Cirurgia Digestiva",
            "Acta Cirúrgica Brasileira",
        ],
        "max_words_main": 3500,
        "max_words_abstract": 250,
        "sections_pt": [
            "Mensagem Central / Destaques",
            "Resumo (Introdução, Objetivo, Métodos, Resultados, Conclusão) + Descritores DeCS",
            "Abstract (Background, Objective, Methods, Results, Conclusion) + MeSH Headings",
            "1. Introdução",
            "2. Métodos",
            "3. Resultados",
            "4. Discussão",
            "5. Conclusão",
        ],
        "sections_en": [
            "Central Message / Highlights",
            "Abstract (Background, Objective, Methods, Results, Conclusion) + MeSH Headings",
            "Resumo (Introdução, Objetivo, Métodos, Resultados, Conclusão) + Descritores DeCS",
            "1. Introduction",
            "2. Methods",
            "3. Results",
            "4. Discussion",
            "5. Conclusion",
        ],
    },
    "jamia-lancet-digital-health-ai": {
        "id": "jamia-lancet-digital-health-ai",
        "name_pt": "IA Médica e Modelos de Predição Clínica (Lancet Digital Health / JAMIA / TRIPOD+AI)",
        "name_en": "Medical AI & Clinical Prediction Modeling (Lancet Digital Health / JAMIA / TRIPOD+AI)",
        "target_journals": [
            "The Lancet Digital Health",
            "JAMIA",
            "npj Digital Medicine",
            "Artificial Intelligence in Medicine",
        ],
        "max_words_main": 4500,
        "max_words_abstract": 300,
        "sections_pt": [
            "Pesquisa em Contexto & Conformidade TRIPOD+AI / PROBAST+AI",
            (
                "Resumo Estruturado (Objetivo, Fontes de Dados, Partição sem Leakage, "
                "Discriminação/Calibração/DCA, Conclusão)"
            ),
            "1. Introdução e Necessidade Clínica da Predição",
            (
                "2. Métodos (Coortes, Tempo Zero T0, Tratamento de Missing Data, Validação Aninhada "
                "por Paciente, Calibração, DCA e Predição Conformal)"
            ),
            (
                "3. Resultados (Fluxo de Pacientes, Tabela 1, AUROC/AUPRC, Intercepto e Slope de "
                "Calibração, Benefício Líquido DCA, Subgrupos/Equidade)"
            ),
            "4. Discussão (Utilidade Clínica, Risco de Viés PROBAST+AI, Limitações e Implementação)",
            "5. Conclusão e Disponibilidade de Código/Pesos",
        ],
        "sections_en": [
            "Research in Context & TRIPOD+AI / PROBAST+AI Compliance",
            (
                "Structured Abstract (Objective, Data Sources, Zero-Leakage Partitioning, "
                "Discrimination/Calibration/DCA, Conclusion)"
            ),
            "1. Introduction & Clinical Prediction Need",
            (
                "2. Methods (Cohorts, Time-Zero T0, Missing Data Handling, Patient-Grouped "
                "Validation, Calibration, DCA & Conformal Prediction)"
            ),
            (
                "3. Results (Patient Flow, Table 1, AUROC/AUPRC, Calibration Intercept & Slope, DCA "
                "Net Benefit, Subgroups/Fairness)"
            ),
            "4. Discussion (Clinical Utility, PROBAST+AI Risk of Bias, Limitations & Deployment)",
            "5. Conclusion & Code/Model Availability",
        ],
    },
    "cochrane-bmj-systematic-review": {
        "id": "cochrane-bmj-systematic-review",
        "name_pt": "Revisão Sistemática e Meta-Análise Completa (BMJ / Cochrane / PRISMA 2020 / NMA)",
        "name_en": "Comprehensive Systematic Review & Meta-Analysis (BMJ / Cochrane / PRISMA 2020 / NMA)",
        "target_journals": [
            "BMJ",
            "Cochrane Database of Systematic Reviews",
            "Annals of Internal Medicine",
            "Syst Rev",
        ],
        "max_words_main": 5000,
        "max_words_abstract": 350,
        "sections_pt": [
            "O Que Este Estudo Adiciona (Box de Síntese de Evidência)",
            (
                "Resumo Estruturado PRISMA 2020 (Objetivo, Desenho, Fontes de Dados, Critérios de "
                "Elegibilidade, Síntese REML+HKSJ, Resultados, GRADE, Registro)"
            ),
            "1. Introdução",
            (
                "2. Métodos (Protocolo PROSPERO/OSF, Estratégia PRISMA-S Multi-Base, Triagem e "
                "Extração Dupla, RoB 2/ROBINS-I/QUADAS-2, Modelo REML+HKSJ em R)"
            ),
            (
                "3. Resultados (Fluxograma PRISMA 2020, Características dos Estudos, Risco de Viés, "
                "Síntese Quantitativa e Intervalo de Predição, Tabela SoF GRADE)"
            ),
            "4. Discussão",
            "5. Conclusões",
        ],
        "sections_en": [
            "What This Study Adds (Evidence Synthesis Box)",
            (
                "PRISMA 2020 Structured Abstract (Objective, Design, Data Sources, Eligibility "
                "Criteria, REML+HKSJ Synthesis, Results, GRADE, Registration)"
            ),
            "1. Introduction",
            (
                "2. Methods (PROSPERO/OSF Protocol, Multi-Database PRISMA-S Search, Duplicate "
                "Screening & Extraction, RoB 2/ROBINS-I/QUADAS-2, R REML+HKSJ Model)"
            ),
            (
                "3. Results (PRISMA 2020 Flowchart, Study Characteristics, Risk of Bias, "
                "Quantitative Synthesis & Prediction Interval, GRADE SoF Table)"
            ),
            "4. Discussion",
            "5. Conclusions",
        ],
    },
}

SLIDE_TEMPLATES: dict[str, dict[str, Any]] = {
    "congresso-cirurgico-oral-10min": {
        "id": "congresso-cirurgico-oral-10min",
        "name_pt": "Apresentação Oral de Congresso (10 min / 10 Slides)",
        "name_en": "Congress Oral Presentation (10 min / 10 Slides)",
        "duration_minutes": 10,
        "target_slides": 10,
    },
    "pitch-rapido-3min-5min": {
        "id": "pitch-rapido-3min-5min",
        "name_pt": "Short Oral / Pitch Rápido (3–5 min / 5 Slides)",
        "name_en": "Short Oral / Rapid Fire Pitch (3–5 min / 5 Slides)",
        "duration_minutes": 5,
        "target_slides": 5,
    },
    "defesa-qualificacao-doutorado-40min": {
        "id": "defesa-qualificacao-doutorado-40min",
        "name_pt": "Defesa / Qualificação de Doutorado (30–40 min / 14+ Slides + Backup Banca)",
        "name_en": "Doctoral Defense / Qualification (30–40 min / 14+ Slides + Defense Backup)",
        "duration_minutes": 40,
        "target_slides": 14,
    },
    "reuniao-clinica-journal-club-20min": {
        "id": "reuniao-clinica-journal-club-20min",
        "name_pt": "Reunião Científica / Discussão Metodológica do Grupo (20 min / 10 Slides)",
        "name_en": "Research Group / Methodological Journal Club (20 min / 10 Slides)",
        "duration_minutes": 20,
        "target_slides": 10,
    },
}

POSTER_TEMPLATES: dict[str, dict[str, Any]] = {
    "eposter-digital-16x9-congresso": {
        "id": "eposter-digital-16x9-congresso",
        "name_pt": "e-Poster Digital Widescreen 16:9 (1920x1080 — Congressos Internacionais e Brasileiros)",
        "name_en": "Widescreen 16:9 Digital e-Poster (1920x1080 — International & National Congresses)",
        "orientation": "landscape",
        "width_px": 1920,
        "height_px": 1080,
    },
    "a0-retrato-classico": {
        "id": "a0-retrato-classico",
        "name_pt": "Pôster Impresso A0 Retrato Clássico (841x1189 mm — 3 Colunas)",
        "name_en": "Classic A0 Portrait Printed Poster (841x1189 mm — 3 Columns)",
        "orientation": "portrait",
        "width_px": 1440,
        "height_px": 2036,
    },
    "a0-paisagem-visual": {
        "id": "a0-paisagem-visual",
        "name_pt": "Pôster Impresso A0 Paisagem Visual (1189x841 mm — 4 Colunas)",
        "name_en": "Visual A0 Landscape Printed Poster (1189x841 mm — 4 Columns)",
        "orientation": "landscape",
        "width_px": 2036,
        "height_px": 1440,
    },
    "better-poster-foco-achado": {
        "id": "better-poster-foco-achado",
        "name_pt": "Better Poster Moderno (Achado Clínico Central em Destaque + Figuras R)",
        "name_en": "Modern Better Poster (Central Clinical Takeaway Hero + R Figures)",
        "orientation": "landscape",
        "width_px": 1920,
        "height_px": 1080,
    },
}

ABSTRACT_TEMPLATES: dict[str, dict[str, Any]] = {
    "estruturado-revista-300p": {
        "id": "estruturado-revista-300p",
        "name_pt": "Resumo Estruturado de Periódico Q1 (250–350 palavras + Registro + DeCS/MeSH)",
        "name_en": "Q1 Journal Structured Abstract (250–350 words + Registration + MeSH)",
        "word_limit": 350,
    },
    "congresso-internacional-esicm-wses-acs": {
        "id": "congresso-internacional-esicm-wses-acs",
        "name_pt": "Resumo de Congresso Internacional (ESICM / WSES / ACS / DDW — 300 palavras)",
        "name_en": "International Congress Abstract (ESICM / WSES / ACS / DDW — 300 words)",
        "word_limit": 300,
    },
    "congresso-brasileiro-cbc-cbcd-sbcd": {
        "id": "congresso-brasileiro-cbc-cbcd-sbcd",
        "name_pt": "Resumo de Congresso Brasileiro (CBC / CBCD / SBAD — 250 palavras)",
        "name_en": "Brazilian Surgical Congress Abstract (CBC / CBCD / SBAD — 250 words)",
        "word_limit": 250,
    },
    "graphical-visual-abstract-brief": {
        "id": "graphical-visual-abstract-brief",
        "name_pt": "Roteiro de Visual / Graphical Abstract (3 Painéis Quantitativos)",
        "name_en": "Visual / Graphical Abstract Blueprint (3 Quantitative Panels)",
        "word_limit": 120,
    },
}


def list_synthesis_templates() -> dict[str, Any]:
    """Return all available bilingual publication, slide, poster, and abstract templates."""
    return {
        "contract": "BilingualSynthesisTemplatesCatalogV1",
        "status": "pass",
        "publication_templates": list(PUBLICATION_TEMPLATES.values()),
        "slide_templates": list(SLIDE_TEMPLATES.values()),
        "poster_templates": list(POSTER_TEMPLATES.values()),
        "abstract_templates": list(ABSTRACT_TEMPLATES.values()),
    }


def _csv_to_markdown_table(csv_path: Path, max_rows: int = 12) -> tuple[str, list[dict[str, str]]]:
    """Read a CSV/TSV file and return a Markdown table string plus parsed row dicts."""
    delim = "\t" if csv_path.suffix.lower() == ".tsv" else ","
    rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delim)
        headers = list(reader.fieldnames or [])
        for idx, row in enumerate(reader):
            if idx >= max_rows:
                break
            rows.append({str(k): str(v or "").strip() for k, v in row.items() if k is not None})
    if not headers or not rows:
        return "_Tabela vazia / Empty table_", []
    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join("---" for _ in headers) + " |"
    body_lines = ["| " + " | ".join(str(r.get(h, "")).replace("|", "/") for h in headers) + " |" for r in rows]
    return "\n".join([header_line, sep_line, *body_lines]), rows


def harvest_analysis_outputs(project_dir: Path) -> dict[str, Any]:
    """Scan analysis/ and figures/ for R and Python outputs and sync analysis/results_ledger.json."""
    root = Path(project_dir).resolve()
    gate = scientific_execution_gate(root, "results-harvest", mark_started=True)
    if gate["status"] != "pass":
        return gate
    analysis_dir = root / "analysis"
    figures_dir = root / "figures"

    tables: list[dict[str, Any]] = []
    figures: list[dict[str, Any]] = []
    json_summaries: list[dict[str, Any]] = []
    merged_metrics: dict[str, Any] = {}
    metric_claims: dict[str, str] = {}
    issues: list[str] = []
    metric_sources: dict[str, list[dict[str, str]]] = {}

    def add_metric(key: str, value: Any, source: Path) -> None:
        try:
            if isinstance(value, bool):
                raise ValueError("Boolean is not a result")
            number = Decimal(str(value).replace(",", "."))
            if not number.is_finite():
                raise ValueError("Nonfinite result")
        except (InvalidOperation, ValueError):
            issues.append(f"Metric '{key}' is not a finite numeric result: {source.relative_to(root).as_posix()}")
            return
        if key in merged_metrics and Decimal(str(merged_metrics[key]).replace(",", ".")) != number:
            issues.append(f"Conflicting values for metric '{key}'; canonical ledger preserved.")
            return
        merged_metrics[key] = value
        if source != ledger_path:
            record = {
                "path": source.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
            if record not in metric_sources.setdefault(key, []):
                metric_sources[key].append(record)

    def add_claims(mapping: Any) -> None:
        if not isinstance(mapping, dict):
            issues.append("metric_claims must be an object.")
            return
        for key, claim in mapping.items():
            if not isinstance(claim, str) or not claim.strip():
                issues.append(f"Invalid claim binding for metric '{key}'.")
            elif key in metric_claims and metric_claims[key] != claim:
                issues.append(f"Conflicting claim bindings for metric '{key}'.")
            else:
                metric_claims[key] = claim

    def strict_json(path: Path) -> Any:
        def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("Duplicate JSON key")
                result[key] = value
            return result

        return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique)

    # 1. Existing results_ledger.json if present
    ledger_path = analysis_dir / "results_ledger.json"
    if ledger_path.is_file():
        try:
            existing = strict_json(ledger_path)
            if isinstance(existing, dict):
                historical = existing.get("metric_sources", {})
                if not isinstance(historical, dict):
                    issues.append("Metric source provenance must be an object.")
                else:
                    for key, sources in historical.items():
                        if not isinstance(sources, list):
                            issues.append(f"Invalid source provenance for '{key}'.")
                            continue
                        for record in sources:
                            if not isinstance(record, dict) or not isinstance(record.get("path"), str):
                                issues.append(f"Invalid source record for '{key}'.")
                                continue
                            source_path = root / record["path"]
                            if (
                                not source_path.resolve().is_relative_to(root)
                                or source_path.resolve() == ledger_path
                                or not source_path.is_file()
                                or hashlib.sha256(source_path.read_bytes()).hexdigest() != record.get("sha256")
                            ):
                                issues.append(
                                    f"Missing, changed or unsafe original source for '{key}'; ledger preserved."
                                )
                            else:
                                metric_sources.setdefault(key, []).append(record)
                add_claims(existing.get("metric_claims", {}))
                raw_m = existing.get("metrics", {})
                if isinstance(raw_m, dict):
                    for key, value in raw_m.items():
                        add_metric(str(key), value, ledger_path)
                else:
                    issues.append("Canonical metrics must be an object.")
            else:
                issues.append("Canonical ledger must be an object.")
        except (OSError, ValueError):
            issues.append("Canonical ledger is unreadable or ambiguous; preserved.")

    # 2. Scan analysis/ for JSON, CSV, TSV, and R/Python scripts
    r_scripts: list[str] = []
    if analysis_dir.is_dir():
        for path in sorted(analysis_dir.rglob("*")):
            if not path.is_file():
                continue
            if path == ledger_path or any(
                part in {".venv", "biblioteca", "node_modules", "__pycache__"} or part.startswith("backup")
                for part in path.relative_to(analysis_dir).parts
            ):
                continue
            rel = path.relative_to(root).as_posix()
            suf = path.suffix.lower()
            if suf == ".r":
                r_scripts.append(rel)
            elif suf in {".csv", ".tsv"}:
                md_table, parsed_rows = _csv_to_markdown_table(path)
                tables.append(
                    {
                        "name": path.stem,
                        "path": rel,
                        "row_count": len(parsed_rows),
                        "markdown": md_table,
                        "sample_rows": parsed_rows[:5],
                    }
                )
                # Extract key-value metrics if table has metric/value columns or single summary row
                if len(parsed_rows) == 1:
                    for k, v in parsed_rows[0].items():
                        if v:
                            try:
                                Decimal(str(v).replace(",", "."))
                            except InvalidOperation:
                                continue  # textual labels are table content, never numeric metrics
                            add_metric(f"{path.stem}.{k}", v, path)
                else:
                    for r in parsed_rows:
                        m_key = r.get("metric") or r.get("term") or r.get("outcome") or r.get("comparison")
                        m_val = r.get("estimate") or r.get("value") or r.get("pooled_effect") or r.get("auroc")
                        if m_key and m_val:
                            add_metric(f"{path.stem}.{m_key}", m_val, path)
            elif suf == ".json" and path.name != "results_ledger.json":
                try:
                    data = strict_json(path)
                    if isinstance(data, dict):
                        json_summaries.append({"name": path.stem, "path": rel, "data": data})
                        if isinstance(data.get("metric_claims"), dict):
                            add_claims(data["metric_claims"])
                        flat_source = data.get("metrics", data if path.stem.endswith("metrics") else {})
                        if isinstance(flat_source, dict):
                            for k, v in flat_source.items():
                                if isinstance(v, (int, float, str)) and not isinstance(v, bool):
                                    add_metric(str(k), v, path)
                except (OSError, ValueError):
                    issues.append(f"Unreadable or ambiguous JSON summary: {rel}")
            elif suf in {".png", ".svg", ".pdf"}:
                figures.append({"name": path.stem, "path": rel, "format": suf.lstrip(".")})

    # 3. Scan figures/ directory
    if figures_dir.is_dir():
        for path in sorted(figures_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".png", ".svg", ".pdf"}:
                rel = path.relative_to(root).as_posix()
                if not any(f["path"] == rel for f in figures):
                    figures.append({"name": path.stem, "path": rel, "format": path.suffix.lower().lstrip(".")})

    # 4. Also harvest PRISMA counts if present
    prisma_path = root / "evidence" / "prisma" / "prisma_flow_counts.json"
    prisma_data: dict[str, Any] = {}
    if prisma_path.is_file():
        prisma_data = load_structured_file(prisma_path)
        ident = prisma_data.get("identification", {})
        scr = prisma_data.get("screening", {})
        if ident.get("total_records_identified") is not None:
            add_metric("prisma_identified", ident["total_records_identified"], prisma_path)
        if ident.get("total_duplicates_removed") is not None:
            add_metric("prisma_duplicates_removed", ident["total_duplicates_removed"], prisma_path)
        if scr.get("records_screened") is not None:
            add_metric("prisma_records_screened", scr["records_screened"], prisma_path)

    if issues:
        return {
            "contract": "AnalysisHarvestV2",
            "status": "blocked",
            "issues": issues,
            "gate_eligible": False,
            "ledger_preserved": True,
        }

    # Save updated results_ledger.json if we harvested any metrics
    if merged_metrics:
        analysis_dir.mkdir(parents=True, exist_ok=True)
        save_structured_file(
            ledger_path,
            {
                "contract": "ResultsLedgerV1",
                "updated_at": datetime.now(UTC).isoformat(),
                "metrics": merged_metrics,
                "metric_claims": metric_claims,
                "metric_sources": metric_sources,
                "metrics_without_source_provenance": sorted(set(merged_metrics) - set(metric_sources)),
                "tables_harvested": [t["path"] for t in tables],
                "figures_harvested": [f["path"] for f in figures],
            },
        )

    return {
        "contract": "AnalysisHarvestV1",
        "status": "pass",
        "r_scripts": r_scripts,
        "tables": tables,
        "figures": figures,
        "json_summaries": json_summaries,
        "metrics": merged_metrics,
        "prisma": prisma_data,
        "ledger_path": "analysis/results_ledger.json" if merged_metrics else None,
    }


def _didactic_methodology_lesson(project_type: str) -> tuple[str, str, list[dict[str, str]]]:
    """Return (pt_lesson, en_lesson, flashcards) tailored to the project's scientific design."""
    ptype = (project_type or "").strip().lower()
    if ptype in {"systematic-review", "network-meta-analysis"}:
        pt_lesson = (
            "### Aula Didática: Como Funciona a Metodologia Estatística deste Estudo (Meta-Análise / NMA em R)\n\n"
            "1. **Por que usamos efeitos aleatórios com REML + Hartung-Knapp-Sidik-Jonkman "
            '(`test="knha"` no `metafor`)?**\n'
            "- O método tradicional de DerSimonian-Laird subestima a variância entre estudos "
            "($\\tau^2$) e infla o erro Tipo I "
            "(falsos positivos), especialmente quando o número de estudos ($k$) é pequeno ou moderado.\n"
            "- O estimador **REML** (Máxima Verossimilhança Restrita) combinado ao ajuste "
            "**HKSJ (`knha`)** usa a distribuição $t$ "
            "com graus de liberdade baseados em $k$, produzindo intervalos de confiança "
            "honestos e rigorosos exigidos pela Cochrane e BMJ.\n"
            "2. **Como interpretar $I^2$, $\\tau^2$ e o Intervalo de Predição de 95% (95% PI)?**\n"
            "- **$I^2$:** Proporção da variabilidade total que se deve à heterogeneidade "
            "verdadeira entre estudos e não ao erro amostral "
            "(não depende da escala, mas depende do tamanho amostral dos estudos).\n"
            "- **$\\tau^2$:** Variância verdadeira entre os efeitos reais dos estudos na escala "
            "da medida de efeito.\n"
            "- **Intervalo de Predição de 95% (95% PI):** Mostra a faixa onde o efeito "
            "verdadeiro de um **novo estudo futuro** "
            "provavelmente cairá. Mesmo quando o IC 95% médio exclui o efeito nulo, se o 95% PI "
            "cruzar o nulo, em alguns cenários clínicos "
            "o tratamento pode não ter benefício.\n"
            "3. **Se houver Meta-Análise em Rede (`netmeta`), o que são Transitividade, "
            "Inconsistência e P-score/SUCRA?**\n"
            "- **Transitividade:** Pressuposto clínico de que os estudos comparando A vs C e B "
            "vs C são semelhantes nos modificadores de efeito.\n"
            "- **Coerência / Inconsistência (`decomp.design` e `netsplit`):** Testa se a "
            "evidência direta concorda com a evidência indireta.\n"
            "- **P-score / SUCRA:** Probabilidade média de um tratamento ser superior aos "
            "demais. **Regra de ouro:** ranking alto não significa "
            "evidência forte — sempre interprete junto à certeza **GRADE**!\n"
        )
        en_lesson = (
            "### Didactic Lesson: How the Statistical Methodology of This Study Works (Meta-Analysis / NMA in R)\n\n"
            '1. **Why do we use Random-Effects REML + Hartung-Knapp-Sidik-Jonkman (`test="knha"` in `metafor`)?**\n'
            "- Classical DerSimonian-Laird underestimates between-study variance ($\\tau^2$) "
            "and inflates Type I error when $k$ is small.\n"
            "- **REML** paired with **HKSJ (`knha`)** uses a $t$-distribution calibrated to "
            "$k$, yielding honest confidence intervals "
            "required by Cochrane and top clinical journals.\n"
            "2. **How to interpret $I^2$, $\\tau^2$, and the 95% Prediction Interval (95% PI)?**\n"
            "- **$I^2$:** Percentage of total variability due to true between-study "
            "heterogeneity rather than sampling error.\n"
            "   - **$\\tau^2$:** True between-study variance on the effect-measure scale.\n"
            "- **95% Prediction Interval (95% PI):** The expected range of the true effect in a "
            "**new future study**.\n"
            "3. **In Network Meta-Analysis (`netmeta`), what are Transitivity, Inconsistency, and P-score/SUCRA?**\n"
            "   - **Transitivity:** Clinical exchangeability of effect modifiers across indirect comparisons.\n"
            "- **Inconsistency (`decomp.design` & `netsplit`):** Statistical agreement between "
            "direct and indirect evidence.\n"
            "- **P-score / SUCRA:** Ranking metric from 0 to 1; never interpret ranking in "
            "isolation from **GRADE** certainty!\n"
        )
        flashcards = [
            {
                "q_pt": "Por que vocês usaram REML com ajuste Hartung-Knapp (HKSJ) em vez de DerSimonian-Laird?",
                "a_pt": (
                    "Porque o DerSimonian-Laird gera intervalos de confiança artificialmente estreitos "
                    "quando há poucos estudos ou heterogeneidade moderada. O REML + HKSJ usa "
                    "distribuição t e protege contra falsos positivos, seguindo o Cochrane Handbook."
                ),
                "q_en": "Why did you use REML with Hartung-Knapp (HKSJ) adjustment instead of DerSimonian-Laird?",
                "a_en": (
                    "DerSimonian-Laird produces overly narrow confidence intervals under small k or "
                    "heterogeneity. REML + HKSJ uses a t-distribution and controls false-positive rates "
                    "in accordance with the Cochrane Handbook."
                ),
            },
            {
                "q_pt": (
                    "Qual a diferença prática entre o Intervalo de Confiança de 95% (IC 95%) e o "
                    "Intervalo de Predição de 95% (IP 95%)?"
                ),
                "a_pt": (
                    "O IC 95% mede a incerteza sobre a média global dos estudos existentes; já o IP 95% "
                    "incorpora a variância entre estudos (tau²) e mostra onde o efeito real cairá em "
                    "uma nova população ou hospital futuro."
                ),
                "q_en": (
                    "What is the practical difference between the 95% Confidence Interval and the 95% "
                    "Prediction Interval?"
                ),
                "a_en": (
                    "The 95% CI quantifies uncertainty around the grand mean effect, whereas the 95% PI "
                    "incorporates between-study variance (tau²) to predict the true effect range in a "
                    "future clinical setting."
                ),
            },
            {
                "q_pt": "Como foi evitada a perda de estudos ou viés de seleção na busca bibliográfica?",
                "a_pt": (
                    "Resposta depende dos logs do estudo. Verificar strings, datas e cobertura de PubMed, "
                    "Scopus, Embase, Cochrane "
                    "CENTRAL e LILACS segundo o PRISMA-S, com deduplicação determinística em 3 estágios "
                    "(DOI, PMID/PUI/EID e Título+Ano+Autor) que funde metadados sem descartar "
                    "informações."
                ),
                "q_en": "How did you prevent study loss or selection bias during the bibliographic search?",
                "a_en": (
                    "Answer requires this study's search logs. Verify queries, dates and coverage of "
                    "PubMed, Scopus, Embase, Cochrane "
                    "CENTRAL and LILACS where appropriate under PRISMA-S; audit recall and "
                    "deduplication."
                ),
            },
            {
                "q_pt": (
                    "Por que não testar viés de publicação com teste de Egger quando há menos de 10 estudos (k < 10)?"
                ),
                "a_pt": (
                    "Porque com k < 10 o poder estatístico da regressão de assimetria do funil é muito "
                    "baixo, não distinguindo acaso de assimetria real."
                ),
                "q_en": "Why avoid Egger's regression test for funnel plot asymmetry when k < 10?",
                "a_en": (
                    "With fewer than 10 studies, funnel plot regression has insufficient statistical "
                    "power to distinguish chance from true small-study effects."
                ),
            },
        ]
        return pt_lesson, en_lesson, flashcards

    if ptype == "prediction-model":
        pt_lesson = (
            "### Aula Didática: Como Funciona a Metodologia de Machine Learning Clínico deste "
            "Estudo (TRIPOD+AI / PROBAST+AI)\n\n"
            "1. **Prevenção de Vazamento de Dados (*Zero Patient-Level Leakage*):**\n"
            "- Múltiplas internações ou exames do mesmo paciente (`subject_id`) **jamais** "
            "podem ser divididos entre treino e teste. "
            "Toda imputação (`mice`/mediana), normalização e seleção de variáveis ocorre "
            "estritamente dentro das dobras de treino.\n"
            "2. **Discriminação (AUROC) vs. Calibração Logística (Intercepto e Slope):**\n"
            "- **AUROC** mede apenas ordenação (probabilidade de um paciente com evento ter "
            "escore maior que um sem evento). "
            "Um modelo pode ter AUROC de 0,90 e ainda assim superestimar o risco real em 3 vezes!\n"
            "- **Calibração (*Calibration-in-the-Large* = 0 e *Slope* = 1):** Garante que "
            "quando o modelo prevê 20% de risco de óbito ou necrose, "
            "exatamente ~20 em cada 100 pacientes semelhantes realmente apresentam o evento.\n"
            "3. **Curva de Decisão (DCA — *Net Benefit*) e Predição Conformal:**\n"
            "- **DCA (`dcurves`):** Avalia se usar o modelo para indicar cirurgia/UTI traz mais "
            "benefício líquido do que 'Tratar Todos' ou 'Tratar Nenhum' "
            "ao longo dos limiares de probabilidade clínica ($p_t$).\n"
            "- **Predição Conformal (*Split-Conformal*):** Fornece garantia matemática em "
            "amostra finita ($1 - \\alpha = 90\\%$) de cobertura e "
            "identifica casos incertos/ambíguos onde o médico deve solicitar exame adicional.\n"
        )
        en_lesson = (
            "### Didactic Lesson: How the Clinical Machine Learning Methodology Works (TRIPOD+AI / PROBAST+AI)\n\n"
            "1. **Zero Patient-Level Data Leakage:**\n"
            "- Repeated admissions or timepoints from the same patient (`subject_id`) are "
            "strictly grouped into the same partition. "
            "All imputation and scaling occur inside training folds only.\n"
            "2. **Discrimination (AUROC) vs. Logistic Calibration (Intercept & Slope):**\n"
            "- **AUROC** only measures rank-order separation. **Calibration** (target intercept "
            "= 0, slope = 1, Brier score) ensures "
            "predicted probabilities match observed clinical event rates.\n"
            "3. **Decision Curve Analysis (DCA Net Benefit) & Split-Conformal Prediction:**\n"
            "- **DCA** proves clinical utility over 'Treat All' and 'Treat None' across "
            "clinically plausible threshold probabilities ($p_t$).\n"
            "- **Split-Conformal Prediction** guarantees finite-sample coverage ($1 - \\alpha$) "
            "and flags ambiguous cases for human review.\n"
        )
        flashcards = [
            {
                "q_pt": (
                    "Por que reportar apenas AUROC e F1-score é insuficiente para publicar um modelo "
                    "clínico em revista Q1?"
                ),
                "a_pt": (
                    "Porque AUROC mede apenas discriminação (ranking) e F1 depende de um ponto de corte "
                    "arbitrário. Pelo TRIPOD+AI e PROBAST+AI, decisões médicas exigem probabilidades "
                    "calibradas (intercepto/slope/Brier) e demonstração de benefício líquido na Curva "
                    "de Decisão (DCA)."
                ),
                "q_en": "Why is reporting only AUROC and F1-score insufficient for Q1 clinical prediction journals?",
                "a_en": (
                    "AUROC only assesses rank discrimination and F1 uses an arbitrary threshold. "
                    "Assess probability calibration (intercept, slope, Brier) and clinical relevance "
                    "under TRIPOD+AI/PROBAST+AI; "
                    "use decision-curve analysis only with justified thresholds and an appropriate clinical decision."
                ),
            },
            {
                "q_pt": "Como vocês garantiram ausência de data leakage no pré-processamento e validação?",
                "a_pt": (
                    "Verificar nos manifests se os dados foram agrupados por paciente (patient_id) antes de qualquer "
                    "transformação, ajustando imputação e hiperparâmetros exclusivamente dentro das "
                    "partições de treino."
                ),
                "q_en": "How did you guarantee zero data leakage during preprocessing and validation?",
                "a_en": (
                    "Verify in partition manifests whether patients were separated before any transformation, "
                    "fitting imputation and hyperparameters strictly inside training folds."
                ),
            },
        ]
        return pt_lesson, en_lesson, flashcards

    pt_lesson = (
        "### Aula Didática: Metodologia Científica e Governança de Evidências deste Estudo\n\n"
        "- **Protocolo Congelado e Pré-Registrado:** Toda hipótese, estimando, critério de "
        "elegibilidade e plano analítico deve ser congelado e conferido "
        "com hash SHA-256 antes da extração/modelagem.\n"
        "- **Rastreabilidade Evidence Lock:** Cada afirmação factual no manuscrito e nos "
        "slides deve apontar para um `{{claim:id}}` validado; conferir cada ocorrência.\n"
    )
    en_lesson = (
        "### Didactic Lesson: Scientific Methodology & Evidence Governance of This Study\n\n"
        "- **Frozen Preregistered Protocol:** Every hypothesis, estimand, eligibility "
        "criterion and analysis plan must be locked and verified with SHA-256 "
        "prior to extraction or modeling.\n"
        "- **Evidence Lock Traceability:** Every factual assertion in manuscripts and "
        "slides must link to a verified `{{claim:id}}`; check each occurrence.\n"
    )
    flashcards = [
        {
            "q_pt": "Como a reprodutibilidade computacional e a integridade dos números foram garantidas?",
            "a_pt": (
                "É necessário auditar os outputs estatísticos do R/Python contra o "
                "analysis/results_ledger.json e verificar as versões em português e inglês; esta aula "
                "não executa essa revisão."
            ),
            "q_en": "How were computational reproducibility and numerical integrity guaranteed?",
            "a_en": (
                "R/Python statistical outputs require an audit against analysis/results_ledger.json "
                "and cross-checking across Portuguese and English deliverables; this lesson does not "
                "perform that review."
            ),
        }
    ]
    return pt_lesson, en_lesson, flashcards


def build_project_study_guide(project_dir: Path) -> dict[str, Any]:
    """Generate paired PT-BR/EN Markdown study guides and an interactive HTML5 Study & Defense Dashboard."""
    root = Path(project_dir).resolve()
    gate = scientific_execution_gate(root, "study-guide")
    if gate["status"] != "pass":
        return gate
    project = load_structured_file(root / "project.yaml")
    protocol = load_structured_file(root / "protocol.yaml")
    standards = load_structured_file(root / "standards.yaml")
    harvest = harvest_analysis_outputs(root)
    if harvest.get("status") != "pass":
        return harvest

    title = str(protocol.get("title") or project.get("name") or root.name)
    project_type = str(project.get("project_type") or protocol.get("project_type") or "systematic-review")
    current_mode = str(project.get("state", {}).get("current_mode") or "bootstrap")
    question = str(protocol.get("research_question") or "Pergunta de pesquisa em definição no protocol.yaml")
    reg = protocol.get("registration", {}) if isinstance(protocol.get("registration"), dict) else {}
    reg_label = f"{reg.get('registry') or 'Pendente'} ({reg.get('registry_id') or reg.get('status') or 'draft'})"
    guidelines = standards.get("primary_guidelines", [])

    pt_lesson, en_lesson, flashcards = _didactic_methodology_lesson(project_type)

    # Format harvested metrics & tables for study guide
    metrics = harvest["metrics"]
    metrics_lines_pt = [f"- **`{k}`:** `{v}`" for k, v in sorted(metrics.items())] or [
        "- _Nenhuma métrica numérica colhida ainda em `analysis/`._"
    ]
    metrics_lines_en = [f"- **`{k}`:** `{v}`" for k, v in sorted(metrics.items())] or [
        "- _No numerical metrics harvested yet in `analysis/`._"
    ]

    tables_section_pt = []
    tables_section_en = []
    for tbl in harvest["tables"]:
        tables_section_pt.append(f"#### Tabela R/Python: `{tbl['name']}` (`{tbl['path']}`)\n\n{tbl['markdown']}\n")
        tables_section_en.append(f"#### R/Python Table: `{tbl['name']}` (`{tbl['path']}`)\n\n{tbl['markdown']}\n")

    figures_lines = [f"- **{f['name']}** (`{f['path']}`)" for f in harvest["figures"]] or [
        "- _Nenhuma figura gerada ainda em `figures/` ou `analysis/`._"
    ]

    qa_md_pt = "\n\n".join(
        f"**Pergunta {i} (Banca / Revisor):** {fc['q_pt']}\n> **Resposta Técnica:** {fc['a_pt']}"
        for i, fc in enumerate(flashcards, start=1)
    )
    qa_md_en = "\n\n".join(
        f"**Question {i} (Defense / Reviewer):** {fc['q_en']}\n> **Technical Answer:** {fc['a_en']}"
        for i, fc in enumerate(flashcards, start=1)
    )

    study_root = root / "context" / "estudo_do_projeto"
    pt_dir = study_root / "portugues"
    en_dir = study_root / "ingles"
    pt_dir.mkdir(parents=True, exist_ok=True)
    en_dir.mkdir(parents=True, exist_ok=True)

    pt_md = (
        f"# Caderno de Estudo, Domínio Metodológico e Defesa: {title}\n\n"
        f"- **ID do Projeto:** `{root.name}`\n"
        f"- **Desenho Científico:** `{project_type}` | **Modo Atual:** `{current_mode}`\n"
        f"- **Registro do Protocolo:** `{reg_label}`\n"
        f"- **Diretrizes EQUATOR Aplicáveis:** {', '.join(guidelines) or 'PRISMA / TRIPOD / STROBE'}\n\n"
        f"## 1. Pergunta de Pesquisa e Racional Clínico\n\n"
        f"**Pergunta Central:** {question}\n\n"
        f"## 2. Domínio da Metodologia (Por que fizemos assim?)\n\n"
        f"{pt_lesson}\n"
        f"## 3. Leitura Guiada dos Resultados e Outputs do R / Python\n\n"
        f"### 3.1 Métricas Canônicas Colhidas (`analysis/results_ledger.json`)\n"
        + "\n".join(metrics_lines_pt)
        + "\n\n### 3.2 Tabelas Geradas pelos Scripts Analíticos\n\n"
        + (
            "\n".join(tables_section_pt)
            if tables_section_pt
            else "_Nenhuma tabela CSV/TSV encontrada em `analysis/`._\n"
        )
        + "\n### 3.3 Figuras e Gráficos Gerados\n"
        + "\n".join(figures_lines)
        + f"\n\n## 4. Simulador de Banca de Doutorado e Revisores Q1 (Flashcards Q&A)\n\n{qa_md_pt}\n"
    )

    en_md = (
        f"# Scientific Study, Methodological Mastery & Defense Guide: {title}\n\n"
        f"- **Project ID:** `{root.name}`\n"
        f"- **Study Design:** `{project_type}` | **Current Mode:** `{current_mode}`\n"
        f"- **Protocol Registration:** `{reg_label}`\n"
        f"- **Applicable EQUATOR Guidelines:** {', '.join(guidelines) or 'PRISMA / TRIPOD / STROBE'}\n\n"
        f"## 1. Research Question & Clinical Rationale\n\n"
        f"**Core Question:** {question}\n\n"
        f"## 2. Methodological Mastery (Why did we design it this way?)\n\n"
        f"{en_lesson}\n"
        f"## 3. Guided Interpretation of R / Python Outputs\n\n"
        f"### 3.1 Canonical Harvested Metrics (`analysis/results_ledger.json`)\n"
        + "\n".join(metrics_lines_en)
        + "\n\n### 3.2 Tables Generated by Analytical Scripts\n\n"
        + ("\n".join(tables_section_en) if tables_section_en else "_No CSV/TSV tables found in `analysis/` yet._\n")
        + "\n### 3.3 Generated Figures & Plots\n"
        + "\n".join(figures_lines)
        + f"\n\n## 4. Doctoral Defense & Q1 Peer-Review Q&A Flashcards\n\n{qa_md_en}\n"
    )

    pt_path = pt_dir / "caderno_de_estudo_e_defesa.md"
    en_path = en_dir / "caderno_de_estudo_e_defesa.md"
    pt_path.write_text(pt_md, encoding="utf-8")
    en_path.write_text(en_md, encoding="utf-8")

    # Build Interactive HTML5 Study & Flashcards Dashboard
    flashcards_html = "".join(
        f"""
        <div class="flashcard" onclick="this.classList.toggle('flipped')">
          <div class="fc-q"><strong>Q{i} (PT):</strong> {html.escape(fc["q_pt"])}<br><small><em>EN:
          {html.escape(fc["q_en"])}</em></small></div>
          <div class="fc-a"><strong>Resposta (PT):</strong> {html.escape(fc["a_pt"])}<hr><small><strong>Answer
          (EN):</strong> {html.escape(fc["a_en"])}</small></div>
        </div>
        """
        for i, fc in enumerate(flashcards, start=1)
    )
    metrics_rows_html = (
        "".join(
            f"<tr><td><code>{html.escape(str(k))}</code></td><td><strong>{html.escape(str(v))}</strong></td></tr>"
            for k, v in sorted(metrics.items())
        )
        or "<tr><td colspan='2'>Execute os scripts em analysis/ para popular as métricas.</td></tr>"
    )

    html_dashboard = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Painel de Estudo e Defesa — {html.escape(title)}</title>
  <style>
    :root {{ --bg: #0f172a; --card: #1e293b; --accent: #38bdf8; --text: #f8fafc; --muted: #94a3b8; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0;
    padding: 32px; line-height: 1.6; }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header {{ background: linear-gradient(135deg, #1e3a8a, #0f172a); padding: 28px; border-radius: 16px; border:
    1px solid #334155; margin-bottom: 24px; }}
    .badge {{ display: inline-block; background: rgba(56, 189, 248, 0.15); color: var(--accent); padding: 4px 12px;
    border-radius: 999px; font-size: 0.85rem; margin-right: 8px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
    .card {{ background: var(--card); padding: 22px; border-radius: 14px; border: 1px solid #334155; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #334155; }}
    .flashcard {{ background: #0f172a; border: 1px solid var(--accent); border-radius: 12px; padding: 16px;
    margin-bottom: 14px; cursor: pointer; transition: transform 0.15s; }}
    .flashcard:hover {{ transform: translateY(-2px); }}
    .fc-a {{ margin-top: 12px; padding-top: 12px; border-top: 1px dashed #334155; color: #bae6fd; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="badge">Projeto: {html.escape(root.name)}</span>
      <span class="badge">Desenho: {html.escape(project_type)}</span>
      <span class="badge">Modo: {html.escape(current_mode)}</span>
      <span class="badge">Registro: {html.escape(reg_label)}</span>
      <h1>{html.escape(title)}</h1>
      <p><strong>Pergunta Central:</strong> {html.escape(question)}</p>
    </div>
    <div class="grid">
      <div class="card">
        <h2>Métricas Canônicas Colhidas do R / Python</h2>
        <table>
          <thead><tr><th>Métrica / Estimativa</th><th>Valor Canônico</th></tr></thead>
          <tbody>{metrics_rows_html}</tbody>
        </table>
      </div>
      <div class="card">
        <h2>Arquivos Analíticos e Figuras do Projeto</h2>
        <p><strong>Scripts R:</strong> {len(harvest["r_scripts"])} | <strong>Tabelas:</strong>
        {len(harvest["tables"])} | <strong>Figuras:</strong> {len(harvest["figures"])}</p>
        <ul>
          {
        "".join(
            f"<li>Tabela: <code>{html.escape(t['path'])}</code> ({t['row_count']} linhas)</li>"
            for t in harvest["tables"]
        )
    }
          {"".join(f"<li>Figura: <code>{html.escape(f['path'])}</code></li>" for f in harvest["figures"])}
        </ul>
      </div>
    </div>
    <div class="card">
      <h2>Simulador de Banca e Revisores (Flashcards Bilíngues PT-BR / EN)</h2>
      {flashcards_html}
    </div>
  </div>
</body>
</html>
"""
    html_path = study_root / "painel_estudo_interativo.html"
    html_path.write_text(html_dashboard, encoding="utf-8")

    return {
        "contract": "ProjectStudyGuideV1",
        "status": "pass",
        "project_id": root.name,
        "project_type": project_type,
        "harvest_summary": {
            "metrics_count": len(metrics),
            "tables_count": len(harvest["tables"]),
            "figures_count": len(harvest["figures"]),
        },
        "study_guides": {
            "portugues": pt_path.relative_to(root).as_posix(),
            "ingles": en_path.relative_to(root).as_posix(),
            "interactive_html": html_path.relative_to(root).as_posix(),
        },
    }


def synthesize_from_r_outputs(
    project_dir: Path,
    *,
    publication_template_id: str = "jama-lancet-nejm-high-impact",
    slide_template_id: str = "congresso-cirurgico-oral-10min",
    poster_template_id: str = "eposter-digital-16x9-congresso",
    slug: str = "pacote-completo-r",
) -> dict[str, Any]:
    """Generate complete paired PT-BR/EN manuscripts, abstracts, slides, and posters from R outputs."""
    root = Path(project_dir).resolve()
    gate = scientific_execution_gate(root, "scientific-synthesis")
    if gate["status"] != "pass":
        return gate
    from ..evidence import validate_evidence_lock

    evidence = validate_evidence_lock(root)
    if evidence.get("gate_eligible") is not True:
        return {
            "contract": "ROutputBilingualSynthesisV2",
            "status": "blocked",
            "issues": ["Evidence Lock must approve canonical claims before scientific synthesis."],
            "evidence_issues": evidence.get("issues", []),
            "submission_eligible": False,
        }
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", slug):
        return {"status": "blocked", "issues": ["Synthesis slug must be a simple project-local identifier."]}
    destinations = [root / "drafts" / lang / slug for lang in ("portugues", "ingles")]
    destinations.append(root / "deliverables" / slug)
    if any(path.exists() for path in destinations):
        return {
            "status": "blocked",
            "issues": ["Version already exists; choose a new slug. Earlier artifacts preserved."],
        }
    project = load_structured_file(root / "project.yaml")
    protocol = load_structured_file(root / "protocol.yaml")
    harvest = harvest_analysis_outputs(root)
    if harvest.get("status") != "pass":
        return harvest

    pub_tpl = (
        PUBLICATION_TEMPLATES.get(publication_template_id) or PUBLICATION_TEMPLATES["jama-lancet-nejm-high-impact"]
    )
    slide_tpl = SLIDE_TEMPLATES.get(slide_template_id) or SLIDE_TEMPLATES["congresso-cirurgico-oral-10min"]
    poster_tpl = POSTER_TEMPLATES.get(poster_template_id) or POSTER_TEMPLATES["eposter-digital-16x9-congresso"]

    title = str(protocol.get("title") or project.get("name") or root.name)
    project_type = str(project.get("project_type") or protocol.get("project_type") or "systematic-review")
    question = str(protocol.get("research_question") or "Investigação clínica baseada em protocolo registrado.")
    reg = protocol.get("registration", {}) if isinstance(protocol.get("registration"), dict) else {}
    reg_id = str(reg.get("registry_id") or reg.get("status") or "PROSPERO/OSF")
    reg_name = str(reg.get("registry") or "OSF/PROSPERO")

    # Collect approved claims if present
    claims_path = root / "evidence" / "claim_map.jsonl"
    claims: list[dict[str, Any]] = []
    if claims_path.is_file():
        for line in claims_path.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                try:
                    c = json.loads(line)
                    if (
                        isinstance(c, dict)
                        and c.get("claim_id") in evidence.get("claims_checked", [])
                        and c.get("status") == "supported"
                    ):
                        claims.append(c)
                except json.JSONDecodeError:
                    pass

    if not claims:
        return {
            "contract": "ROutputBilingualSynthesisV2",
            "status": "blocked",
            "issues": ["No supported claim_id is available for synthesis."],
            "submission_eligible": False,
        }
    claim_tag = f"{{{{claim:{claims[0]['claim_id']}}}}}"
    metrics = harvest["metrics"]
    ledger = load_structured_file(root / "analysis" / "results_ledger.json")
    if ledger.get("metrics_without_source_provenance"):
        return {
            "contract": "BilingualSynthesisV2",
            "status": "blocked",
            "issues": ["Canonical results lack original output provenance; verify sources before drafting."],
        }
    metric_claims = ledger.get("metric_claims", {})
    unsupported = [key for key in metrics if metric_claims.get(key) not in evidence.get("claims_checked", [])]
    if not metrics or unsupported:
        return {
            "contract": "ROutputBilingualSynthesisV2",
            "status": "blocked",
            "submission_eligible": False,
            "issues": ["Each canonical result must link to a validated claim_id via metric_claims."],
            "unbound_metrics": unsupported,
        }
    metrics_bullet_pt = "\n".join(
        f"- **{k}:** {{{{metric:{k}}}}} {str(v).replace('.', ',')} {{{{claim:{metric_claims[k]}}}}}"
        for k, v in sorted(metrics.items())
    ) or ("- Métricas aguardando execução de scripts em `analysis/`.")
    metrics_bullet_en = "\n".join(
        f"- **{k}:** {{{{metric:{k}}}}} {v} {{{{claim:{metric_claims[k]}}}}}" for k, v in sorted(metrics.items())
    ) or ("- Metrics awaiting script execution in `analysis/`.")

    tables_md_pt = (
        "\n\n".join(f"### Tabela: {t['name']} (Fonte: `{t['path']}`)\n\n{t['markdown']}" for t in harvest["tables"])
        or "_Nenhuma tabela CSV/TSV colhida ainda._"
    )
    tables_md_en = (
        "\n\n".join(f"### Table: {t['name']} (Source: `{t['path']}`)\n\n{t['markdown']}" for t in harvest["tables"])
        or "_No CSV/TSV tables harvested yet._"
    )

    figs_md_pt = "\n".join(
        f"- Figura `{f['name']}`: ![{f['name']}](../../../{f['path']})" for f in harvest["figures"]
    ) or ("- _Nenhuma figura colhida ainda em `figures/` ou `analysis/`._")
    figs_md_en = "\n".join(
        f"- Figure `{f['name']}`: ![{f['name']}](../../../{f['path']})" for f in harvest["figures"]
    ) or ("- _No figures harvested yet in `figures/` or `analysis/`._")

    # 1. Paired Manuscripts (PT-BR & EN)
    drafts_pt_dir = root / "drafts" / "portugues" / slug
    drafts_en_dir = root / "drafts" / "ingles" / slug
    drafts_pt_dir.mkdir(parents=True, exist_ok=True)
    drafts_en_dir.mkdir(parents=True, exist_ok=True)

    sec_pt = "\n\n".join(f"## {s}\n" for s in pub_tpl["sections_pt"])
    sec_en = "\n\n".join(f"## {s}\n" for s in pub_tpl["sections_en"])

    manuscript_pt = (
        f"# {title}\n\n"
        f"**Template Editorial:** {pub_tpl['name_pt']}  \n"
        f"**Desenho:** `{project_type}` | **Registro do Protocolo:** {reg_name} (`{reg_id}`)\n\n"
        f"## Síntese Quantitativa Colhida do R / Python (`analysis/results_ledger.json`)\n\n"
        f"Pergunta de pesquisa: {question} {claim_tag}\n\n"
        f"{metrics_bullet_pt}\n\n"
        f"{sec_pt}\n"
        f"## Tabelas Integradas dos Outputs em R\n\n{tables_md_pt}\n\n"
        f"## Figuras Geradas pelos Scripts em R\n\n{figs_md_pt}\n\n"
        f"## Uso de Inteligência Artificial e Tecnologias Assistidas por IA na Redação Científica\n\n"
        "RASCUNHO AUTOMÁTICO — Durante a preparação deste trabalho, os autores utilizaram Claude Opus 5.5 "
        "(Anthropic) para auxiliar no polimento do idioma inglês, refinamento gramatical, correções tipográficas "
        "e formatação do layout de tabelas. Após o uso desta ferramenta, os autores revisaram criticamente, "
        "verificaram e editaram todo o conteúdo gerado e assumem total responsabilidade pela integridade científica, "
        "precisão factual e conclusões apresentadas neste manuscrito. Em conformidade com os critérios de autoria "
        "da revista-alvo, tecnologias de IA generativa não são listadas como autores.\n"
    )

    manuscript_en = (
        f"# {title}\n\n"
        f"**Editorial Template:** {pub_tpl['name_en']}  \n"
        f"**Study Design:** `{project_type}` | **Protocol Registration:** {reg_name} (`{reg_id}`)\n\n"
        f"## Quantitative Synthesis Harvested from R / Python (`analysis/results_ledger.json`)\n\n"
        f"Research question: {question} {claim_tag}\n\n"
        f"{metrics_bullet_en}\n\n"
        f"{sec_en}\n"
        f"## Integrated R Output Tables\n\n{tables_md_en}\n\n"
        f"## Figures Generated by R Scripts\n\n{figs_md_en}\n\n"
        f"## Use of Artificial Intelligence and AI-Assisted Technologies in Scientific Writing\n\n"
        "AUTOMATED DRAFT — During the preparation of this work, the authors used Claude Opus 5.5 (Anthropic) "
        "to assist with English language polishing, grammatical refinement, typographical corrections, and table "
        "layout formatting. Following the use of this tool, the authors critically reviewed, verified, and edited "
        "all generated content and take full responsibility for the scientific integrity, factual accuracy, and "
        "conclusions presented in this manuscript. In accordance with target journal authorship criteria, generative "
        "AI technologies are not listed as authors.\n"
    )

    ms_pt_path = drafts_pt_dir / "manuscrito_completo.md"
    ms_en_path = drafts_en_dir / "manuscrito_completo.md"
    ms_pt_path.write_text(manuscript_pt, encoding="utf-8")
    ms_en_path.write_text(manuscript_en, encoding="utf-8")

    # 2. Paired Multi-Template Abstracts Pack (PT-BR & EN)
    inline_metrics_pt = (
        "; ".join(f"{k}: {str(v).replace('.', ',')}" for k, v in sorted(metrics.items())) or "análise em execução"
    )
    inline_metrics_en = "; ".join(f"{k}: {v}" for k, v in sorted(metrics.items())) or "analysis in progress"

    abstracts_pt = (
        f"# Pacote de Resumos Estruturados Bilíngues (Integrados aos Outputs do R): {title}\n\n"
        f"## 1. Resumo de Periódico Q1 (300–350 palavras)\n"
        f"- **Introdução/Importância:** {question}\n"
        "- **Objetivo:** Avaliar quantitativamente os desfechos clínicos segundo protocolo "
        f"pré-registrado ({reg_name}: `{reg_id}`).\n"
        f"- **Métodos:** Estudo do tipo `{project_type}` a documentar com a checklist aplicável "
        "EQUATOR e versões comprovadas nos logs de execução.\n"
        f"- **Resultados:** Síntese dos outputs analíticos: {inline_metrics_pt}. {claim_tag}\n"
        f"- **Conclusão:** [PENDENTE: interpretar apenas achados verificados, incerteza e "
        f"limitações; não presumir utilidade clínica.]\n"
        f"- **Registro:** {reg_name} `{reg_id}`.\n\n"
        f"## 2. Roteiro de Visual / Graphical Abstract (3 Painéis)\n"
        f"- **Painel 1 (População & Pergunta):** {question}\n"
        f"- **Painel 2 (Metodologia & R Engine):** `{project_type}` | Registro `{reg_id}`\n"
        f"- **Painel 3 (Achado Quantitativo Principal):** {inline_metrics_pt}\n"
    )

    abstracts_en = (
        f"# Bilingual Structured Abstracts Pack (Integrated with R Outputs): {title}\n\n"
        f"## 1. Q1 Journal Structured Abstract (300–350 words)\n"
        f"- **Background/Importance:** {question}\n"
        "- **Objective:** To quantitatively evaluate clinical outcomes under a "
        f"preregistered protocol ({reg_name}: `{reg_id}`).\n"
        f"- **Methods:** `{project_type}` requiring the applicable reporting checklist "
        "and software versions established from execution logs.\n"
        f"- **Results:** Quantitative synthesis from R outputs: {inline_metrics_en}. {claim_tag}\n"
        "- **Conclusions:** [PENDING: interpret verified findings, uncertainty and limitations; do not presume "
        "clinical utility.]\n"
        f"- **Registration:** {reg_name} `{reg_id}`.\n\n"
        f"## 2. Visual / Graphical Abstract Blueprint (3 Panels)\n"
        f"- **Panel 1 (Population & Question):** {question}\n"
        f"- **Panel 2 (Methods & R Engine):** `{project_type}` | Registry `{reg_id}`\n"
        f"- **Panel 3 (Primary Quantitative Finding):** {inline_metrics_en}\n"
    )

    abs_pt_path = drafts_pt_dir / "resumos_estruturados.md"
    abs_en_path = drafts_en_dir / "resumos_estruturados.md"
    abs_pt_path.write_text(abstracts_pt, encoding="utf-8")
    abs_en_path.write_text(abstracts_en, encoding="utf-8")

    # Congress artifacts require the dedicated requirements/storyboard/QA pipeline.
    # This synthesis route produces journal drafts only; it cannot bypass that pipeline.
    routing = {}
    for language, message in {
        "portugues": (
            "# Encaminhamento para congresso\n\n"
            "Não foram gerados slides, pôster ou resumo de congresso nesta rota. "
            "Importar as regras oficiais do evento com `article-machine congress import`; "
            "depois executar `deck/poster plan`, `build`, `qa` e `export`. "
            "Somente claims validados podem entrar no storyboard. "
            "Submissão exige confirmação explícita e snapshot recente do portal.\n"
        ),
        "ingles": (
            "# Conference routing\n\n"
            "No slides, poster or conference abstract were generated by this route. "
            "Import official event requirements with `article-machine congress import`; "
            "then run `deck/poster plan`, `build`, `qa` and `export`. "
            "Only validated claims may enter the storyboard. "
            "Submission requires explicit confirmation and a fresh portal snapshot.\n"
        ),
    }.items():
        target = (drafts_pt_dir if language == "portugues" else drafts_en_dir) / "encaminhamento_congresso.md"
        target.write_text(message, encoding="utf-8")
        routing[language] = target.relative_to(root).as_posix()

    # Also build/refresh the project study guide automatically so the user can always study the latest outputs!
    study_report = build_project_study_guide(root)

    return {
        "contract": "ROutputBilingualSynthesisV2",
        "status": "pass",
        "artifact_state": "draft-unreviewed",
        "submission_eligible": False,
        "human_review_verified": False,
        "project_id": root.name,
        "templates_used": {
            "publication": pub_tpl["id"],
            "slides": slide_tpl["id"],
            "poster": poster_tpl["id"],
        },
        "harvested_counts": {
            "metrics": len(metrics),
            "tables": len(harvest["tables"]),
            "figures": len(harvest["figures"]),
        },
        "manuscripts": {
            "portugues": ms_pt_path.relative_to(root).as_posix(),
            "ingles": ms_en_path.relative_to(root).as_posix(),
        },
        "abstracts": {
            "portugues": abs_pt_path.relative_to(root).as_posix(),
            "ingles": abs_en_path.relative_to(root).as_posix(),
        },
        "conference_outputs": {
            "status": "not-generated-dedicated-pipeline-required",
            "routing_guides": routing,
            "submission_eligible": False,
        },
        "study_guide": study_report["study_guides"],
    }


def _render_bilingual_slides_html(
    *,
    lang: str,
    title: str,
    question: str,
    project_type: str,
    reg_label: str,
    template_name: str,
    metrics: dict[str, Any],
    table_html: str,
    figs_html: str,
) -> str:
    is_pt = lang.startswith("pt")
    lbl_q = "Pergunta de Pesquisa e Racional Clínico" if is_pt else "Research Question & Clinical Rationale"
    lbl_m = "Metodologia Científica e Ambiente R 4.6.1" if is_pt else "Scientific Methodology & R 4.6.1 Engine"
    lbl_r = "Resultados Quantitativos (Outputs do R)" if is_pt else "Quantitative Results (R Outputs)"
    lbl_f = "Tabelas e Figuras Geradas no R" if is_pt else "R-Generated Tables & Figures"
    lbl_c = "Conclusões, Limitações e Impacto Clínico" if is_pt else "Conclusions, Limitations & Clinical Impact"

    metrics_cards = (
        "".join(
            f"<div class='kpi'><span>{html.escape(str(k))}</span>"
            f"<strong>{html.escape(str(v).replace('.', ',') if is_pt else str(v))}</strong></div>"
            for k, v in list(sorted(metrics.items()))[:6]
        )
        or "<div class='kpi'><span>Status</span><strong>Aguardando Outputs R</strong></div>"
    )

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)} — Slides ({lang})</title>
  <style>
    body {{ margin: 0; background: #0b1120; color: #f8fafc; font-family: 'Segoe UI', system-ui, sans-serif; }}
    .slide {{ width: 1280px; height: 720px; margin: 24px auto; padding: 48px 56px; box-sizing: border-box;
    background: linear-gradient(145deg, #0f172a, #1e293b); border: 1px solid #334155; border-radius: 18px; display:
    flex; flex-direction: column; justify-content: space-between; page-break-after: always; }}
    .top-bar {{ display: flex; justify-content: space-between; color: #38bdf8; font-size: 0.95rem; font-weight:
    600; text-transform: uppercase; letter-spacing: 0.06em; }}
    h1 {{ font-size: 2.4rem; margin: 16px 0; line-height: 1.25; }}
    h2 {{ font-size: 1.85rem; color: #e2e8f0; margin: 8px 0 16px; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin: 18px 0; }}
    .kpi {{ background: rgba(15, 23, 42, 0.75); border: 1px solid #38bdf8; border-radius: 14px; padding: 18px; }}
    .kpi span {{ display: block; color: #94a3b8; font-size: 0.9rem; }}
    .kpi strong {{ font-size: 1.6rem; color: #f8fafc; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    th, td {{ border-bottom: 1px solid #334155; padding: 8px 10px; text-align: left; }}
    .fig-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .fig-box {{ background: #0f172a; border: 1px dashed #475569; padding: 14px; border-radius: 10px; }}
    .footer {{ color: #64748b; font-size: 0.85rem; display: flex; justify-content: space-between; }}
  </style>
</head>
<body>
  <section class="slide">
    <div class="top-bar"><span>{html.escape(template_name)}</span><span>{html.escape(reg_label)}</span></div>
    <div>
      <h1>{html.escape(title)}</h1>
      <p style="font-size:1.25rem;color:#cbd5e1;">{html.escape(question)}</p>
    </div>
    <div class="footer"><span>Desenho / Design: {html.escape(project_type)}</span><span>Slide 1 / 5</span></div>
  </section>
  <section class="slide">
    <div class="top-bar"><span>{lbl_q}</span><span>{html.escape(reg_label)}</span></div>
    <div>
      <h2>{lbl_m}</h2>
      <p style="font-size:1.15rem;line-height:1.6;">{html.escape(question)}</p>
      <ul>
        <li>Protocolo prospectivo travado por SHA-256 ({html.escape(reg_label)})</li>
        <li>Pipeline estatístico reprodutível em R 4.6.1 (<code>renv.lock</code>) e Python 3.13</li>
        <li>Rastreabilidade integral por <code>Evidence Lock</code> e paridade numérica PT-BR / EN</li>
      </ul>
    </div>
    <div class="footer"><span>{html.escape(title)}</span><span>Slide 2 / 5</span></div>
  </section>
  <section class="slide">
    <div class="top-bar"><span>{lbl_r}</span><span>analysis/results_ledger.json</span></div>
    <div>
      <h2>{lbl_r}</h2>
      <div class="kpi-grid">{metrics_cards}</div>
    </div>
    <div class="footer"><span>{html.escape(title)}</span><span>Slide 3 / 5</span></div>
  </section>
  <section class="slide">
    <div class="top-bar"><span>{lbl_f}</span><span>R 4.6.1 Outputs</span></div>
    <div>
      <h2>{lbl_f}</h2>
      {table_html}
      <div class="fig-grid" style="margin-top:16px;">{figs_html}</div>
    </div>
    <div class="footer"><span>{html.escape(title)}</span><span>Slide 4 / 5</span></div>
  </section>
  <section class="slide">
    <div class="top-bar"><span>{lbl_c}</span><span>Evidence Lock Verified</span></div>
    <div>
      <h2>{lbl_c}</h2>
      <ul>
        <li>Estimativas quantitativas integradas diretamente dos scripts analíticos em R.</li>
        <li>Interpretação calibrada pela certeza da evidência (GRADE / PROBAST+AI / TRIPOD+AI).</li>
      </ul>
    </div>
    <div class="footer"><span>{html.escape(title)}</span><span>Slide 5 / 5</span></div>
  </section>
</body>
</html>
"""


def _render_bilingual_poster_html(
    *,
    lang: str,
    title: str,
    question: str,
    project_type: str,
    reg_label: str,
    template_name: str,
    metrics: dict[str, Any],
    table_html: str,
    figs_html: str,
) -> str:
    is_pt = lang.startswith("pt")
    sec1 = "1. Introdução e Pergunta Clínica" if is_pt else "1. Background & Clinical Question"
    sec2 = "2. Métodos e Governança (R 4.6.1)" if is_pt else "2. Methods & Governance (R 4.6.1)"
    sec3 = "3. Resultados Quantitativos (R Outputs)" if is_pt else "3. Quantitative Results (R Outputs)"
    sec4 = "4. Tabelas, Figuras e Conclusão" if is_pt else "4. Tables, Figures & Conclusion"

    metrics_list = (
        "".join(
            f"<li><strong>{html.escape(str(k))}:</strong> "
            f"{html.escape(str(v).replace('.', ',') if is_pt else str(v))}</li>"
            for k, v in sorted(metrics.items())
        )
        or "<li>Aguardando execução de scripts em <code>analysis/</code></li>"
    )

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)} — Poster ({lang})</title>
  <style>
    body {{ margin: 0; background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', system-ui, sans-serif; }}
    .poster {{ width: 1920px; min-height: 1080px; margin: 0 auto; padding: 36px; box-sizing: border-box; display:
    flex; flex-direction: column; gap: 24px; }}
    .banner {{ background: linear-gradient(135deg, #1e3a8a, #0f172a); padding: 28px 36px; border-radius: 16px;
    border: 1px solid #38bdf8; display: flex; justify-content: space-between; align-items: center; }}
    .cols {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; flex: 1; }}
    .panel {{ background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 22px; }}
    h1 {{ margin: 0 0 8px; font-size: 2.1rem; }}
    h2 {{ margin: 0 0 12px; color: #38bdf8; font-size: 1.35rem; border-bottom: 1px solid #334155; padding-bottom:
    8px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-top: 10px; }}
    th, td {{ border-bottom: 1px solid #334155; padding: 6px 8px; text-align: left; }}
    .fig-box {{ background: #0f172a; border: 1px dashed #475569; padding: 12px; border-radius: 8px; margin-top: 10px; }}
  </style>
</head>
<body>
  <div class="poster">
    <header class="banner">
      <div>
        <h1>{html.escape(title)}</h1>
        <div>{html.escape(template_name)} | Desenho / Design: <code>{html.escape(project_type)}</code> | Registro:
        <code>{html.escape(reg_label)}</code></div>
      </div>
      <div style="text-align:right;font-size:0.95rem;color:#bae6fd;">Article Machine — Reproducible R 4.6.1
      Synthesis</div>
    </header>
    <div class="cols">
      <div class="panel">
        <h2>{sec1}</h2>
        <p>{html.escape(question)}</p>
        <h2>{sec2}</h2>
        <ul>
          <li>Protocolo congelado ({html.escape(reg_label)})</li>
          <li>Ambiente R 4.6.1 travado via <code>renv.lock</code></li>
          <li>Deduplicação determinística PRISMA-S e validação de extração</li>
        </ul>
      </div>
      <div class="panel">
        <h2>{sec3}</h2>
        <ul>{metrics_list}</ul>
        {table_html}
      </div>
      <div class="panel">
        <h2>{sec4}</h2>
        {figs_html}
      </div>
    </div>
  </div>
</body>
</html>
"""
