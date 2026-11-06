---
license: Apache-2.0
name: workspace-graph-navigator
description: Use when an agent must navigate the Doutorado workspace, query or refresh graphify-out, understand agent handoff docs, or answer architecture/navigation questions without scanning raw corpora.
---

# Workspace Graph Navigator

Use this skill before broad workspace navigation in the current repository clone.

## Purpose
- Make `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.html`, and `graphify-out/graph.json` the first navigation layer.
- Convert natural user phrasing into graph queries before walking the root manually.
- Keep root navigation operational; do not turn the whole workspace into a semantic extraction job.

## Required Flow
1. Read `docs/AGENT_START_HERE.md`.
2. Read `graphify-out/GRAPH_REPORT.md`.
3. If the graph may be stale, run `python scripts\generate_workspace_graph.py`.
4. Query with `python -m graphify query "<question>" --budget 1200`.
5. Use `graphify-out/graph.html` for visual inspection and community filtering.
6. If the task is scientific evidence, analysis, discovery, or drafting, stop navigation and switch to a `projects/<project_id>/` workflow.

## Safe Query Patterns
- `Como um agente novo deve navegar o workspace?`
- `Qual projeto ativo devo escolher para esta tarefa?`
- `Que skill cobre este pedido?`
- `Quais areas do workspace sao risco de staging ou limpeza?`
- `Como Graphify e Article Machine se conectam aqui?`

## Hard Rules
- Do not run full-root semantic graph extraction by default.
- Do not ingest raw PDFs, patient/source dumps, full text, or legacy folders into a new graph unless the user explicitly scopes that project and accepts the risk.
- Do not claim graph edges are scientific evidence. `INFERRED` edges are navigation/risk inferences only.
- Do not move or rewrite content while navigating.
