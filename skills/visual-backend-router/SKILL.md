---
name: visual-backend-router
description: Use when choosing how to generate or render scientific visuals, diagrams, hero images, charts, tables, or poster assets.
---

# Visual Backend Router

Choose the backend by asset type and evidence requirements.

## Routing
- Technical diagram, pathway, flowchart: `scientific-schematics`.
- Chart, table, forest plot, network plot: local Python/R pipeline.
- Hero, title illustration, poster background: GPT Image/OpenRouter/Flux if configured, otherwise HTML/CSS.
- Editable layout element: HTML/CSS first.

## Contract
- Every asset needs `asset_id`, `type`, `purpose`, `source_claim_ids`, `backend`, and `status`.
- Data-derived visuals must point back to the analysis artifact or claim IDs.
- Do not use raster AI images for primary quantitative evidence.

## Python Hook
```python
from article_machine.visuals import route_visual_backend
```
