"""Landmark Paper Dissection & Learning Engine: Learn from the greatest biomedical papers in history."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
from typing import Any

from ..serialization import save_structured_file

ELITE_JOURNALS = {
    "nature": {"name": "Nature", "category": "Multidisciplinary Science", "min_impact": "High"},
    "science": {"name": "Science", "category": "Multidisciplinary Science", "min_impact": "High"},
    "nature_medicine": {"name": "Nature Medicine", "category": "Translational Medicine", "min_impact": "High"},
    "nejm": {"name": "The New England Journal of Medicine", "category": "General Clinical", "min_impact": "High"},
    "lancet": {"name": "The Lancet", "category": "General Clinical", "min_impact": "High"},
    "jama": {"name": "JAMA", "category": "General Clinical", "min_impact": "High"},
    "annals_surgery": {"name": "Annals of Surgery", "category": "Surgical Science", "min_impact": "High"},
    "ajt": {"name": "American Journal of Transplantation", "category": "Transplantation", "min_impact": "High"},
    "transplantation": {"name": "Transplantation", "category": "Transplantation", "min_impact": "High"},
    "jama_surgery": {"name": "JAMA Surgery", "category": "Surgical Science", "min_impact": "High"},
    "bjs": {"name": "British Journal of Surgery", "category": "Surgical Science", "min_impact": "High"},
    "gastroenterology": {"name": "Gastroenterology", "category": "Gastroenterology & Hepatology", "min_impact": "High"},
    "gut": {"name": "Gut", "category": "Gastroenterology & Hepatology", "min_impact": "High"},
    "j_hepatology": {"name": "Journal of Hepatology", "category": "Gastroenterology & Hepatology", "min_impact": "High"},
}

LANDMARK_DIMENSIONS = [
    ("1_gap_e_hipotese", "Enunciado do Gap de Conhecimento e Racionalidade da Hipótese"),
    ("2_delineamento_e_poder", "Delineamento Experimental, Poder Amostral e Controles"),
    ("3_storyline_visual_figuras", "Storyline Visual e Arquitetura Multipainel das Figuras"),
    ("4_metodologia_estatistica", "Estatística Robusta, Modelos Mistos e Controle de Falsos Positivos"),
    ("5_calibracao_de_claims", "Calibração e Sobriedade dos Claims Científicos"),
    ("6_licoes_de_excelencia", "Roteiro Prático de Lições para o Nosso Projeto"),
]


def search_landmark_papers(
    query: str,
    target_journals: list[str] | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Search for seminal / landmark papers in elite medical and surgical journals."""
    selected_journals = target_journals or [j["name"] for j in ELITE_JOURNALS.values()]
    q_norm = query.strip()

    # Return structured search plan and recommended landmark query parameters
    return {
        "status": "planned",
        "query": q_norm,
        "target_elite_journals": selected_journals[:8],
        "limit": limit,
        "recommended_filters": {
            "has_doi": True,
            "min_citations": 50,
            "publication_types": ["Randomized Controlled Trial", "Meta-Analysis", "Classic Article", "Multicenter Study"],
        },
        "search_recipe": f'("{q_norm}") AND ({" OR ".join(f'"{j}"[Journal]' for j in selected_journals[:5])})',
    }


def dissect_landmark_paper(
    project_dir: Path,
    title: str,
    journal: str,
    year: str | int,
    doi: str,
    authors: str = "Autores Principais",
    primary_endpoint: str = "",
    study_design: str = "",
    slug: str = "",
) -> dict[str, Any]:
    """Dissect the architectural and methodological blueprint of an elite landmark paper."""
    project_dir = Path(project_dir).resolve()
    slug_val = slug or re.sub(r"[^a-zA-Z0-9]+", "_", title[:40]).strip("_").lower()
    today_str = date.today().strftime("%Y-%m-%d")

    learnings_dir = project_dir / "context" / "landmark_learnings"
    learnings_dir.mkdir(parents=True, exist_ok=True)

    dossier_path = learnings_dir / f"dossie_metodologico_{slug_val}.md"

    content = f"""# Dossiê de Dissecação Metodológica: Estudo Landmark de Elite

> **Artigo de Referência:** {title}
> **Autores:** {authors}
> **Periódico:** {journal} ({year}) | **DOI:** {doi}
> **Delineamento:** {study_design or 'Ensaio Clínico Randomizado Multicêntrico / Estudo Translacional de Alta Definição'}
> **Desfecho Primário:** {primary_endpoint or 'Especificado no protocolo'}
> **Data da Dissecação:** {today_str}

---

## 1. Enunciado do Gap de Conhecimento e Hipótese Central
- **O Que Faltava na Literatura:** Os autores identificaram não apenas uma lacuna pontual, mas uma contradição ou incerteza clínica com impacto direto na conduta médica ou sobrevida.
- **Formulação da Hipótese:** A hipótese não é genérica; ela define a intervenção precisa, a população-alvo e a direção biológica esperada do efeito.
- **Racional Mecanístico:** A introdução conecta a clínica aos mecanismos moleculares/fisiopatológicos fundamentais (ex: permeabilidade epitelial, quebra de barreira, vias inflamatórias).

## 2. Delineamento Experimental, Poder Amostral e Controles
- **Cálculo de Poder a Priori:**
  - Hipótese nula ($H_0$) e alternativa ($H_1$) claramente demarcadas.
  - Poder estabelecido em $1 - \\beta \\ge 0.80$ (ou $0.90$) com nível de significância $\\alpha = 0.05$ bicaudal.
  - Estimativa de tamanho de efeito ancorada em estudos-piloto ou literatura preliminar.
  - Previsão formal de taxa de perdas de seguimento ou amostras não conformes (+10% a 15%).
- **Arquitetura de Controles:**
  - Controles negativos e basais rigorosos.
  - Bloqueio estrito de pseudorreplicação (unidade amostral é o sujeito/animal biológico, nunca poços ou cortes técnicos).
  - Alocação aleatória gerada por computador e cegamento duplo ou triplo (paciente, cirurgião/pesquisador e avaliador de desfecho/patologista).

## 3. Storyline Visual e Arquitetura Multipainel das Figuras
- **Figura 1:** Delineamento experimental, linha do tempo e fluxograma PRISMA / CONSORT de inclusão e perda de sujeitos.
- **Figura 2:** Desfecho clínico ou cirúrgico primário com intervalos de confiança e dispersão individual dos dados (gráficos de pontos com medianas/médias, evitando gráficos de barras opacos).
- **Figura 3:** Painel mecanístico de bancada (análises pareadas de biomarcadores por ELISA 4-PL, imunotransferência com controle de carga e escores histopatológicos cegos).
- **Figura 4:** Validação em subgrupos pré-especificados, curvas de sobrevida (Kaplan-Meier / Riscos Competitivos de Fine-Gray) ou curva ROC de acurácia diagnóstica.
- **Paleta de Cores e Acessibilidade:** Cores sóbrias e legíveis para daltonismo (viridis ou paleta Nature), com resolução mínima de 300 dpi (vetorial SVG/PDF para gráficos; TIFF/PNG de alta resolução para micrografias com barras de escala calibradas).

## 4. Metodologia Estatística e Controle de Viés
- **Tratamento de Dados Normais e Não-Normais:** Avaliação formal de normalidade (Shapiro-Wilk) combinada com inspeção visual de gráficos Q-Q.
- **Dados Pareados e Medidas Repetidas:** Uso de modelos lineares de efeitos mistos (LMM) ou modelos de equações de estimativa generalizada (GEE) para acomodar a correlação intra-indivíduo sem inflar graus de liberdade.
- **Correção de Multiplicidade:** Controle da taxa de descoberta falsa (FDR via Benjamini-Hochberg) em múltiplos biomarcadores ou correção de Bonferroni/Holm para comparações planejadas.
- **Análises de Sensibilidade:** Checagem de robustez retirando casos limítrofes (outliers biologicamente plausíveis) e avaliando o impacto de dados faltantes (imputação múltipla vs análise de casos completos).

## 5. Calibração e Sobriedade dos Claims Científicos
- **Linguagem Acadêmica Nobre:** Os autores utilizam verbos precisos: *"demonstramos que"*, *"nossos achados sugerem"*, *"na presente coorte"*, evitando superlativos vazios (*"perfeito"*, *"revolucionário"*, *"único no mundo"*).
- **Reconhecimento Ativo de Limitações:** O penúltimo parágrafo da discussão disseca francamente o tamanho amostral, a representatividade da população, a monocentricidade e potenciais variáveis de confusão não mensuradas. Essa humildade metodológica é o que garante a aceitação em periódicos de topo.

## 6. Roteiro Prático de Lições para o Nosso Projeto
1. **Adotar o mesmo rigor no cálculo amostral:** Não iniciar coleta de bancada ou animais sem $N$ justificado por poder estatístico.
2. **Espelhar a estrutura das Figuras:** Montar os rascunhos das Figuras 1 a 4 antes mesmo da redação do manuscrito.
3. **Manter o cego e biobanco padronizados:** Registrar todas as amostras no manifesto antes do processamento.
4. **Redigir a discussão com claims calibrados:** Ancorar cada frase no Evidence Lock (`claim_map.jsonl`).
"""
    dossier_path.write_text(content, encoding="utf-8")

    manifest_entry = {
        "contract": "LandmarkPaperDossierV1",
        "created_at": today_str,
        "title": title,
        "journal": journal,
        "year": str(year),
        "doi": doi,
        "dossier_file": str(dossier_path.relative_to(project_dir)),
    }
    save_structured_file(learnings_dir / f"manifest_{slug_val}.yaml", manifest_entry)

    return {
        "status": "created",
        "slug": slug_val,
        "dossier_path": str(dossier_path),
        "target_journal": journal,
    }
