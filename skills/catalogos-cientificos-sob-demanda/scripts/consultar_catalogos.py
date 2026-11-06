"""Search pinned metadata only. Never executes or imports upstream content."""

from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path


def normalize(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(c))


def search_catalogs(root: Path, query: str = "", source: str | None = None, limit: int = 20) -> dict:
    inventory = json.loads(
        (root / "integracoes/catalogos_cientificos/inventario_de_habilidades.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (root / "integracoes/catalogos_cientificos/manifesto_das_fontes.json").read_text(encoding="utf-8")
    )
    sources = {s["id"]: s for s in manifest["sources"]}
    if source and source not in sources:
        raise ValueError("Unknown catalog source")
    tokens = normalize(query).split()
    results = []
    for item in inventory["sources"]:
        sid = item["source_id"]
        if source and sid != source:
            continue
        if item["pinned_sha"] != sources[sid]["head_sha"]:
            raise ValueError("Inventory/manifest revision drift")
        for entry in item.get("entries", []):
            text = normalize(entry["name"] + " " + entry["path"])
            score = sum(token in text for token in tokens)
            if normalize(query) == normalize(entry["name"]) and tokens:
                score += 10
            if tokens and not score:
                continue
            results.append(
                {
                    **entry,
                    "source_id": sid,
                    "pinned_sha": item["pinned_sha"],
                    "repository": sources[sid]["repository"],
                    "score": score,
                    "execution_authorized": False,
                }
            )
    results.sort(key=lambda row: (-row["score"], row["source_id"], row["name"]))
    return {
        "status": "metadata-only",
        "sources_available": sorted(sources),
        "query": query,
        "total_matches": len(results),
        "entries": results[: max(1, min(limit, 100))],
        "warning": "Tree presence is not executable validation; "
                   "InternScience is a submodule index, not own SKILL.md entries.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--busca", default="")
    parser.add_argument("--fonte")
    parser.add_argument("--limite", type=int, default=20)
    args = parser.parse_args()
    root = next(
        parent for parent in Path(__file__).resolve().parents if (parent / "integracoes/catalogos_cientificos").is_dir()
    )
    print(json.dumps(search_catalogs(root, args.busca, args.fonte, args.limite), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
