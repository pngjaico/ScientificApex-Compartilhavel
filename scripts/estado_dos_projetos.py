"""Gera o painel de estado dos projetos a partir dos project.yaml.

Uso:
    python scripts/estado_dos_projetos.py            # grava docs/ESTADO_DOS_PROJETOS.md
    python scripts/estado_dos_projetos.py --check    # falha se o painel estiver desatualizado
    python scripts/estado_dos_projetos.py --stdout   # imprime sem gravar

O script nao altera projetos: apenas le project.yaml, protocol.yaml,
standards.yaml, compute.yaml e conta artefatos.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
DEFAULT_OUT = ROOT / "docs" / "ESTADO_DOS_PROJETOS.md"


def load_yaml(path: Path) -> dict:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return payload if isinstance(payload, dict) else {}


def count_files(path: Path, *, recursive: bool = True) -> int:
    if not path.is_dir():
        return 0
    pattern = "**/*" if recursive else "*"
    return sum(1 for item in path.glob(pattern) if item.is_file())


def project_row(project_dir: Path) -> dict[str, object]:
    contract = load_yaml(project_dir / "project.yaml")
    state = contract.get("state") or {}
    release = contract.get("release") or {}
    updated = str(contract.get("updated_at") or "")[:10]
    if not updated:
        updated = datetime.fromtimestamp((project_dir / "project.yaml").stat().st_mtime).strftime("%Y-%m-%d")
    return {
        "id": str(contract.get("id") or project_dir.name),
        "name": str(contract.get("name") or project_dir.name),
        "type": str(contract.get("project_type") or "?"),
        "lane": str(contract.get("lane") or "?"),
        "mode": str(state.get("current_mode") or "?"),
        "updated": updated,
        "protocol": (project_dir / "protocol.yaml").is_file(),
        "standards": (project_dir / "standards.yaml").is_file(),
        "compute": (project_dir / "compute.yaml").is_file(),
        "drafts": count_files(project_dir / "drafts"),
        "deliverables": count_files(project_dir / "deliverables"),
        "publicacoes": count_files(project_dir / "publicacoes"),
        "target": str(release.get("target_state") or ""),
    }


def render(rows: list[dict[str, object]]) -> str:
    rows = sorted(rows, key=lambda row: (str(row["updated"]), str(row["id"])), reverse=True)
    latest = rows[0]["updated"] if rows else "-"
    lines = [
        "# Estado dos projetos",
        "",
        "Painel gerado a partir dos `project.yaml`. Não editar à mão: rode",
        "`python scripts/estado_dos_projetos.py`.",
        "",
        f"Projetos: **{len(rows)}** · contrato mais recente: **{latest}**",
        "",
        "| Projeto | Tipo | Modo atual | Contratos | Artefatos | Atualizado |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        contracts = "".join(
            [
                "P" if row["protocol"] else "·",
                "S" if row["standards"] else "·",
                "C" if row["compute"] else "·",
            ]
        )
        artifacts = f"{row['drafts']} draft(s) · {row['deliverables']} entrega(s) · {row['publicacoes']} pub."
        lines.append(
            f"| `{row['id']}` | {row['type']} | {row['mode']} | {contracts} | {artifacts} | {row['updated']} |"
        )
    lines += [
        "",
        "Legenda dos contratos: **P** `protocol.yaml`, **S** `standards.yaml`, **C** `compute.yaml`.",
        "O ponto (`·`) indica contrato ausente e deve ser tratado antes de avançar de modo.",
        "",
        "## Contagens",
        "",
    ]
    by_type: dict[str, int] = {}
    by_mode: dict[str, int] = {}
    for row in rows:
        by_type[str(row["type"])] = by_type.get(str(row["type"]), 0) + 1
        by_mode[str(row["mode"])] = by_mode.get(str(row["mode"]), 0) + 1
    lines.append("| Tipo | Projetos |")
    lines.append("|---|---:|")
    for key, value in sorted(by_type.items()):
        lines.append(f"| {key} | {value} |")
    lines += ["", "| Modo | Projetos |", "|---|---:|"]
    for key, value in sorted(by_mode.items()):
        lines.append(f"| {key} | {value} |")
    incomplete = [row for row in rows if not (row["protocol"] and row["standards"] and row["compute"])]
    lines += ["", "## Pendências de contrato", ""]
    if incomplete:
        for row in incomplete:
            missing = [
                name
                for name, present in (
                    ("protocol.yaml", row["protocol"]),
                    ("standards.yaml", row["standards"]),
                    ("compute.yaml", row["compute"]),
                )
                if not present
            ]
            lines.append(f"- `{row['id']}`: falta {', '.join(missing)}")
    else:
        lines.append("Nenhuma: todos os projetos têm os três contratos.")

    sem_metadados = [row for row in rows if row["type"] == "?" or row["mode"] == "?"]
    lines += ["", "## Pendências de metadados", ""]
    if sem_metadados:
        for row in sem_metadados:
            missing = []
            if row["type"] == "?":
                missing.append("`project_type`")
            if row["mode"] == "?":
                missing.append("`state.current_mode`")
            lines.append(f"- `{row['id']}`: falta {', '.join(missing)}")
    else:
        lines.append("Nenhuma: todos os projetos declaram tipo e modo.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    if not PROJECTS.is_dir():
        print(f"pasta de projetos ausente: {PROJECTS}", file=sys.stderr)
        return 2

    rows = [
        project_row(path)
        for path in sorted(PROJECTS.iterdir())
        if path.is_dir() and (path / "project.yaml").is_file()
    ]
    content = render(rows)

    if args.stdout:
        print(content, end="")
        return 0

    current = DEFAULT_OUT.read_text(encoding="utf-8") if DEFAULT_OUT.exists() else ""
    if args.check:
        if current != content:
            print(f"painel desatualizado: {DEFAULT_OUT}", file=sys.stderr)
            return 1
        print("painel atualizado")
        return 0

    DEFAULT_OUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"painel gravado: {DEFAULT_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
