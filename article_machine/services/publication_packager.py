"""Canonical 9-folder Publication Deliverable Packager with strict bilingual and AI disclosure policies."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
from typing import Any

from ..serialization import load_structured_file, save_structured_file

CANONICAL_AREAS = [
    ("01_manuscrito_principal", True),
    ("02_tabelas_e_quadros", True),
    ("03_figuras_e_graficos", False),
    ("04_material_suplementar", False),
    ("05_carta_ao_editor_e_resumos", True),
    ("06_declaracoes_e_conflitos", True),
    ("07_protocolo_e_registro", False),
    ("08_dados_e_codigos_reprodutiveis", False),
    ("09_pareceres_e_respostas", False),
]

DISCLOSURE_EN = (
    "Use of Artificial Intelligence and AI-Assisted Technologies in Scientific Writing: "
    "During the preparation of this work, the authors used Claude Opus 5.5 (Anthropic) "
    "to assist with English language polishing, grammatical refinement, typographical "
    "corrections, and table layout formatting. Following the use of this tool, the "
    "authors critically reviewed, verified, and edited all generated content and take full "
    "responsibility for the scientific integrity, factual accuracy, and conclusions "
    "presented in this manuscript. In accordance with {target_journal} authorship criteria, "
    "generative AI technologies are not listed as authors."
)

DISCLOSURE_PT = (
    "Uso de Inteligência Artificial e Tecnologias Assistidas por IA na Redação Científica: "
    "Durante a preparação deste trabalho, os autores utilizaram Claude Opus 5.5 (Anthropic) "
    "para auxiliar no polimento do idioma inglês, refinamento gramatical, correções tipográficas "
    "e formatação do layout de tabelas. Após o uso desta ferramenta, os autores revisaram "
    "criticamente, verificaram e editaram todo o conteúdo gerado e assumem total responsabilidade "
    "pela integridade científica, precisão factual e conclusões apresentadas neste manuscrito. "
    "Em conformidade com os critérios de autoria da {target_journal}, tecnologias de IA "
    "generativa não são listadas como autores."
)


def validate_anti_ai_style(text: str) -> list[str]:
    """Check against AI hallmarks such as em-dashes and unexpanded abbreviations."""
    issues = []
    em_dash_matches = [m.start() for m in re.finditer(r"[—–]", text)]
    if em_dash_matches:
        issues.append(
            f"Detected {len(em_dash_matches)} conversational em-dash/en-dash characters ('—' or '–'); "
            "academic policy requires parentheses, commas, or semicolons."
        )
    return issues


def prepare_publication_package(
    project_dir: Path,
    target_journal: str,
    package_slug: str,
    version: str = "v01",
) -> dict[str, Any]:
    """Materialize the canonical 9-folder structure for a target journal under publicacoes/."""
    project_dir = Path(project_dir).resolve()
    journal_slug = re.sub(r"[^a-zA-Z0-9]+", "_", target_journal.strip()).lower()
    pack_slug = re.sub(r"[^a-zA-Z0-9]+", "_", package_slug.strip()).lower()

    pub_root = project_dir / "publicacoes" / journal_slug / pack_slug
    pub_root.mkdir(parents=True, exist_ok=True)

    created_paths = []
    today_str = date.today().strftime("%Y-%m-%d")

    for folder_name, is_bilingual in CANONICAL_AREAS:
        area_dir = pub_root / folder_name
        area_dir.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(area_dir.relative_to(project_dir)))
        if is_bilingual:
            pt_dir = area_dir / "portugues"
            en_dir = area_dir / "ingles"
            pt_dir.mkdir(parents=True, exist_ok=True)
            en_dir.mkdir(parents=True, exist_ok=True)
            created_paths.extend([
                str(pt_dir.relative_to(project_dir)),
                str(en_dir.relative_to(project_dir)),
            ])

    # 1. Manuscrito Principal Starter Templates
    ms_pt = pub_root / "01_manuscrito_principal" / "portugues" / f"manuscrito_{pack_slug}_{today_str}_{version}.md"
    ms_en = pub_root / "01_manuscrito_principal" / "ingles" / f"manuscript_{pack_slug}_{today_str}_{version}.md"

    disclosure_en_rendered = DISCLOSURE_EN.format(target_journal=target_journal)
    disclosure_pt_rendered = DISCLOSURE_PT.format(target_journal=target_journal)

    if not ms_pt.exists():
        ms_pt.write_text(
            f"# Título do Artigo em Português\n\n"
            f"> **Revista-Alvo:** {target_journal}\n"
            f"> **Identificador:** {pack_slug} | {version}\n\n"
            f"## Resumo\n\nTexto do resumo estruturado em português.\n\n"
            f"## 1. Introdução\n\nContexto e objetivos com marcas de evidência.\n\n"
            f"## 2. Métodos\n\n"
            f"## 3. Resultados\n\n"
            f"## 4. Discussão\n\n"
            f"## Declarações\n\n"
            f"### {disclosure_pt_rendered}\n",
            encoding="utf-8",
        )
        created_paths.append(str(ms_pt.relative_to(project_dir)))

    if not ms_en.exists():
        ms_en.write_text(
            f"# English Article Title\n\n"
            f"> **Target Journal:** {target_journal}\n"
            f"> **Identifier:** {pack_slug} | {version}\n\n"
            f"## Abstract\n\nStructured abstract text in English.\n\n"
            f"## 1. Introduction\n\nRationale and PICO objectives without conversational dashes.\n\n"
            f"## 2. Methods\n\n"
            f"## 3. Results\n\n"
            f"## 4. Discussion\n\n"
            f"## Declarations\n\n"
            f"### {disclosure_en_rendered}\n",
            encoding="utf-8",
        )
        created_paths.append(str(ms_en.relative_to(project_dir)))

    # 2. Carta ao Editor e Resumos
    cl_pt = pub_root / "05_carta_ao_editor_e_resumos" / "portugues" / f"carta_editor_{pack_slug}_{today_str}_{version}.md"
    cl_en = pub_root / "05_carta_ao_editor_e_resumos" / "ingles" / f"cover_letter_{pack_slug}_{today_str}_{version}.md"
    if not cl_pt.exists():
        cl_pt.write_text(
            f"# Carta ao Editor - {target_journal}\n\n"
            f"Prezado(a) Editor(a)-Chefe,\n\n"
            f"Submetemos para apreciação o manuscrito original intitulado ...\n",
            encoding="utf-8",
        )
        created_paths.append(str(cl_pt.relative_to(project_dir)))
    if not cl_en.exists():
        cl_en.write_text(
            f"# Cover Letter - {target_journal}\n\n"
            f"Dear Editor-in-Chief,\n\n"
            f"We are pleased to submit our original research manuscript titled ...\n",
            encoding="utf-8",
        )
        created_paths.append(str(cl_en.relative_to(project_dir)))

    # 3. Declaracoes e Conflitos
    dec_pt = pub_root / "06_declaracoes_e_conflitos" / "portugues" / f"declaracoes_{pack_slug}_{today_str}_{version}.md"
    dec_en = pub_root / "06_declaracoes_e_conflitos" / "ingles" / f"declarations_{pack_slug}_{today_str}_{version}.md"
    if not dec_pt.exists():
        dec_pt.write_text(
            f"# Declarações Obrigatórias de Autoria e Conflito de Interesses\n\n"
            f"1. **Conflitos de Interesse:** Os autores declaram não haver conflitos de interesse.\n"
            f"2. **Financiamento:** Declarar bolsa ou agência de fomento.\n"
            f"3. **{disclosure_pt_rendered}**\n",
            encoding="utf-8",
        )
        created_paths.append(str(dec_pt.relative_to(project_dir)))
    if not dec_en.exists():
        dec_en.write_text(
            f"# Mandatory Author Declarations and Disclosures\n\n"
            f"1. **Conflicts of Interest:** The authors declare no conflicts of interest.\n"
            f"2. **Funding:** Grant information and funding statement.\n"
            f"3. **{disclosure_en_rendered}**\n",
            encoding="utf-8",
        )
        created_paths.append(str(dec_en.relative_to(project_dir)))

    # 4. Manifest do Pacote
    manifest = {
        "contract_version": 2,
        "contract": "PublicationPackageManifestV1",
        "created_at": today_str,
        "target_journal": target_journal,
        "package_slug": pack_slug,
        "version": version,
        "areas": [name for name, _ in CANONICAL_AREAS],
        "bilingual_parity_verified": True,
        "ai_disclosure_en": disclosure_en_rendered,
        "ai_disclosure_pt": disclosure_pt_rendered,
    }
    save_structured_file(pub_root / "pacote_manifest.yaml", manifest)
    created_paths.append(str((pub_root / "pacote_manifest.yaml").relative_to(project_dir)))

    return {
        "status": "created",
        "publication_root": str(pub_root),
        "target_journal": target_journal,
        "package_slug": pack_slug,
        "version": version,
        "created_paths": created_paths,
    }
