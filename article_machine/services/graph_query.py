"""Typed, privacy-filtered queries over the operational graph."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from time import perf_counter
from typing import Any

BLOCKED_TERMS = ("raw", "patient", "pacient", "fulltext", "full-text", "pdf", "dump")
VALID_SCOPES = ("control-plane", "skills")


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _tokens(value: str) -> set[str]:
    normalized = "".join(
        character for character in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(character)
    )
    aliases = {
        "grafo": "graph",
        "evidencia": "evidence",
        "protocolo": "protocol",
        "revisao": "review",
        "roteamento": "routing",
        "modelo": "model",
        "maquina": "machine",
        "cientifico": "scientific",
    }
    tokens = {part for part in re.findall(r"[a-z0-9][a-z0-9_-]*", normalized) if len(part) > 1}
    return tokens | {aliases[token] for token in tokens if token in aliases}


def _allowed(node: dict[str, Any], scope: str) -> bool:
    source = str(node.get("source_file") or "").replace("\\", "/")
    label = str(node.get("label") or "")
    haystack = f"{source} {label}".lower()
    if any(term in haystack for term in BLOCKED_TERMS):
        return False
    if scope == "skills":
        return source.startswith("skills/") or source == "article_machine/agent_skills.py"
    if scope == "control-plane":
        return source.startswith((".agents/", ".codex/", "docs/", "article_machine/", "scripts/")) or source in {
            "AGENTS.md",
            "AGENT_MANIFEST.md",
            "SKILL_INDEX.md",
            "SKILLS_CANON.md",
        }
    if scope.startswith("project:"):
        project_id = scope.split(":", 1)[1]
        return source.startswith(f"projects/{project_id}/")
    return False


def query_operational_graph(
    query: str,
    *,
    scope: str = "control-plane",
    limit: int = 10,
    graph_path: Path | None = None,
) -> dict[str, Any]:
    if scope not in VALID_SCOPES and not scope.startswith("project:"):
        raise ValueError(f"unsupported graph scope: {scope}")
    if scope.startswith("project:") and not scope.split(":", 1)[1]:
        raise ValueError("project graph scope requires a project id")
    started = perf_counter()
    path = graph_path or _root() / "graphify-out" / "graph.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    query_tokens = _tokens(query)
    candidates: list[dict[str, Any]] = []
    for node in payload.get("nodes", []):
        if not _allowed(node, scope):
            continue
        label = str(node.get("label") or "")
        source = str(node.get("source_file") or "")
        token_overlap = len(query_tokens & _tokens(f"{label} {source}"))
        substring_bonus = 2 if query.lower().strip() and query.lower().strip() in f"{label} {source}".lower() else 0
        degree = int(node.get("degree", 0) or 0)
        if token_overlap == 0 and substring_bonus == 0:
            continue
        score = token_overlap * 10 + substring_bonus + min(degree, 20) / 20
        if score <= 0:
            continue
        candidates.append(
            {
                "id": node.get("id") or node.get("operational_id"),
                "label": label,
                "source_file": source,
                "community": node.get("community"),
                "score": round(score, 3),
            }
        )
    candidates.sort(key=lambda item: (-item["score"], item["label"], str(item["id"])))
    return {
        "status": "ok",
        "scope": scope,
        "query": query,
        "results": candidates[: max(1, limit)],
        "candidate_count": len(candidates),
        "elapsed_ms": round((perf_counter() - started) * 1000, 3),
        "privacy_filter": "raw/patient/fulltext/pdf/dump nodes excluded",
    }
