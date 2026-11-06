"""Peer Rebuttal Engine: Generate diplomatic, point-by-point rebuttal letters and track manuscript modifications."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
from typing import Any

from ..serialization import save_structured_file


RE_REVIEWER_HEADER = re.compile(r"^(?:Reviewer\s*#?\s*(\d+)|Revisor\s*#?\s*(\d+)|Editor(?:'s Comments)?):?", re.IGNORECASE | re.MULTILINE)


def parse_peer_review_letter(raw_text: str) -> list[dict[str, Any]]:
    """Parse an unstructured peer review letter into individual reviewer sections and items."""
    lines = raw_text.lstrip('\ufeff').splitlines()
    sections: list[dict[str, Any]] = []
    current_role = "Editor"
    current_items: list[str] = []
    current_buffer: list[str] = []

    def flush_item():
        if current_buffer:
            text_block = "\n".join(current_buffer).strip()
            if text_block:
                current_items.append(text_block)
            current_buffer.clear()

    for line in lines:
        match = RE_REVIEWER_HEADER.match(line.strip())
        if match:
            flush_item()
            if current_items:
                sections.append({"role": current_role, "items": list(current_items)})
                current_items.clear()
            num = match.group(1) or match.group(2)
            current_role = f"Reviewer {num}" if num else "Editor"
            continue

        # Check for numbered items (1., 2., 3., Point 1, etc.)
        if re.match(r"^(?:(?:Point|Comment|Major Comment|Item)\s*)?\d+[\.:\)]|^[-*•]\s+", line.strip()):
            flush_item()
            current_buffer.append(line.strip())
        else:
            if line.strip():
                current_buffer.append(line.strip())

    flush_item()
    if current_items:
        sections.append({"role": current_role, "items": list(current_items)})
    elif current_buffer:
        sections.append({"role": current_role, "items": ["\n".join(current_buffer).strip()]})

    if not sections and raw_text.strip():
        # Fallback single block
        sections.append({"role": "Reviewer 1", "items": [raw_text.strip()]})

    return sections


def draft_rebuttal_response(
    role: str,
    item_index: int,
    critique_text: str = "",
    *,
    critique: str = "",
) -> dict[str, str]:
    critique_text = critique or critique_text
    """Draft diplomatic paired English and PT-BR responses adhering to top-tier editorial etiquette."""
    # Standard diplomatic opening formulas
    diplomatic_en_starts = [
        "We thank the reviewer for this constructive observation.",
        "We appreciate this insightful question regarding our methodological rationale.",
        "We agree with the reviewer that this is a critical aspect requiring clarification.",
        "We are grateful for this important critique, which has significantly strengthened the manuscript.",
    ]
    diplomatic_pt_starts = [
        "Agradecemos ao parecerista por esta observação altamente construtiva.",
        "Apreciamos esta pergunta perspicaz referente à racionalidade metodológica do nosso estudo.",
        "Concordamos plenamente com o parecerista quanto à importância de clarificar este aspecto.",
        "Agradecemos por esta crítica fundamental, que fortaleceu substancialmente a qualidade do manuscrito.",
    ]

    start_en = diplomatic_en_starts[item_index % len(diplomatic_en_starts)]
    start_pt = diplomatic_pt_starts[item_index % len(diplomatic_pt_starts)]

    response_en = f"""**Response:** {start_en} [AUTHOR TO COMPLETE: state the action actually taken, or the reasoned disagreement, with supporting evidence.]

**Manuscript Changes:**
> *[AUTHOR TO COMPLETE: location (section, page, line) and the exact revised text. Do not claim analyses that were not performed.]*
"""

    response_pt = f"""**Resposta:** {start_pt} [AUTOR PREENCHER: descrever a a\u00e7\u00e3o efetivamente realizada, ou a discord\u00e2ncia fundamentada, com evid\u00eancia.]

**Altera\u00e7\u00f5es no Manuscrito:**
> *[AUTOR PREENCHER: local (se\u00e7\u00e3o, p\u00e1gina, linha) e texto revisado exato. N\u00e3o declarar an\u00e1lises que n\u00e3o foram realizadas.]*
"""

    return {
        "en": response_en.strip(),
        "pt": response_pt.strip(),
    }


def generate_peer_rebuttal_package(
    project_dir: Path | str,
    peer_review_text: str | Path = "",
    target_journal: str = "The Lancet",
    journal_slug: str = "",
    *,
    peer_review_path: str | Path | None = None,
    package_slug: str = "artigo_principal",
) -> dict[str, Any]:
    """Generate canonical 9-folder Point-by-Point Rebuttal package in Portuguese and English."""
    project_dir = Path(project_dir).resolve()

    review_input = peer_review_path or peer_review_text
    if isinstance(review_input, Path) or (isinstance(review_input, str) and Path(review_input).exists()):
        review_path = Path(review_input)
        raw_text = review_path.read_text(encoding="utf-8-sig")
    else:
        raw_text = str(review_input)

    parsed_sections = parse_peer_review_letter(raw_text)

    # Derive slug if not explicitly passed
    effective_slug = journal_slug or (target_journal.lower().replace(" ", "_") if target_journal else "revista_destino")

    # Setup 9-folder canonical destination: 08_resposta_pareceristas/
    rebuttal_dir = project_dir / "publicacoes" / effective_slug / "08_resposta_pareceristas"
    pt_dir = rebuttal_dir / "portugues"
    en_dir = rebuttal_dir / "ingles"
    pt_dir.mkdir(parents=True, exist_ok=True)
    en_dir.mkdir(parents=True, exist_ok=True)

    today_str = date.today().strftime("%Y-%m-%d")

    # Construct paired letters
    letter_en_lines = [
        f"# Point-by-Point Response to the Reviewers and Editor",
        f"**Journal:** {target_journal}",
        f"**Date:** {today_str}",
        f"**Manuscript Title:** [Insert Manuscript Title]",
        f"",
        f"Dear Editor and Reviewers,",
        f"",
        f"We sincerely thank the editorial team and the expert reviewers for their thorough, constructive, and demanding review of our manuscript. We have carefully addressed every comment and incorporated all suggestions into the revised version.",
        f"",
        f"Below, please find our itemized, point-by-point responses detailing the modifications made.",
        f"",
        f"---",
        f"",
    ]

    letter_pt_lines = [
        f"# Carta de Resposta Ponto a Ponto aos Pareceristas e Editor",
        f"**Revista:** {target_journal}",
        f"**Data:** {today_str}",
        f"**Título do Manuscrito:** [Inserir Título do Manuscrito]",
        f"",
        f"Prezado(a) Editor(a) e Ilustres Pareceristas,",
        f"",
        f"Agradecemos sinceramente à equipe editorial e aos pareceristas especializados por sua revisão minuciosa, construtiva e rigorosa do nosso manuscrito. Abordamos com o máximo cuidado cada uma das observações e incorporamos todas as sugestões na versão revisada.",
        f"",
        f"Abaixo, apresentamos nossas respostas detalhadas, ponto a ponto, especificando as modificações efetuadas.",
        f"",
        f"---",
        f"",
    ]

    item_count = 0
    structured_items: list[dict[str, Any]] = []

    for section in parsed_sections:
        role = section["role"]
        letter_en_lines.append(f"## {role}\n")
        letter_pt_lines.append(f"## {role}\n")

        for idx, critique in enumerate(section["items"], 1):
            item_count += 1
            code = f"{role[0]}.{idx}"
            drafts = draft_rebuttal_response(role, idx, critique)

            # English block
            letter_en_lines.append(f"### Comment {code}")
            letter_en_lines.append(f"> \"{critique}\"\n")
            letter_en_lines.append(drafts["en"])
            letter_en_lines.append("\n---\n")

            # Portuguese block
            letter_pt_lines.append(f"### Comentário {code}")
            letter_pt_lines.append(f"> \"{critique}\"\n")
            letter_pt_lines.append(drafts["pt"])
            letter_pt_lines.append("\n---\n")

            structured_items.append({
                "item_id": code,
                "role": role,
                "critique": critique,
                "response_en": drafts["en"],
                "response_pt": drafts["pt"],
            })

    # Save documents
    en_file = en_dir / "rebuttal_letter_to_reviewers.md"
    pt_file = pt_dir / "carta_resposta_pareceristas.md"
    manifest_file = rebuttal_dir / "rebuttal_manifest.json"

    en_file.write_text("\n".join(letter_en_lines), encoding="utf-8")
    pt_file.write_text("\n".join(letter_pt_lines), encoding="utf-8")

    manifest = {
        "contract": "PeerRebuttalManifestV1",
        "created_at": today_str,
        "target_journal": target_journal,
        "journal_slug": effective_slug,
        "total_comments_addressed": item_count,
        "sections_count": len(parsed_sections),
        "deliverables": {
            "english_letter": str(en_file),
            "portuguese_letter": str(pt_file),
        },
        "items": structured_items,
    }
    save_structured_file(manifest_file, manifest)

    return {
        "status": "created",
        "total_comments": item_count,
        "rebuttal_dir": str(rebuttal_dir),
        "english_letter": str(en_file),
        "portuguese_letter": str(pt_file),
        "manifest": str(manifest_file),
    }
