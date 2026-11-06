from __future__ import annotations

import html
import json
from pathlib import Path
import zipfile

from .serialization import load_structured_file


P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_R_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
SLIDE_CX = 12192000
SLIDE_CY = 6858000


def _content_types(slide_count: int, media_exts: set[str] | None = None) -> str:
    image_defaults: list[str] = []
    for ext in sorted(media_exts or set()):
        content_type = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
        }.get(ext.lower())
        if content_type:
            image_defaults.append(f'  <Default Extension="{ext.lower()}" ContentType="{content_type}"/>')
    slide_overrides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
{chr(10).join(image_defaults)}
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  {slide_overrides}
</Types>"""


def _root_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""


def _presentation_xml(slide_count: int) -> str:
    ids = "\n".join(
        f'<p:sldId id="{255 + i}" r:id="rId{i}"/>' for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}">
  <p:sldIdLst>{ids}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_CX}" cy="{SLIDE_CY}" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""


def _presentation_rels(slide_count: int) -> str:
    rels = "\n".join(
        f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PKG_R_NS}">{rels}</Relationships>"""


def _paragraphs(text: str, font_size: int, color: str = "15211F", bold: bool = False) -> str:
    lines = [line for line in str(text or "").splitlines() if line.strip()]
    if not lines:
        lines = [""]
    paragraphs = []
    for line in lines:
        safe = html.escape(line)
        paragraphs.append(
            f'<a:p><a:r><a:rPr lang="en-US" sz="{font_size * 100}" b="{1 if bold else 0}">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f"</a:rPr><a:t>{safe}</a:t></a:r></a:p>"
        )
    return "".join(paragraphs)


def _textbox(
    shape_id: int,
    x: int,
    y: int,
    cx: int,
    cy: int,
    text: str,
    font_size: int,
    color: str = "15211F",
    bold: bool = False,
) -> str:
    return f"""
<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="{shape_id}" name="Text {shape_id}"/>
    <p:cNvSpPr txBox="1"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="square"/>
    <a:lstStyle/>
    {_paragraphs(text, font_size, color=color, bold=bold)}
  </p:txBody>
</p:sp>"""


def _rect(shape_id: int, x: int, y: int, cx: int, cy: int, fill: str, line: str) -> str:
    return f"""
<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="{shape_id}" name="Block {shape_id}"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
    <a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>
    <a:ln w="12700"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>
  </p:spPr>
  <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
</p:sp>"""


def _picture(pic_id: int, rel_id: str, x: int, y: int, cx: int, cy: int, name: str) -> str:
    safe_name = html.escape(name)
    return f"""
<p:pic>
  <p:nvPicPr>
    <p:cNvPr id="{pic_id}" name="{safe_name}"/>
    <p:cNvPicPr/>
    <p:nvPr/>
  </p:nvPicPr>
  <p:blipFill>
    <a:blip r:embed="{rel_id}"/>
    <a:stretch><a:fillRect/></a:stretch>
  </p:blipFill>
  <p:spPr>
    <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
  </p:spPr>
</p:pic>"""


def _slide_xml(title: str, body: str, notes: str) -> str:
    text = body
    if notes:
        text = f"{body}\n\nSpeaker notes: {notes}"
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {_textbox(2, 600000, 500000, 10900000, 900000, title, 34, bold=True)}
      {_textbox(3, 800000, 1600000, 10400000, 4300000, text, 19)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def _metadata_json(storyboard: dict, conference: dict, kind: str) -> str:
    payload = {
        "schema_version": 1,
        "kind": kind,
        "event_name": conference.get("event_name", ""),
        "profile": conference.get("profile", ""),
        "authors": conference.get("authors", []),
        "affiliations": conference.get("affiliations", []),
        "qr_url": conference.get("qr", {}).get("url", ""),
        "scene_count": len(storyboard.get("scenes", [])),
        "source_claim_ids": sorted(
            {
                claim_id
                for scene in storyboard.get("scenes", [])
                for claim_id in scene.get("source_claim_ids", [])
            }
        ),
        "policy": "HTML remains canonical; this PPTX is an editable fallback export.",
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _notes_markdown(storyboard: dict, conference: dict) -> str:
    lines = [
        f"# Speaker Notes - {conference.get('event_name', 'Conference')}",
        "",
        f"Profile: {conference.get('profile', '')}",
        "",
    ]
    for idx, scene in enumerate(storyboard.get("scenes", []), start=1):
        lines.extend(
            [
                f"## Slide {idx}: {scene.get('title', '')}",
                "",
                str(scene.get("speaker_notes") or ""),
                "",
                f"Claims: {', '.join(scene.get('source_claim_ids', []))}",
                "",
            ]
        )
    return "\n".join(lines)


def _resolve_media_path(base_dir: Path, raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    candidate = Path(str(raw_path))
    if candidate.is_absolute():
        return candidate if candidate.exists() else None
    resolved = base_dir / candidate
    return resolved if resolved.exists() else None


def _poster_body_text(scene: dict, conference: dict) -> str:
    lines: list[str] = []
    if scene.get("lead"):
        lines.append(str(scene.get("lead")))
    if scene.get("body"):
        lines.append(str(scene.get("body")))
    for bullet in scene.get("bullets") or []:
        lines.append(f"- {bullet}")
    for metric in scene.get("metrics") or []:
        label = metric.get("label", "")
        value = metric.get("value", "")
        lines.append(f"{label}: {value}".strip(": "))
    for meta in scene.get("meta_lines") or []:
        lines.append(str(meta))
    if scene.get("qr_path"):
        lines.append(str(scene.get("qr_label") or "Full references and supporting material"))
        qr_url = conference.get("qr", {}).get("url", "")
        if qr_url:
            lines.append(qr_url)
    return "\n".join(lines)


def _poster_height(scene: dict) -> int:
    if scene.get("pptx_height_emu"):
        try:
            return int(scene.get("pptx_height_emu"))
        except (TypeError, ValueError):
            pass
    role = str(scene.get("role") or "").lower()
    if role == "header":
        return 980000
    if role in {"figure", "prisma", "network", "ranking", "forest"}:
        return 1380000
    if role in {"references", "qr"}:
        return 840000
    return 1080000


def _poster_layout(scenes: list[dict]) -> list[dict]:
    cols = 12
    margin_x = 300000
    margin_y = 180000
    gap_x = 90000
    gap_y = 100000
    inner_width = SLIDE_CX - (2 * margin_x) - ((cols - 1) * gap_x)
    col_width = inner_width // cols
    placed: list[dict] = []
    current_col = 0
    current_y = margin_y
    row_height = 0
    for scene in scenes:
        try:
            span = int(scene.get("span") or 3)
        except (TypeError, ValueError):
            span = 3
        span = max(2, min(cols, span))
        height = _poster_height(scene)
        if current_col + span > cols:
            current_y += row_height + gap_y
            current_col = 0
            row_height = 0
        x = margin_x + current_col * (col_width + gap_x)
        cx = span * col_width + (span - 1) * gap_x
        placed.append(
            {
                "scene": scene,
                "x": x,
                "y": current_y,
                "cx": cx,
                "cy": height,
            }
        )
        current_col += span
        row_height = max(row_height, height)
    return placed


def _poster_slide_xml(storyboard: dict, conference: dict, spec_path: Path) -> tuple[str, str, dict[str, Path]]:
    scenes = storyboard.get("scenes", [])
    placements = _poster_layout(scenes)
    base_dir = spec_path.parent
    shapes: list[str] = []
    media: dict[str, Path] = {}
    media_rel_ids: dict[str, str] = {}
    shape_id = 2
    rel_index = 1

    for item in placements:
        scene = item["scene"]
        role = str(scene.get("role") or "block").lower()
        x = int(item["x"])
        y = int(item["y"])
        cx = int(item["cx"])
        cy = int(item["cy"])

        fill = "FFFFFF"
        line = "D4E0DD"
        title_color = "0D6B5F"
        body_color = "15211F"
        if role == "header":
            fill = "0D6B5F"
            line = "0D6B5F"
            title_color = "F7F2E8"
            body_color = "F7F2E8"

        shapes.append(_rect(shape_id, x, y, cx, cy, fill, line))
        shape_id += 1

        kicker = str(scene.get("kicker") or role.upper())
        title = str(scene.get("title") or "")
        body = _poster_body_text(scene, conference)
        shapes.append(_textbox(shape_id, x + 120000, y + 70000, cx - 240000, 140000, kicker, 7, color=body_color, bold=True))
        shape_id += 1
        shapes.append(
            _textbox(
                shape_id,
                x + 120000,
                y + 190000,
                cx - 240000,
                340000 if role == "header" else 220000,
                title,
                24 if role == "header" else 16,
                color=title_color,
                bold=True,
            )
        )
        shape_id += 1

        image_path = _resolve_media_path(base_dir, scene.get("image_path") or scene.get("qr_path"))
        if image_path:
            key = str(image_path.resolve())
            if key not in media_rel_ids:
                media_rel_ids[key] = f"rId{rel_index}"
                media[key] = image_path
                rel_index += 1
            rel_id = media_rel_ids[key]
            if scene.get("qr_path"):
                pic_w = min(960000, cx // 3)
                pic_h = pic_w
                pic_x = x + 120000
                pic_y = y + 340000
                text_x = pic_x + pic_w + 100000
                text_cx = cx - (text_x - x) - 120000
                shapes.append(_picture(shape_id, rel_id, pic_x, pic_y, pic_w, pic_h, image_path.name))
                shape_id += 1
                shapes.append(_textbox(shape_id, text_x, y + 340000, text_cx, cy - 460000, body, 11, color=body_color))
                shape_id += 1
            else:
                text_h = 430000 if role == "header" else 420000
                shapes.append(_textbox(shape_id, x + 120000, y + 430000, cx - 240000, text_h, body, 10, color=body_color))
                shape_id += 1
                pic_y = y + 430000 + text_h + 50000
                pic_h = max(360000, cy - (pic_y - y) - 120000)
                shapes.append(_picture(shape_id, rel_id, x + 120000, pic_y, cx - 240000, pic_h, image_path.name))
                shape_id += 1
        else:
            shapes.append(_textbox(shape_id, x + 120000, y + 430000, cx - 240000, cy - 530000, body, 10, color=body_color))
            shape_id += 1

    slide_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {''.join(shapes)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""

    rel_lines = []
    media_targets: dict[str, str] = {}
    for index, (media_key, media_path) in enumerate(media.items(), start=1):
        rel_id = media_rel_ids[media_key]
        ext = media_path.suffix.lower()
        media_name = f"image{index}{ext}"
        media_targets[media_key] = media_name
        rel_lines.append(
            f'<Relationship Id="{rel_id}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            f'Target="../media/{media_name}"/>'
        )
    slide_rels = (
        f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PKG_R_NS}">
  {''.join(rel_lines)}
</Relationships>"""
        if rel_lines
        else ""
    )
    packaged_media = {
        media_targets[key]: value
        for key, value in media.items()
    }
    return slide_xml, slide_rels, packaged_media


def export_editable_pptx(
    spec_path: Path,
    output_path: Path,
    kind: str,
    conference_path: Path | None = None,
) -> dict:
    spec_path = Path(spec_path)
    output_path = Path(output_path)
    storyboard = load_structured_file(spec_path)
    conference = load_structured_file(Path(conference_path)) if conference_path else {}
    scenes = storyboard.get("scenes", [])
    if not scenes:
        return {"status": "blocked", "message": "storyboard.yaml has no scenes to export."}

    slide_xmls: list[str] = []
    slide_rels: list[str] = []
    packaged_media: dict[str, Path] = {}
    slide_count = 0

    if kind == "poster":
        slide_xml, rel_xml, media = _poster_slide_xml(storyboard, conference, spec_path)
        slide_xmls.append(slide_xml)
        slide_rels.append(rel_xml)
        packaged_media.update(media)
        slide_count = 1
    else:
        for idx, scene in enumerate(scenes, start=1):
            title = str(scene.get("title") or f"Slide {idx}")
            body = str(scene.get("body") or scene.get("message") or "")
            notes = str(scene.get("speaker_notes") or "")
            slide_xmls.append(_slide_xml(title, body, notes))
            slide_rels.append("")
        slide_count = len(slide_xmls)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    media_exts = {Path(name).suffix.lower().lstrip(".") for name in packaged_media}
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as pptx:
        pptx.writestr("[Content_Types].xml", _content_types(slide_count, media_exts))
        pptx.writestr("_rels/.rels", _root_rels())
        pptx.writestr("ppt/presentation.xml", _presentation_xml(slide_count))
        pptx.writestr("ppt/_rels/presentation.xml.rels", _presentation_rels(slide_count))
        pptx.writestr("docProps/article-machine.json", _metadata_json(storyboard, conference, kind))
        pptx.writestr("ppt/notes/article-machine-notes.md", _notes_markdown(storyboard, conference))
        for idx, slide_xml in enumerate(slide_xmls, start=1):
            pptx.writestr(f"ppt/slides/slide{idx}.xml", slide_xml)
            rel_xml = slide_rels[idx - 1]
            if rel_xml:
                pptx.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", rel_xml)
        for media_name, media_path in packaged_media.items():
            pptx.write(media_path, f"ppt/media/{media_name}")

    return {
        "status": "pass",
        "path": str(output_path),
        "kind": kind,
        "slide_count": slide_count,
        "editability": "text-boxes-editable",
        "metadata": "docProps/article-machine.json",
        "notes": "ppt/notes/article-machine-notes.md",
        "animation_policy": "complex HTML motion is degraded to editable static poster blocks or build-step slides",
    }
