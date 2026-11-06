---
name: stage-audit-governor
description: Use when checking project modes, mode advancement, submission readiness, task packets, protocol freeze, corpus build, extraction, analysis, Evidence Lock, Review Trinity, benchmark, or journal route gates.
---

# Stage Audit Governor

Use this skill whenever a project may advance from one mode to another.

## Gate
- Run `article-machine stage audit <project_dir> --target-mode <mode>`.
- Run `article-machine guard check <project_dir>` before strong readiness claims.
- Submission requires Review Trinity, journal route, and benchmark evidence.

## Mode Coverage
- `bootstrap`: project, protocol, standards, compute
- `protocol-freeze`: research question, objectives, frozen protocol
- `corpus-build`: query plan and retrieval plan
- `screening`: registry
- `extraction`: extraction manifest
- `analysis`: analysis manifest
- `drafting`: Evidence Lock
- `review-trinity`: aggregate review pass
- `submission`: journal route and benchmark pass
