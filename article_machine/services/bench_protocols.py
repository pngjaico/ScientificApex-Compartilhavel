"""Canonical Wet-Lab & Translational Bench Protocols (SOPs), Histological Scoring, and Biobank Governance."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
import re
from typing import Any

from ..serialization import save_structured_file


SUPPORTED_ASSAYS = {
    "elisa": "Ensaio Imunoenzimático (ELISA) Sanduíche com Calibração 4-PL",
    "western": "Imunotransferência (Western Blot) com Normalização de Carga",
    "rt-qpcr": "RT-qPCR Quantitativo em Conformidade Estrita com Diretrizes MIQE",
    "chiu": "Score Histopatológico de Chiu / Park para Lesão Intestinal Mucosa",
    "suzuki": "Score Histopatológico de Suzuki para Isquemia-Reperfusão Hepática",
    "teer": "Avaliação Funcional de Barreira Epitelial (TEER e FITC-Dextrano)",
    "biobank": "Cadeia de Custódia e Rastreamento de Biobanco (-80°C)",
}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_bench_template(
    project_dir: Path,
    assay_key: str,
    assay_name: str = "",
) -> dict[str, Any]:
    """Generate a standardized, audit-ready bench SOP and data template inside a project."""
    project_dir = Path(project_dir).resolve()
    key = assay_key.strip().lower()
    if key not in SUPPORTED_ASSAYS:
        raise ValueError(f"Assay '{key}' not supported. Choose from: {list(SUPPORTED_ASSAYS.keys())}")

    title = assay_name or SUPPORTED_ASSAYS[key]
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_").lower()
    today_str = date.today().strftime("%Y-%m-%d")
    created_files = []

    exp_dir = project_dir / "experiments"
    proto_dir = exp_dir / "protocols"
    raw_dir = exp_dir / "data" / "raw"
    analysis_dir = exp_dir / "analysis"

    proto_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    if key == "elisa":
        sop_path = proto_dir / f"sop_elisa_{slug}_{today_str}.md"
        sop_content = f"""# Procedimento Operacional Padrão (SOP): {title}

> **Norma de Referência:** Clinical & Laboratory Standards Institute (CLSI) & Cochrane Gold Standard
> **Data de Criação:** {today_str}
> **Unidade Experimental:** Animal ou Paciente Único (poços são réplicas técnicas)

## 1. Princípio do Ensaio
Quantificação quantitativa por ELISA sanduíche em matriz biológica (plasma, soro, urina ou homogenato tecidual).
Ajuste de curva de calibração padrão utilizando modelo logístico de 4 parâmetros (4-PL):
$$y = D + \\frac{{A - D}}{{1 + \\left(\\frac{{x}}{{C}}\\right)^B}}$$

## 2. Reagentes e Equipamentos
- Kit ELISA com número de lote e data de validade certificados.
- Leitora de microplacas calibrada para absorbância a 450 nm (com correção a 540 ou 570 nm).
- Lavadora de placas automatizada (300 µL/poço, 4 a 6 ciclos com tampão PBST).
- Pipetas multicanal calibradas (calibração RBC/ISO 8655).

## 3. Critérios Obrigatórios de Controle de Qualidade (QC)
1. **Curva Padrão:** 7 pontos de diluição seriada ao meio em duplicata, mais poço Branco (Zero). $R^2 \\ge 0.990$.
2. **Reprodutibilidade Técnica:** Coeficiente de Variação (CV) entre duplicatas $\\le 15\\%$. Poços com $CV > 15\\%$ devem ser retestados.
3. **Limites Analíticos:**
   - Limite de Detecção ($LoD = \\text{{Média}}_{{\\text{{branco}}}} + 3 \\cdot SD_{{\\text{{branco}}}}$).
   - Limite Inferior de Quantificação ($LoQ = \\text{{Média}}_{{\\text{{branco}}}} + 10 \\cdot SD_{{\\text{{branco}}}}$).
4. **Fator de Diluição:** Ajustar diluição da amostra para que as leituras caiam na porção linear central da curva 4-PL.

## 4. Passo a Passo Operacional
1. Equilibrar todos os reagentes e placas à temperatura ambiente ($20-25^\\circ\\text{{C}}$) por 30 minutos antes do uso.
2. Preparar curva padrão imediatamente antes da aplicação.
3. Adicionar 100 µL de padrão, controle ou amostra diluída aos poços correspondentes conforme o mapa de placa.
4. Incubar conforme especificação do fabricante com agitação orbital suave (300 rpm).
5. Lavar 4 vezes com PBST aspirando completamente o líquido residual.
6. Adicionar conjugado de detecção e incubar protegido da luz.
7. Revelar com substrato TMB (10-20 min) e interromper com Stop Solution ($H_2SO_4$ 0.16 M).
8. Ler a absorbância imediatamente a 450 nm.
"""
        _write(sop_path, sop_content)
        created_files.append(str(sop_path.relative_to(project_dir)))

        # Plate map template
        plate_csv = raw_dir / f"plate_map_{slug}.csv"
        plate_rows = ["row,col,well_id,sample_type,sample_id,dilution,concentration_nominal"]
        for r in ["A", "B", "C", "D", "E", "F", "G", "H"]:
            for c in range(1, 13):
                sample_type = "STD" if c <= 2 and r != "H" else ("BLANK" if r == "H" and c <= 2 else "SAMPLE")
                plate_rows.append(f"{r},{c},{r}{c:02d},{sample_type},,,")
        _write(plate_csv, "\n".join(plate_rows) + "\n")
        created_files.append(str(plate_csv.relative_to(project_dir)))

        # R 4-PL calculation script
        r_script = analysis_dir / f"fit_elisa_4pl_{slug}.R"
        r_content = f"""# Script Reprodutivel: Ajuste de Curva ELISA 4-PL
# Ambiente R 4.6.1 - Article Machine

library(dplyr)
library(ggplot2)

message("Carregando mapa de placa e leituras de absorbancia...")
# Requer dados de absorbancia em experiments/data/raw/
# Modelo 4-PL: y = D + (A - D) / (1 + (x / C)^B)
# A = assintota inferior, B = slope de Hill, C = EC50 / IC50, D = assintota superior

calc_lod_loq <- function(blank_ods) {{
  mean_b <- mean(blank_ods, na.rm = TRUE)
  sd_b <- sd(blank_ods, na.rm = TRUE)
  list(lod = mean_b + 3 * sd_b, loq = mean_b + 10 * sd_b)
}}
"""
        _write(r_script, r_content)
        created_files.append(str(r_script.relative_to(project_dir)))

    elif key == "western":
        sop_path = proto_dir / f"sop_western_blot_{today_str}.md"
        sop_content = f"""# Procedimento Operacional Padrão: {title}

> **Norma de Referência:** Nature Protocols & NIH Guidelines
> **Data de Criação:** {today_str}

## 1. Princípio e Controle de Carga
Quantificação semiquantitativa de proteínas em lisados teciduais ou celulares.
A normalização por controle de carga endógeno (ex: GAPDH, $\\beta$-actina, vinculina ou coloração de proteína total por Ponceau S) é estritamente obrigatória no mesmo gel e membrana.

## 2. Preparação do Lisado e Lise Tecidual
- Tampão RIPA: Tris-HCl 50 mM (pH 7.4), NaCl 150 mM, NP-40 1%, Desoxicolato de sódio 0.5%, SDS 0.1%.
- Adicionar coquetel inibidor de proteases e fosfatases imediatamente antes do uso.
- Homogeneização mecânica a frio ($4^\\circ\\text{{C}}$). Centrifugação a $14.000 \\times g$ por 15 min a $4^\\circ\\text{{C}}$.
- Dosagem proteica pelo método BCA (Pierce BCA Protein Assay Kit) em triplicata com curva de BSA ($R^2 \\ge 0.995$).

## 3. Eletroforese (SDS-PAGE) e Transferência
- Carregar exatamente 20 a 40 µg de proteína total por poço.
- Gel de poliacrilamida com gradiente adequado ao peso molecular da proteína-alvo.
- Transferência para membrana PVDF pré-ativada em metanol ou nitrocelulose (transferência úmida a 100 V por 1-2 h a $4^\\circ\\text{{C}}$).

## 4. Bloqueio e Anticorpos
- Bloqueio com BSA 5% ou leite desnatado 5% em TBST por 1 hora à temperatura ambiente.
- Incubação com anticorpo primário overnight a $4^\\circ\\text{{C}}$ sob agitação lenta.
- Lavagens: 3 vezes de 10 minutos em TBST.
- Incubação com anticorpo secundário conjugado a HRP (1:5000 a 1:10000) por 1 hora à temperatura ambiente.

## 5. Aquisição e Densitometria
- Revelação por quimioluminescência reforçada (ECL Prime/Select).
- Captura digital em sistema de documentação em modo dinâmico (sem saturação de pixels).
- Análise densitométrica por ImageJ/Fiji: traçar regiões de interesse de mesma área, subtrair background local e normalizar pela banda do controle de carga.
"""
        _write(sop_path, sop_content)
        created_files.append(str(sop_path.relative_to(project_dir)))

    elif key == "rt-qpcr":
        sop_path = proto_dir / f"sop_rt_qpcr_miqe_{today_str}.md"
        sop_content = f"""# Procedimento Operacional Padrão: {title}

> **Norma de Referência:** MIQE Guidelines (Bustin et al., Clin Chem 2009)
> **Data de Criação:** {today_str}

## 1. Controle Pré-Analítico de RNA
- Extração de RNA com reagente à base de fenol/clorofórmio (TRIzol) ou colunas de sílica com digestão por DNase I on-column.
- Quantificação espectrofotométrica / fluorimétrica:
  - Relação $A_{{260}}/A_{{280}} = 1.80 \\text{{ a }} 2.10$.
  - Relação $A_{{260}}/A_{{230}} > 1.80$.
- Avaliação de integridade em gel de agarose desnaturante ou RIN $\\ge 7.0$.

## 2. Síntese de cDNA (Transcrição Reversa)
- Quantidade fixa de RNA total por reação (ex: 1000 ng em 20 µL).
- Uso de iniciadores oligo(dT) combinados com hexâmeros aleatórios.
- Incluir controle sem transcriptase reversa (controle No-RT) para excluir contaminação com DNA genômico.

## 3. Validação dos Primers e Eficiência de Amplificação
- Primers desenhados cruzando junções éxon-éxon (span exon-exon junction).
- Curva padrão de eficiência com diluições seriadas de 5 pontos do cDNA:
  - Eficiência aceitável: $E = 90\\% \\text{{ a }} 110\\%$ (equivalente a $Slope = -3.58 \\text{{ a }} -3.10$).
  - Linearidade: $R^2 \\ge 0.99$.
- Curva de dissociação (Melt Curve) com pico único demonstrando ausência de dímeros de primers ou produtos inespecíficos.

## 4. Normalização e Método $\\Delta\\Delta C_t$
- Genes de referência (housekeeping): Validar a estabilidade de pelo menos dois genes candidatos (ex: ACTB, GAPDH, HPRT1, B2M) no modelo experimental específico.
- $\\Delta C_t = C_{{t,\\text{{alvo}}}} - C_{{t,\\text{{referência}}}}$.
- $\\Delta\\Delta C_t = \\Delta C_{{t,\\text{{tratado}}}} - \\Delta C_{{t,\\text{{controle}}}}$.
- Quantificação relativa (Fold Change) $= 2^{{-\\Delta\\Delta C_t}}$.
"""
        _write(sop_path, sop_content)
        created_files.append(str(sop_path.relative_to(project_dir)))

    elif key == "chiu":
        sop_path = proto_dir / f"sop_histopatologia_chiu_park_{today_str}.md"
        sop_content = f"""# Protocolo de Avaliação Histopatológica Cega: Score de Chiu / Park

> **Área:** Isquemia e Reperfusão da Mucosa Intestinal
> **Norma de Referência:** Chiu et al., Arch Surg 1970 & Park et al., Surgery 1990
> **Data de Criação:** {today_str}

## 1. Princípio e Cegamento
Avaliação semiquantitativa da lesão tecidual e da quebra de barreira epitelial do intestino delgado.
O examinador deve obrigatoriamente estar cego para a alocação dos grupos e tempos de reperfusão.

## 2. Preparação Histológica Padronizada
- Segmento intestinal: coletar 2 cm de íleo terminal (5 cm proximal à válvula ileocecal) ou jejuno médio.
- Fixação imediata em formalina tamponada a 10% (pH 7.2-7.4) por 24 horas a $4^\\circ\\text{{C}}$.
- Inclusão em parafina orientando o fragmento rigorosamente no plano transversal/longitudinal dos vilos.
- Cortes de 4 a 5 µm corados por Hematoxilina e Eosina (H&E).
- Analisar apenas vilos inteiros orientados verticalmente da cripta ao ápice (mínimo de 10 a 20 vilos por animal).

## 3. Escala Graduada de Chiu / Park
- **Grau 0:** Mucosa normal, vilosidades intactas, sem lise ou edema subepitelial.
- **Grau 1:** Formação do espaço subepitelial de Gruenhagen no ápice da vilosidade, frequentemente acompanhado por congestão capilar apical.
- **Grau 2:** Extensão do espaço subepitelial com descolamento moderado da camada epitelial em direção à base do vilo.
- **Grau 3:** Descolamento epitelial maciço ao longo das faces laterais das vilosidades; algumas pontas de vilos podem estar denudadas.
- **Grau 4:** Vilosidades totalmente desnudadas de epitélio, com lâmina própria e capilares dilatados expostos ao lúmen intestinal.
- **Grau 5:** Perda da conformação das vilosidades, desintegração da lâmina própria com hemorragia e ulceração mucosa.
- **Grau 6:** Necrose e hemorragia estendendo-se à camada submucosa.
- **Grau 7:** Necrose transmural comprometendo a camada muscular própria.
- **Grau 8:** Necrose transmural completa com perfuração iminente ou estabelecida da serosa.

## 4. Análise Estatística
- Tratar o animal como a unidade amostral (calcular a mediana ou média dos vilos de cada animal).
- Não realizar testes estatísticos usando os vilos individuais como $N$ independente (pseudorreplicação).
- Comparação entre grupos por teste de Mann-Whitney (2 grupos) ou Kruskal-Wallis com pós-teste de Dunn (> 2 grupos).
"""
        _write(sop_path, sop_content)
        created_files.append(str(sop_path.relative_to(project_dir)))

        # Sheet for scoring records
        score_csv = raw_dir / "leitura_histologica_chiu_template.csv"
        score_rows = [
            "animal_id,slide_id,field_id,villus_number,chiu_score_0_to_8,observer_id,date,notes"
        ]
        _write(score_csv, "\n".join(score_rows) + "\n")
        created_files.append(str(score_csv.relative_to(project_dir)))

    elif key == "suzuki":
        sop_path = proto_dir / f"sop_histopatologia_suzuki_{today_str}.md"
        sop_content = f"""# Protocolo de Avaliação Histopatológica Cega: Score de Suzuki

> **Área:** Isquemia e Reperfusão Hepática
> **Norma de Referência:** Suzuki et al., Transplantation 1993
> **Data de Criação:** {today_str}

## 1. Princípio e Cegamento
Quantificação semiquantitativa da lesão celular e sinusoidal após isquemia fria/quente e reperfusão hepática.
Avaliação cega de 10 campos de grande aumento ($400\\times$) por lâmina por observador independente.

## 2. Critérios de Pontuação de Suzuki (0 a 4)
| Grau | Congestão Sinusoidal | Vacuolização de Hepatócitos | Necrose Parenquimatosa |
|---|---|---|---|
| **0** | Ausente | Ausente | Ausente |
| **1** | Mínima | Mínima | Ausente |
| **2** | Leve | Leve | < 30% dos hepatócitos |
| **3** | Moderada | Moderada | 30% a 60% dos hepatócitos |
| **4** | Grave | Grave | > 60% dos hepatócitos |

## 3. Consolidação Estatística
O escore final do animal é a média ou mediana dos campos analisados.
Testes não-paramétricos de postos são obrigatórios.
"""
        _write(sop_path, sop_content)
        created_files.append(str(sop_path.relative_to(project_dir)))

    elif key == "teer":
        sop_path = proto_dir / f"sop_permeabilidade_barreira_{today_str}.md"
        sop_content = f"""# Protocolo Operacional Padrão: Permeabilidade Epitelial (TEER & FITC-Dextrano)

> **Área:** Barreira Epitelial e Integridade Mucosa
> **Data de Criação:** {today_str}

## 1. Resistência Elétrica Transepitelial (TEER)
- Montagem de tecido em câmara de Ussing ou células epiteliais (Caco-2/organoides) em inserts Transwell ($0.4\\text{{ µm}}$).
- Solução de Krebs-Henseleit gaseificada com carbogênio ($95\\%\\text{{ }}O_2 / 5\\%\\text{{ }}CO_2$) a $37^\\circ\\text{{C}}$.
- Leitura com voltômetro-ohmímetro epitelial (ex: EVOM).
- Cálculo: $TEER = (R_{{\\text{{total}}}} - R_{{\\text{{branco}}}}) \\times \\text{{Área}}_{{\\text{{insert}}}} \\text{{ [}}\\Omega \\cdot \\text{{cm}}^2\\text{{]}}$.

## 2. Fluxo Macromolecular de FITC-Dextrano (4 kDa)
- Adição de FITC-dextrano 4 kDa (FD4) no compartimento luminal/apical ($1 \\text{{ mg/mL}}$).
- Coleta de amostras do compartimento seroso/basolateral em $0, 30, 60, 90 \\text{{ e }} 120$ minutos.
- Leitura em espectrofluorímetro (Excitação: 485 nm / Emissão: 530 nm).
- Cálculo do coeficiente de permeabilidade aparente ($P_{{\\text{{app}}}}$):
  $$P_{{\\text{{app}}}} = \\frac{{dQ/dt}}{{A \\times C_0}} \\text{{ [cm/s]}}$$
"""
        _write(sop_path, sop_content)
        created_files.append(str(sop_path.relative_to(project_dir)))

    elif key == "biobank":
        sop_path = proto_dir / f"sop_cadeia_custodia_biobanco_{today_str}.md"
        sop_content = f"""# Procedimento Operacional Padrão: Biobanco e Cadeia de Custódia

> **Norma de Referência:** ISBER Best Practices for Repositories
> **Data de Criação:** {today_str}

## 1. Diretrizes Pré-Analíticas Obrigatórias
- Coleta de amostras em tubos pré-resfriados a $4^\\circ\\text{{C}}$.
- Centrifugação imediata (máximo 30 minutos pós-coleta): $2000 \\times g$ por 10 minutos a $4^\\circ\\text{{C}}$.
- Aliquotagem imediata em criotubos de 0.5 mL identificados com código 2D/alfanumérico único.
- Congelamento imediato em nitrogênio líquido ou freezer ultrabaixo ($-80^\\circ\\text{{C}}$).

## 2. Controle de Ciclos de Congelamento/Descongelamento
- Proteínas e biomarcadores lábeis (I-FABP, Claudina-3, citocinas) sofrem proteólise severa após descongelamento repetido.
- A contagem de ciclos deve ser rigorosamente registrada no manifesto de amostras.
- Amostras com mais de 2 ciclos de descongelamento devem ser marcadas como impróprias para dosagens quantitativas finas.
"""
        _write(sop_path, sop_content)
        created_files.append(str(sop_path.relative_to(project_dir)))

        # Manifest template
        manifest_csv = exp_dir / "samples" / "sample_manifest.csv"
        if not manifest_csv.exists():
            rows = [
                "sample_id,subject_id,group,tissue,warm_ischemia_min,cold_ischemia_min,collection_time,centrifugation_time,storage_temp,freeze_thaw_cycles,freezer_location"
            ]
            _write(manifest_csv, "\n".join(rows) + "\n")
            created_files.append(str(manifest_csv.relative_to(project_dir)))

    return {
        "status": "created",
        "assay_key": key,
        "assay_title": title,
        "created_files": created_files,
    }


def validate_sample_manifest(manifest_csv_path: Path) -> dict[str, Any]:
    """Audit a sample manifest for missing metadata, duplicate IDs, or dangerous freeze-thaw cycles."""
    path = Path(manifest_csv_path)
    if not path.is_file():
        return {"status": "error", "issues": [f"Manifest file not found: {path}"]}

    issues = []
    sample_ids = set()
    high_freeze_thaw = []

    with path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):
            sid = str(row.get("sample_id", "")).strip()
            if not sid:
                issues.append(f"Row {idx}: missing sample_id.")
                continue
            if sid in sample_ids:
                issues.append(f"Row {idx}: duplicate sample_id '{sid}'.")
            sample_ids.add(sid)

            cycles = row.get("freeze_thaw_cycles", "").strip()
            if cycles and cycles.isdigit() and int(cycles) > 2:
                high_freeze_thaw.append(sid)

    if high_freeze_thaw:
        issues.append(
            f"Caution: {len(high_freeze_thaw)} samples have > 2 freeze-thaw cycles: {high_freeze_thaw[:5]}... "
            "Biomarkers may be degraded."
        )

    return {
        "status": "pass" if not issues else "warning",
        "total_samples": len(sample_ids),
        "issues": issues,
    }
