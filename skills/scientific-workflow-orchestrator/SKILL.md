---
name: scientific-workflow-orchestrator
description: Use when planning complex scientific work, systematic reviews, meta-analysis, cohort or trial analysis, scientific hypotheses, reproducible research, or trabalhos científicos complexos with coordinated agents.
---

# Scientific workflow orchestration

Read the active project's four contracts. Run `article-machine workflow plan
<project> --query "..." --language en|pt-BR`. A plan organizes work; execution
and transitions require the existing lifecycle and stage gates.

The coordinator (GPT-6.1 Sol medium) owns question framing, protocol, design,
statistical decisions, interpretation and final review. Delegate bounded file
and metadata extraction to Luna low, implementation and tests to Luna medium,
and focused evidence comparisons to Luna high. Every assignment declares inputs,
allowed tools, file ownership, expected artifacts and verification. Use Sol high
for scientific review and difficult method decisions. Record actual runtime.

For hypotheses compare novelty, feasibility, falsifiability, confounding and
expected information gain. Record competing explanations and a negative-result
plan before ranking ideas. Verify novelty with a dated reproducible search.

Follow protocol -> retrieval -> deduplication/screening -> extraction -> bias
assessment -> analysis -> claims -> writing -> Review Trinity -> red-team.
Use guidelines appropriate to study type from standards.yaml. Preserve protocol
deviations and dates; keep study identifiers and decisions traceable.

Full text, database and plugin outputs enter the source registry with hashes
and locators. They become manuscript claims only after support assessment and
Evidence Lock. Analysis uses declared locked runtimes and a run manifest.
Do not invent citations, statistics, eligibility decisions or completed searches.

Output: context/scientific_workflow_plan.json, context/scientific_workflow_packet.md,
analysis manifests and reviews under the active project. Missing optional plugins
produce a documented provider fallback; missing required evidence blocks claims.
