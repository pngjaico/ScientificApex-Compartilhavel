from __future__ import annotations

import os


def route_visual_backend(asset_type: str, preferred: str | None = None) -> dict:
    """Route a visual asset to the safest available generation backend."""
    normalized = (asset_type or "").strip().lower().replace("_", "-")
    if preferred:
        return {
            "status": "selected",
            "asset_type": normalized,
            "backend": preferred,
            "skill": preferred,
            "reason": "Explicit preferred backend was provided.",
        }

    if normalized in {"technical-diagram", "diagram", "schematic", "flowchart", "pathway"}:
        return {
            "status": "selected",
            "asset_type": normalized,
            "backend": "scientific-schematics",
            "skill": "scientific-schematics",
            "reason": "Technical scientific diagrams should remain vector/structure-first.",
        }
    if normalized in {"chart", "table", "forest-plot", "network-plot", "data-visualization"}:
        return {
            "status": "selected",
            "asset_type": normalized,
            "backend": "python-r-native",
            "skill": "scientific-visualization",
            "reason": "Charts and tables must be derived from local Python/R data products.",
        }
    if normalized in {"title-illustration", "hero", "illustration", "cover", "poster-background"}:
        if os.environ.get("OPENAI_API_KEY"):
            backend = "openai-gpt-image"
            reason = "OPENAI_API_KEY is configured for GPT Image generation."
        elif os.environ.get("OPENROUTER_API_KEY"):
            backend = "openrouter-image"
            reason = "OPENROUTER_API_KEY is configured for image-capable routing."
        elif os.environ.get("REPLICATE_API_TOKEN"):
            backend = "flux-or-nano-banana"
            reason = "REPLICATE_API_TOKEN is configured for Flux/Nano Banana style backends."
        else:
            backend = "html-css-native"
            reason = "No image API key is configured; use generated HTML/CSS visual treatment."
        return {
            "status": "selected",
            "asset_type": normalized,
            "backend": backend,
            "skill": "generate-image" if backend != "html-css-native" else "conference-slides-html",
            "reason": reason,
        }

    return {
        "status": "selected",
        "asset_type": normalized or "unknown",
        "backend": "html-css-native",
        "skill": "conference-slides-html",
        "reason": "Default to editable HTML/CSS assets when the asset type is ambiguous.",
    }
