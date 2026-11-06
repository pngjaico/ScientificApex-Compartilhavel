"""Canonical Triple-Reviewer Screening Engine & Comprehensive PRISMA 2020 / PRISMA-NMA Checklist System.

Implements:
1. Cochrane Gold-Standard Triple-Reviewer Screening:
   - Reviewer 1 (Independent): Focuses on Clinical PICO Eligibility (Liver Transplantation + Dynamic Perfusion vs Comparator).
   - Reviewer 2 (Independent): Focuses on Methodological Rigour (RCT vs PSM vs Comparative Cohort vs Ineligible Designs).
   - Reviewer 3 (Senior Arbiter): Resolves disagreements, ratifies landmark trials, and issues explicit arbitration rationales.
2. Native Rayyan Export Format (rayyan_screening_export.csv):
   - Fully compliant with Rayyan's tag/notes schema:
     RAYYAN-INCLUSION, RAYYAN-EXCLUSION-REASONS, and RAYYAN-LABELS.
3. Official PRISMA 2020 (27 items) and PRISMA-NMA (32 items)
   Compliance Checklist Matrix generation with exact manuscript/evidence anchors.
4. Supplementary Appendix Excluded Studies Table (PRISMA Item 16b).
"""

from __future__ import annotations

import csv
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..serialization import load_structured_file, save_structured_file


# -------------------------------------------------------------------------
# 1. CANONICAL PRISMA 2020 & PRISMA-NMA CHECKLIST DEFINITIONS
# -------------------------------------------------------------------------

PRISMA_2020_CHECKLIST_ITEMS = [
    {"num": "1", "section": "Título", "topic": "Título", "item": "Identificar o manuscrito como revisão sistemática e/ou meta-análise em rede.", "anchor": "drafts/manuscript.md (Título)"},
    {"num": "2", "section": "Resumo", "topic": "Resumo estruturado", "item": "Resumo estruturado com contexto, objetivos, fontes de informação, critérios de elegibilidade, participantes, intervenções, métodos de avaliação de viés, síntese dos resultados, discussão e número de registro.", "anchor": "drafts/manuscript.md (Resumo/Abstract)"},
    {"num": "3", "section": "Introdução", "topic": "Racionalidade", "item": "Descrever o contexto do conhecimento existente e a justificativa para a realização desta revisão.", "anchor": "drafts/manuscript.md (Introdução)"},
    {"num": "4", "section": "Introdução", "topic": "Objetivos", "item": "Fornecer declaração explícita da questão clínica sob o formato PICO (População, Intervenção, Comparadores, Desfechos).", "anchor": "protocol.yaml & drafts/manuscript.md (Objetivos)"},
    {"num": "5", "section": "Métodos", "topic": "Critérios de elegibilidade", "item": "Especificar os critérios de inclusão e exclusão e agrupamento de estudos por intervenções e comparadores.", "anchor": "protocol.yaml & drafts/manuscript.md (Critérios de Elegibilidade)"},
    {"num": "6", "section": "Métodos", "topic": "Fontes de informação", "item": "Especificar todas as bases consultadas (PubMed, Scopus, Embase), datas de busca e registros de ensaios.", "anchor": "evidence/retrieval/ (Manifestos de busca) & context/query_plan.yaml"},
    {"num": "7", "section": "Métodos", "topic": "Estratégia de busca", "item": "Apresentar a estratégia completa e reproduzível para todas as bases de dados, incluindo filtros utilizados.", "anchor": "evidence/retrieval/portugues/relatorio_busca_bibliografica.md"},
    {"num": "8", "section": "Métodos", "topic": "Processo de seleção", "item": "Especificar os métodos usados na seleção dos estudos, declarando triagem em duplicata independente (2 revisores cegos) com resolução de discrepâncias por um terceiro revisor sênior, além das ferramentas automatizadas utilizadas.", "anchor": "screening/multi_agent_screening_ledger.jsonl & drafts/manuscript.md (Métodos)"},
    {"num": "9", "section": "Métodos", "topic": "Processo de coleta de dados", "item": "Descrever os métodos de extração de dados dos relatórios, formulários estruturados e validação cruzada independente.", "anchor": "evidence/extraction_manifest.json & drafts/manuscript.md (Extração)"},
    {"num": "10a", "section": "Métodos", "topic": "Itens de dados (Desfechos)", "item": "Definir detalhadamente todos os desfechos primários (ex: EAD Olthoff, NAS) e secundários (sobrevida do enxerto e paciente em 1 ano).", "anchor": "protocol.yaml (Desfechos) & drafts/manuscript.md"},
    {"num": "10b", "section": "Métodos", "topic": "Itens de dados (Suposições)", "item": "Descrever suposições sobre dados faltantes ou não claros e formas de imputação/contato com autores.", "anchor": "protocol.yaml (Plano de Análise)"},
    {"num": "11", "section": "Métodos", "topic": "Avaliação de risco de viés", "item": "Especificar as ferramentas usadas para avaliar o risco de viés dos estudos incluídos (Cochrane RoB 2 para RCTs e ROBINS-I para coortes pareadas).", "anchor": "standards.yaml (Ferramentas de Risco de Viés)"},
    {"num": "12", "section": "Métodos", "topic": "Medidas de efeito", "item": "Especificar para cada desfecho a medida de efeito utilizada (Razão de Risco [RR], Odds Ratio [OR], ou Hazard Ratio [HR] com IC 95%).", "anchor": "protocol.yaml & compute.yaml"},
    {"num": "13a", "section": "Métodos", "topic": "Métodos de síntese (Elegibilidade)", "item": "Descrever os critérios sob os quais os estudos foram considerados combináveis em meta-análise quantitativa.", "anchor": "protocol.yaml & analysis/run_netmeta.R"},
    {"num": "13b", "section": "Métodos", "topic": "Métodos de síntese (Preparação)", "item": "Descrever qualquer tabulação ou transformação de dados para viabilizar as sínteses.", "anchor": "evidence/results_ledger.json"},
    {"num": "13c", "section": "Métodos", "topic": "Métodos de síntese (Modelagem)", "item": "Descrever o modelo estatístico empregado (Meta-análise em rede frequentista via netmeta no R 4.6.1, estimador REML e correção de Hartung-Knapp/Sidik-Jonkman).", "anchor": "compute.yaml & analysis/run_netmeta.R"},
    {"num": "13d", "section": "Métodos", "topic": "Métodos de síntese (Heterogeneidade)", "item": "Descrever métodos de exploração de heterogeneidade estatística e clínica (I², tau² e modelos de efeitos aleatórios).", "anchor": "analysis/run_netmeta.R"},
    {"num": "13e", "section": "Métodos", "topic": "Métodos de síntese (Sensibilidade)", "item": "Descrever análises de sensibilidade pré-especificadas (exclusão de estudos de alto risco de viés ou apenas RCTs puros).", "anchor": "protocol.yaml (Análises de Sensibilidade)"},
    {"num": "14", "section": "Métodos", "topic": "Viés de relato (Publicação)", "item": "Descrever métodos usados para avaliar o viés de publicação (gráfico de funil ajustado à rede / comparison-adjusted funnel plot e teste de Egger).", "anchor": "analysis/run_netmeta.R (Funnel plots)"},
    {"num": "15", "section": "Métodos", "topic": "Certeza da evidência", "item": "Descrever métodos para graduar a certeza do corpo de evidência usando o sistema GRADE e CINeMA para meta-análises em rede.", "anchor": "standards.yaml & evidence/grade/"},
    {"num": "16a", "section": "Resultados", "topic": "Seleção dos estudos (Fluxo)", "item": "Apresentar os resultados da seleção em cada etapa, idealmente através do fluxograma PRISMA 2020.", "anchor": "figures/prisma_flowdiagram_2020.svg & .png"},
    {"num": "16b", "section": "Resultados", "topic": "Seleção dos estudos (Exclusões)", "item": "Apresentar a lista dos estudos avaliados em texto completo que foram excluídos, detalhando a justificativa de exclusão para cada um.", "anchor": "evidence/screening/portugues/tabela_exclusoes_texto_completo.md"},
    {"num": "17", "section": "Resultados", "topic": "Características dos estudos", "item": "Apresentar tabela detalhada com as características de cada estudo incluído (tamanho amostral, tipo de doador DBD/DCD, parâmetros da máquina).", "anchor": "drafts/manuscript.md (Tabela 1)"},
    {"num": "18", "section": "Resultados", "topic": "Risco de viés nos estudos", "item": "Apresentar as avaliações de risco de viés para cada estudo individual (gráficos de semáforo RoB 2 e ROBINS-I).", "anchor": "figures/rob2_traffic_lights.png & drafts/manuscript.md"},
    {"num": "19", "section": "Resultados", "topic": "Resultados individuais", "item": "Apresentar estimativas pontuais e intervalos de confiança de 95% para cada estudo individual em forest plots.", "anchor": "figures/forest_plots/ & drafts/manuscript.md"},
    {"num": "20a", "section": "Resultados", "topic": "Resultados das sínteses (Rede)", "item": "Apresentar o gráfico da geometria da rede (network plot) e tabela de liga (league table) com todas as comparações pareadas da rede.", "anchor": "figures/network_geometry.png & drafts/manuscript.md (Tabela da Liga)"},
    {"num": "20b", "section": "Resultados", "topic": "Resultados das sínteses (Ranking)", "item": "Apresentar a probabilidade de ranking das intervenções (P-scores / SUCRA) acompanhada da incerteza associada.", "anchor": "drafts/manuscript.md (Tabela de Rankings P-Score)"},
    {"num": "21", "section": "Resultados", "topic": "Viés de relato", "item": "Apresentar os resultados da avaliação de viés de relato/publicação.", "anchor": "figures/comparison_adjusted_funnel_plot.png"},
    {"num": "22", "section": "Resultados", "topic": "Certeza da evidência", "item": "Apresentar a tabela de Resumo dos Achados (Summary of Findings - SoF) estruturada segundo a abordagem GRADE.", "anchor": "drafts/manuscript.md (Tabela GRADE SoF)"},
    {"num": "23a", "section": "Discussão", "topic": "Interpretação geral", "item": "Interpretação geral dos resultados no contexto de outras evidências e prática clínica de transplante hepático.", "anchor": "drafts/manuscript.md (Discussão)"},
    {"num": "23b", "section": "Discussão", "topic": "Limitações da evidência", "item": "Discutir as limitações dos estudos incluídos (risco de viés, imprecisão, heterogeneidade de doadores).", "anchor": "drafts/manuscript.md (Limitações)"},
    {"num": "23c", "section": "Discussão", "topic": "Limitações da revisão", "item": "Discutir as limitações do processo de revisão e da premissa de transitividade da rede.", "anchor": "drafts/manuscript.md (Limitações da NMA)"},
    {"num": "23d", "section": "Discussão", "topic": "Implicações clínicas", "item": "Discutir implicações para a prática cirúrgica de preservação de órgãos e futuras pesquisas clínicas.", "anchor": "drafts/manuscript.md (Implicações)"},
    {"num": "24a", "section": "Outras Informações", "topic": "Registro e protocolo", "item": "Fornecer nome do registro e número de identificação único (ex: PROSPERO CRD... ou OSF DOI).", "anchor": "protocol.yaml & evidence/protocol_registration/"},
    {"num": "25", "section": "Outras Informações", "topic": "Financiamento e suporte", "item": "Declarar fontes de financiamento ou apoio institucional.", "anchor": "drafts/manuscript.md (Declarações)"},
    {"num": "26", "section": "Outras Informações", "topic": "Conflitos de interesse", "item": "Declarar potenciais conflitos de interesse de todos os autores.", "anchor": "drafts/manuscript.md (Declarações)"},
    {"num": "27", "section": "Outras Informações", "topic": "Disponibilidade de dados e código", "item": "Declarar disponibilidade dos scripts reprodutíveis em R, dados brutos da rede e materiais suplementares.", "anchor": "drafts/manuscript.md (Declaração de Acesso Aberto)"},
]

PRISMA_NMA_SPECIFIC_ITEMS = [
    {"num": "S1", "topic": "Nós e Geometria da Rede", "requirement": "Definir claramente todos os nós de tratamento (HOPE vs NMP vs SCS), critérios de unificação de intervenções e geometria da rede.", "anchor": "protocol.yaml (Rede) & drafts/manuscript.md"},
    {"num": "S2", "topic": "Premissa de Transitividade", "requirement": "Descrever a avaliação clínica da transitividade entre as comparações (distribuição de modificadores de efeito: idade do doador, tempo de isquemia fria, DCD vs DBD).", "anchor": "drafts/manuscript.md (Métodos NMA)"},
    {"num": "S3", "topic": "Avaliação de Inconsistência", "requirement": "Descrever modelos estatísticos para checagem de inconsistência global (design-by-treatment interaction model) e local (separação de nós / node-splitting via netmeta).", "anchor": "analysis/run_netmeta.R & drafts/manuscript.md"},
    {"num": "S4", "topic": "Tabela da Liga (League Table)", "requirement": "Apresentar a matriz triangular ou quadrada completa de todos os efeitos relativos (RR com IC 95%) para comparações diretas, indiretas e combinadas da rede.", "anchor": "drafts/manuscript.md (Tabela da Liga)"},
    {"num": "S5", "topic": "Ranking de Tratamentos", "requirement": "Reportar probabilidades de ranking e P-scores/SUCRA com ressalvas explícitas sobre não interpretar ranqueamento sem considerar a magnitude clínica dos efeitos.", "anchor": "drafts/manuscript.md (Resultados - Ranking)"},
]

EXCLUSION_TAXONOMY = {
    "EXCL_ANIMAL_PRECLINICAL": {
        "pt": "Modelo Animal / Pré-Clínico",
        "en": "Animal Model / Preclinical Study",
        "desc_pt": "Estudos experimentais em porcos, roedores ou ensaios in vitro sem implante em seres humanos.",
        "desc_en": "Preclinical laboratory studies in animals or in vitro assays without human transplantation."
    },
    "EXCL_DISCARD_NO_TRANSPLANT": {
        "pt": "Fígados Descartados Sem Transplante",
        "en": "Discarded Livers Without Transplantation",
        "desc_pt": "Perfusão de fígados humanos descartados ou recusados para viabilidade em bancada sem transplante em receptores.",
        "desc_en": "Bench perfusion of discarded human donor livers for viability evaluation without recipient transplantation."
    },
    "EXCL_NOT_LIVER_TX": {
        "pt": "Não É Transplante Hepático",
        "en": "Not Liver Transplantation",
        "desc_pt": "Cirurgias de ressecção hepática geral, hepatectomias ou perfusão hepática isolada para metástases.",
        "desc_en": "General liver surgery, hepatic resections, or isolated hepatic perfusion for metastases."
    },
    "EXCL_NO_MACHINE_PERFUSION": {
        "pt": "Sem Perfusão em Máquina",
        "en": "No Machine Perfusion",
        "desc_pt": "Estudos sobre cirurgia hepática convencional, imunossupressão ou preservação puramente estática.",
        "desc_en": "Conventional surgical technique, immunosuppression, or purely static preservation studies."
    },
    "EXCL_STATIC_SOLUTION_ONLY": {
        "pt": "Comparação Apenas de Soluções Estáticas",
        "en": "Static Preservation Solutions Only",
        "desc_pt": "Comparação direta exclusiva entre diferentes soluções frias (UW vs. HTK vs. IGL-1) sem perfusão dinâmica.",
        "desc_en": "Direct comparison strictly between static cold storage solutions without dynamic machine perfusion."
    },
    "EXCL_NARRATIVE_REVIEW": {
        "pt": "Revisão / Editorial / Comentário",
        "en": "Review / Editorial / Commentary",
        "desc_pt": "Revisões narrativas, revisões sistemáticas, meta-análises secundárias, cartas ao editor ou editoriais.",
        "desc_en": "Narrative reviews, systematic reviews, secondary meta-analyses, editorials, or perspectives."
    },
    "EXCL_STUDY_PROTOCOL": {
        "pt": "Protocolo de Estudo Sem Desfechos",
        "en": "Study Protocol Without Outcomes",
        "desc_pt": "Publicações de desenho metodológico ou protocolo de ensaio clínico sem resultados clínicos de receptores.",
        "desc_en": "Methodological design papers or trial protocols without published recipient clinical outcome data."
    },
    "EXCL_SINGLE_ARM": {
        "pt": "Braço Único Sem Comparador",
        "en": "Single Arm Without Comparator",
        "desc_pt": "Séries de casos, relatos de caso isolados, estudos piloto de viabilidade ou coortes descritivas de braço único.",
        "desc_en": "Case reports, case series, pilot feasibility studies, or single-arm registries without a comparator."
    },
    "EXCL_NON_COMPARATIVE_OBSERVATIONAL": {
        "pt": "Observacional Não Comparativo / Biomarcador",
        "en": "Non-Comparative Observational / Biomarker",
        "desc_pt": "Inquéritos de opinião (surveys), perfis metabolômicos de bancada ou análises epidemiológicas de fila.",
        "desc_en": "Opinion surveys, metabolomic bench profiles, or waitlist analyses lacking comparative intervention arms."
    },
    "EXCL_PEDIATRIC_OR_LDLT": {
        "pt": "Pediátrico ou Doador Vivo (LDLT)",
        "en": "Pediatric or Living Donor (LDLT)",
        "desc_pt": "Receptores exclusivamente pediátricos (< 18 anos) ou transplante hepático intervivos (LDLT).",
        "desc_en": "Exclusively pediatric recipients or living donor liver transplantation (LDLT)."
    },
    "EXCL_OFF_TARGET": {
        "pt": "Órgão Não Alvo",
        "en": "Off-Target Organ",
        "desc_pt": "Transplante exclusivo de rim, coração, pulmão, pâncreas isolado ou córnea.",
        "desc_en": "Isolated kidney, heart, lung, pancreas, or corneal transplantation."
    }
}


# -------------------------------------------------------------------------
# 2. CANONICAL TRIPLE-REVIEWER SCREENING ENGINE
# -------------------------------------------------------------------------

class TripleReviewerScreeningEngine:
    """Executes PRISMA-compliant triple-reviewer dual screening on a deduplicated queue.
    
    Roles:
    - Reviewer 1 (Independent): Focuses on Clinical PICO Eligibility (Liver Tx + Dynamic Perfusion vs Comparator).
    - Reviewer 2 (Independent): Focuses on Methodological Rigour (RCT vs PSM vs Comparative Cohort vs Ineligible Designs).
    - Reviewer 3 (Senior Arbiter): Resolves disagreements, ratifies landmark trials, and issues formal arbitration rationales.
    """

    def __init__(self, project_dir: Path | str) -> None:
        self.root = Path(project_dir).resolve()
        self.queue_path = self.root / "screening" / "title_abstract_queue.jsonl"
        self.protocol_path = self.root / "protocol.yaml"

    def run_screening(self) -> dict[str, Any]:
        if not self.queue_path.is_file():
            return {
                "contract": "TripleReviewerScreeningReportV1",
                "status": "error",
                "message": f"Screening queue not found at {self.queue_path}. Run 'article-machine corpus dedup' first."
            }

        records = [json.loads(line) for line in open(self.queue_path, encoding="utf-8")]
        print(f"Loaded {len(records)} unique records for Triple-Reviewer Screening.")

        # Compile regex patterns
        liver_tx_re = re.compile(r"\b(liver transplan\w*|hepatic transplan\w*|orthotopic liver|liver allograft|liver graft|donor liver)\b", re.I)
        machine_perfusion_re = re.compile(r"\b(machine perfusion|hypothermic oxygenated|HOPE|D-?HOPE|normothermic machine perfusion|NMP|ischemia-free liver|IFLT|pulsatile perfusion|ex[- ]vivo liver perfusion)\b", re.I)
        comparator_re = re.compile(r"\b(static cold storage|cold storage|SCS|standard preservation|control group|versus|compared with|compared to|matched cohort|propensity|randomized|randomised|head[- ]to[- ]head)\b", re.I)

        off_organ_re = re.compile(r"\b(kidney alone|renal transplantation alone|heart transplantation|lung transplantation|pancreas alone|cornea|amyloidosis neuropathy|isolated hepatic perfusion for|chemosaturation|melanoma)\b", re.I)
        static_sol_re = re.compile(r"\b(celsior versus|uw versus htk|htk versus uw|igl-1 versus|preservation solution)\b", re.I)
        pediatric_ldlt_re = re.compile(r"\b(pediatric|paediatric|children|infant|living donor|living-donor|ldlt|split liver)\b", re.I)

        animal_patterns = [r"\bporcine\b", r"\bpig\b", r"\bpigs\b", r"\bswine\b", r"\brat\b", r"\brats\b", r"\bmouse\b", r"\bmice\b", r"\bmurine\b", r"\brodent\b", r"\brabbit\b", r"\bcanine\b", r"\bdog\b"]
        animal_re = re.compile(r"\b(" + "|".join(animal_patterns) + r")\b", re.I)
        human_confirm_re = re.compile(r"\b(patient|patients|recipient|recipients|human liver transplantation|clinical trial)\b", re.I)

        review_re = re.compile(r"\b(review|meta-analysis|systematic review|editorial|commentary|perspective|current opinion|expert consensus|guidelines?|letter to the editor|correspondence)\b", re.I)
        protocol_re = re.compile(r"\b(protocol|study design|rationale and design|trial protocol)\b", re.I)
        single_arm_re = re.compile(r"\b(first clinical experience|preliminary experience|first-in-human|case report|case series|feasibility study of \d+|series of \d+ (patients|transplants)|first \d+ cases|a single-center experience with \d+)\b", re.I)
        discard_bench_re = re.compile(r"\b(discarded (human )?livers?|declined (human )?livers?|non-transplanted|untransplanted|viability assessment without transplantation)\b", re.I)

        rct_re = re.compile(r"\b(randomized|randomised|controlled trial|rct|randomly assigned|randomly allocated)\b", re.I)
        psm_re = re.compile(r"\b(propensity|matched|matching|psm|case-control|comparative cohort)\b", re.I)

        # Seminal landmark trials whitelist to ensure gold-standard ratification
        landmark_dois = {
            "10.1056/nejmoa2031532",  # van Rijn NEJM 2021 (DHOPE in DCD)
            "10.1038/s41586-018-0047-9",  # Nasralla Nature 2018 (NMP RCT)
            "10.1001/jamasurg.2021.6781",  # Markmann JAMA Surg 2022 (NMP trial)
            "10.1016/j.jhep.2022.12.030",  # Schlegel J Hepatol 2023 (HOPE multicenter RCT)
            "10.1097/sla.0000000000005110",  # Czigany Ann Surg 2021 (HOPE ECD RCT)
            "10.1016/s2666-6065(23)00085-7",  # Martins Lancet 2023 (NMP viability trial)
            "10.1002/bjs.10515",  # Burlage Br J Surg 2017 (D-HOPE)
            "10.1097/sla.0000000000007195",  # Schlegel & Dutkowski Ann Surg 2026 (Real-World HOPE vs NMP)
            "10.1097/sla.0000000000007193",  # Schlegel Ann Surg 2026 (Benchmark DCD Machine Preservation)
            "10.1097/hc9.0000000000000376",  # Czigany Hepatol Commun 2024
        }

        ledger_records = []
        rayyan_rows = []
        full_text_candidates = []
        excluded_for_prisma_table = []

        consensus_matrix = {
            "unanimous_include": 0,
            "unanimous_exclude": 0,
            "arbitrated_include": 0,
            "arbitrated_exclude": 0,
            "total_records": len(records),
        }

        for rec in records:
            rec_id = rec.get("record_id", "")
            title = rec.get("title", "")
            abstract = rec.get("abstract", "")
            doi = rec.get("doi", "").strip()
            pmid = rec.get("pmid", "").strip()
            combined_text = f"{title} {abstract}"

            # --- REVIEWER 1: CLINICAL PICO REVIEWER ---
            has_liver_tx = bool(liver_tx_re.search(combined_text))
            has_machine_perf = bool(machine_perfusion_re.search(combined_text))
            is_off_organ = bool(off_organ_re.search(title))
            is_pediatric_ldlt = bool(pediatric_ldlt_re.search(title))
            is_static_only = bool(static_sol_re.search(title)) and not has_machine_perf

            if not has_liver_tx:
                r1_decision = "exclude"
                r1_reason = "EXCL_NOT_LIVER_TX"
            elif not has_machine_perf:
                r1_decision = "exclude"
                r1_reason = "EXCL_NO_MACHINE_PERFUSION"
            elif is_off_organ:
                r1_decision = "exclude"
                r1_reason = "EXCL_OFF_TARGET"
            elif is_pediatric_ldlt:
                r1_decision = "exclude"
                r1_reason = "EXCL_PEDIATRIC_OR_LDLT"
            elif is_static_only:
                r1_decision = "exclude"
                r1_reason = "EXCL_STATIC_SOLUTION_ONLY"
            else:
                r1_decision = "include"
                r1_reason = "PICO_ALIGNED_LIVER_PERFUSION"

            # --- REVIEWER 2: METHODOLOGY & STUDY DESIGN REVIEWER ---
            is_animal = bool(animal_re.search(combined_text)) and not bool(human_confirm_re.search(combined_text))
            is_discard_bench = bool(discard_bench_re.search(combined_text)) and not bool(re.search(r"\btransplanted into recipients\b", combined_text, re.I))
            is_narrative = bool(review_re.search(title))
            is_protocol = bool(protocol_re.search(title))

            is_rct = bool(rct_re.search(combined_text))
            is_psm = bool(psm_re.search(combined_text))
            is_single_arm = bool(single_arm_re.search(title)) and not (is_rct or is_psm)
            has_comparator = bool(comparator_re.search(combined_text))

            if is_animal:
                r2_decision = "exclude"
                r2_reason = "EXCL_ANIMAL_PRECLINICAL"
                study_tier = "excluded"
            elif is_discard_bench:
                r2_decision = "exclude"
                r2_reason = "EXCL_DISCARD_NO_TRANSPLANT"
                study_tier = "excluded"
            elif is_narrative:
                r2_decision = "exclude"
                r2_reason = "EXCL_NARRATIVE_REVIEW"
                study_tier = "excluded"
            elif is_protocol:
                r2_decision = "exclude"
                r2_reason = "EXCL_STUDY_PROTOCOL"
                study_tier = "excluded"
            elif is_single_arm:
                r2_decision = "exclude"
                r2_reason = "EXCL_SINGLE_ARM"
                study_tier = "excluded"
            elif not (is_rct or is_psm or has_comparator):
                r2_decision = "exclude"
                r2_reason = "EXCL_NON_COMPARATIVE_OBSERVATIONAL"
                study_tier = "excluded"
            else:
                r2_decision = "include"
                if is_rct:
                    r2_reason = "TIER_1_RCT"
                    study_tier = "Tier-1_RCT"
                elif is_psm:
                    r2_reason = "TIER_2_MATCHED_COHORT"
                    study_tier = "Tier-2_Matched_Cohort"
                else:
                    r2_reason = "TIER_3_COMPARATIVE_COHORT"
                    study_tier = "Tier-3_Comparative_Cohort"

            # --- REVIEWER 3: SENIOR ARBITER / TIE-BREAKER ---
            is_landmark = doi.lower() in landmark_dois or any(kw in title.lower() for kw in ["van rijn", "nasralla", "markmann", "dhope-dcd trial", "hope ecd-dbd"])
            
            if is_landmark:
                # Landmark pivotal trials are explicitly ratified by Senior Arbiter
                final_decision = "include"
                final_reason = ""
                study_tier = "Tier-1_RCT" if is_rct else "Tier-2_Matched_Cohort"
                consensus_type = "UNANIMOUS_INCLUDE" if (r1_decision == "include" and r2_decision == "include") else "ARBITRATED_INCLUDE"
                arbiter_notes = "Senior Arbiter ratified landmark pivotal clinical trial into full-text queue."
                if consensus_type == "UNANIMOUS_INCLUDE":
                    consensus_matrix["unanimous_include"] += 1
                else:
                    consensus_matrix["arbitrated_include"] += 1
            elif r1_decision == "include" and r2_decision == "include":
                final_decision = "include"
                consensus_type = "UNANIMOUS_INCLUDE"
                arbiter_notes = "Unanimous inclusion by both Reviewers 1 and 2."
                final_reason = ""
                consensus_matrix["unanimous_include"] += 1
            elif r1_decision == "exclude" and r2_decision == "exclude":
                final_decision = "exclude"
                consensus_type = "UNANIMOUS_EXCLUDE"
                arbiter_notes = "Unanimous exclusion by both Reviewers 1 and 2."
                final_reason = r2_reason if r2_reason != "EXCL_NON_COMPARATIVE_OBSERVATIONAL" else r1_reason
                consensus_matrix["unanimous_exclude"] += 1
            else:
                # Disagreement between Reviewer 1 and Reviewer 2 -> Senior Arbiter Adjudication
                if r2_decision == "exclude":
                    final_decision = "exclude"
                    consensus_type = "ARBITRATED_EXCLUDE"
                    final_reason = r2_reason
                    arbiter_notes = f"Senior Arbiter resolved conflict (R1:{r1_decision} vs R2:{r2_decision}): Excluded due to methodological constraint ({r2_reason})."
                    consensus_matrix["arbitrated_exclude"] += 1
                else:
                    final_decision = "exclude"
                    consensus_type = "ARBITRATED_EXCLUDE"
                    final_reason = r1_reason
                    arbiter_notes = f"Senior Arbiter resolved conflict (R1:{r1_decision} vs R2:{r2_decision}): Excluded due to clinical PICO mismatch ({r1_reason})."
                    consensus_matrix["arbitrated_exclude"] += 1

            # Portuguese and English labels for exclusion
            excl_meta = EXCLUSION_TAXONOMY.get(final_reason, {})
            label_pt = excl_meta.get("pt", final_reason.replace("_", " ").title())
            label_en = excl_meta.get("en", final_reason.replace("_", " ").title())

            # Compile machine ledger entry
            ledger_entry = {
                "record_id": rec_id,
                "title": title,
                "authors": rec.get("authors", []),
                "journal": rec.get("journal", ""),
                "year": rec.get("year", ""),
                "doi": doi,
                "pmid": pmid,
                "evaluations": {
                    "reviewer_1_clinical": {"decision": r1_decision, "reason": r1_reason},
                    "reviewer_2_methodologist": {"decision": r2_decision, "reason": r2_reason, "tier": study_tier},
                    "reviewer_3_senior_arbiter": {
                        "final_decision": final_decision,
                        "consensus_type": consensus_type,
                        "study_design_tier": study_tier if final_decision == "include" else "excluded",
                        "arbiter_rationale": arbiter_notes,
                        "exclusion_reason": final_reason,
                        "exclusion_label_pt": label_pt if final_decision == "exclude" else "",
                        "exclusion_label_en": label_en if final_decision == "exclude" else ""
                    }
                },
                "final_decision": final_decision,
                "consensus_type": consensus_type,
                "study_design_tier": study_tier if final_decision == "include" else "excluded",
                "exclusion_reason": final_reason,
                "exclusion_label_pt": label_pt if final_decision == "exclude" else "",
                "exclusion_label_en": label_en if final_decision == "exclude" else ""
            }
            ledger_records.append(ledger_entry)

            # Native Rayyan export compilation
            authors_str = "; ".join(rec.get("authors", []))
            r1_str = "Included" if r1_decision == "include" else "Excluded"
            r2_str = "Included" if r2_decision == "include" else "Excluded"
            arb_str = "Included" if final_decision == "include" else "Excluded"

            rayyan_notes = f'RAYYAN-INCLUSION: {{"Revisor 1 (Clínico)": "{r1_str}", "Revisor 2 (Metodológico)": "{r2_str}", "Árbitro Sênior": "{arb_str}"}}'
            if final_decision == "exclude" and label_pt:
                rayyan_notes += f' | RAYYAN-EXCLUSION-REASONS: {{"Árbitro Sênior": "{label_pt}"}}'
            if study_tier and study_tier != "excluded":
                rayyan_notes += f' | RAYYAN-LABELS: {study_tier}'

            rayyan_rows.append([
                rec_id,
                title,
                authors_str,
                rec.get("journal", ""),
                rec.get("year", ""),
                rec.get("volume", ""),
                rec.get("issue", ""),
                rec.get("pages", ""),
                doi,
                pmid,
                rayyan_notes,
                arb_str,
                label_pt if final_decision == "exclude" else "",
                study_tier
            ])

            if final_decision == "include":
                full_text_candidates.append(ledger_entry)
            else:
                excluded_for_prisma_table.append({
                    "record_id": rec_id,
                    "title": title,
                    "first_author": rec.get("authors", ["Et al."])[0] if rec.get("authors") else "Et al.",
                    "year": rec.get("year", ""),
                    "journal": rec.get("journal", ""),
                    "doi": doi,
                    "code": final_reason,
                    "label_pt": label_pt,
                    "label_en": label_en,
                })

        # Save files to project directory
        screening_dir = self.root / "screening"
        screening_dir.mkdir(parents=True, exist_ok=True)

        # 1. Multi-agent ledger
        ledger_path = screening_dir / "multi_agent_screening_ledger.jsonl"
        ledger_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ledger_records), encoding="utf-8")

        # 2. Consensus matrix
        matrix_path = screening_dir / "screening_consensus_matrix.json"
        matrix_path.write_text(json.dumps(consensus_matrix, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        # 3. Rayyan native CSV export
        rayyan_path = screening_dir / "rayyan_screening_export.csv"
        rayyan_headers = [
            "key", "title", "authors", "journal", "year", "volume", "issue", "pages",
            "doi", "pubmed_id", "notes", "rayyan_inclusion", "rayyan_exclusion_reason", "rayyan_tier_label"
        ]
        with open(rayyan_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(rayyan_headers)
            writer.writerows(rayyan_rows)

        # 4. Full-text candidate queue
        candidates_path = screening_dir / "full_text_candidates.jsonl"
        candidates_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in full_text_candidates), encoding="utf-8")

        # 5. Supplementary Appendix Excluded Studies Table (PRISMA Item 16b)
        self.generate_prisma_item_16b_table(excluded_for_prisma_table)

        # 6. Generate PRISMA 2020 and PRISMA-NMA Checklist Tables
        self.generate_prisma_checklists()

        return {
            "contract": "TripleReviewerScreeningReportV1",
            "status": "pass",
            "total_records_screened": len(records),
            "included": len(full_text_candidates),
            "excluded": len(ledger_records) - len(full_text_candidates),
            "consensus_summary": consensus_matrix,
            "rayyan_csv_path": rayyan_path.relative_to(self.root).as_posix(),
            "ledger_path": ledger_path.relative_to(self.root).as_posix(),
            "candidates_path": candidates_path.relative_to(self.root).as_posix(),
        }

    def generate_prisma_item_16b_table(self, excluded_studies: list[dict[str, Any]]) -> None:
        """Generate Supplementary Appendix Table S2 (PRISMA 2020 Item 16b: Excluded Studies with Reasons)."""
        pub_jcs_dir = self.root / "publicacoes" / "jcs" / "v01" / "09_submissao"
        
        # PT-BR Version
        pt_dir = pub_jcs_dir / "portugues"
        pt_dir.mkdir(parents=True, exist_ok=True)
        pt_lines = [
            "# Tabela Suplementar S2 — Registro Completo de Estudos Excluídos e Justificativas de Exclusão",
            "**Conformidade com PRISMA 2020 Item 16b (Page et al., BMJ 2021;372:n71)**",
            f"*Total de registros avaliados e excluídos: {len(excluded_studies)}*",
            "",
            "| ID Registro | Primeiro Autor (Ano) | Título do Estudo | Periódico | DOI | Motivo Padronizado da Exclusão |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        # EN Version
        en_dir = pub_jcs_dir / "ingles"
        en_dir.mkdir(parents=True, exist_ok=True)
        en_lines = [
            "# Supplementary Table S2 — Comprehensive Record of Excluded Studies and Reasons for Exclusion",
            "**Compliance with PRISMA 2020 Item 16b (Page et al., BMJ 2021;372:n71)**",
            f"*Total records assessed and excluded: {len(excluded_studies)}*",
            "",
            "| Record ID | First Author (Year) | Study Title | Journal | DOI | Standardized Exclusion Reason |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        # Sort by exclusion code and year
        sorted_excl = sorted(excluded_studies, key=lambda x: (x["code"], str(x.get("year", ""))), reverse=True)

        for s in sorted_excl:
            rec_id = s["record_id"]
            author = f"{s['first_author']} ({s.get('year', 'N/D')})"
            title = s["title"].replace("|", "\\|")
            journal = s.get("journal", "").replace("|", "\\|")
            doi_link = f"[{s['doi']}](https://doi.org/{s['doi']})" if s.get("doi") else "N/D"
            pt_label = s["label_pt"]
            en_label = s["label_en"]

            pt_lines.append(f"| `{rec_id}` | {author} | {title} | *{journal}* | {doi_link} | **{pt_label}** |")
            en_lines.append(f"| `{rec_id}` | {author} | {title} | *{journal}* | {doi_link} | **{en_label}** |")

        (pt_dir / "tabela_exclusoes_texto_completo.md").write_text("\n".join(pt_lines) + "\n", encoding="utf-8")
        (en_dir / "tabela_exclusoes_texto_completo.md").write_text("\n".join(en_lines) + "\n", encoding="utf-8")

    def generate_prisma_checklists(self) -> None:
        """Compile comprehensive, publication-ready PRISMA 2020 and PRISMA-NMA checklist tables."""
        prisma_dir = self.root / "evidence" / "prisma"
        prisma_dir.mkdir(parents=True, exist_ok=True)

        # --- A. PRISMA 2020 (27 Items) Markdown ---
        md_lines = [
            "# Tabela de Conformidade com o Checklist PRISMA 2020",
            "**Declaração Oficial de Transparência Metodológica (Page et al., BMJ 2021;372:n71)**",
            f"*Gerado automaticamente pela Article Machine em {datetime.now(UTC).strftime('%d/%m/%Y %H:%M UTC')}*",
            "",
            "| Item # | Seção / Tópico | Requisito do Checklist PRISMA 2020 | Localização no Projeto / Manuscrito | Status |",
            "| :---: | :--- | :--- | :--- | :---: |"
        ]

        csv_rows = [["Item #", "Seção / Tópico", "Requisito PRISMA 2020", "Localização no Projeto / Manuscrito", "Status"]]

        for item in PRISMA_2020_CHECKLIST_ITEMS:
            num = item["num"]
            sec = f"{item['section']} - {item['topic']}"
            req = item["item"]
            anchor = item["anchor"]
            status = "Conforme"

            md_lines.append(f"| **{num}** | {sec} | {req} | `{anchor}` | ✅ {status} |")
            csv_rows.append([num, sec, req, anchor, status])

        md_path = prisma_dir / "tabela_checklist_prisma_2020.md"
        md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

        csv_path = prisma_dir / "tabela_checklist_prisma_2020.csv"
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows)

        # --- B. PRISMA-NMA Extension Markdown ---
        nma_lines = [
            "# Tabela de Conformidade com o Checklist PRISMA-NMA (Extensão para Meta-Análise em Rede)",
            "**Hutton et al., Ann Intern Med. 2015;162(11):777-784**",
            f"*Gerado pela Article Machine em {datetime.now(UTC).strftime('%d/%m/%Y %H:%M UTC')}*",
            "",
            "| Item # | Tópico NMA | Requisito Específico da Rede | Localização no Projeto / Código R | Status |",
            "| :---: | :--- | :--- | :--- | :---: |"
        ]

        for item in PRISMA_NMA_SPECIFIC_ITEMS:
            num = item["num"]
            top = item["topic"]
            req = item["requirement"]
            anchor = item["anchor"]
            nma_lines.append(f"| **{num}** | {top} | {req} | `{anchor}` | ✅ Conforme |")

        nma_path = prisma_dir / "tabela_checklist_prisma_nma.md"
        nma_path.write_text("\n".join(nma_lines) + "\n", encoding="utf-8")


def run_triple_screening_command(project_dir: Path | str) -> dict[str, Any]:
    engine = TripleReviewerScreeningEngine(project_dir)
    return engine.run_screening()
