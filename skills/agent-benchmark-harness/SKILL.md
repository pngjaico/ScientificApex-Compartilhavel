---
name: agent-benchmark-harness
description: Use when evaluating Article Machine, agent skills, scientific workflows, retrieval quality, claim accuracy, reproducibility, slides/posters, discovery pipelines, or comparing agent outputs against benchmark cases and regression tests.
---

# Agent Benchmark Harness

Use this skill to prove capabilities with repeatable tests instead of impressions.

## Workflow
1. Define benchmark task, expected artifacts, allowed tools, scoring rubric, and failure gates.
2. Use fixed input datasets or projects whenever possible.
3. Score output on correctness, provenance, guideline compliance, reproducibility, safety, and usefulness.
4. Track cost, runtime, retries, missing artifacts, and hallucinated claims.
5. Add regression tests for bugs found during benchmarking.

## Benchmark Families
- PRISMA review
- diagnostic QUADAS-2 review
- R meta-analysis
- drug discovery target/compound triage
- intestinal digital twin simulation
- congress deck/poster export
- replay/provenance audit

## Artifact Contract
Write the machine-readable result to `analysis/benchmark_report.json`.
Use `AgentBenchmarkReportV2`. Every run records a unique run ID, actual model
and effort, prompt, duration, exit code and hashes for fixture, protocol, output,
gold answer and rubric. File-backed artifact paths are confined to the report
directory and their hashes must match the actual bytes. Record tools, retries
and available token/cost telemetry; absent telemetry cannot support efficiency
or superiority claims. Non-deterministic cases need independent repeated runs.

`benchmark aggregate` and `benchmark validate` ignore producer-declared pass
flags and scorecards. The implemented `exact-json-v1` evaluator compares parsed
output with the gold answer and verifies artifact integrity/replay. Its scope is
`deterministic-artifact-regression`, not scientific acceptance. It cannot score
clinical safety or usefulness, so those dimensions remain unassessed and block
scientific submission. Rubric booleans are not independent scientific review.

Scientific acceptance requires an independently evaluated scientific benchmark
with methods, evidence and residual risks. That evaluator is not provided by
the exact-JSON regression harness. V1/smoke/comparative snapshots remain readable
but cannot unlock gates. Validate with `article-machine benchmark validate
<project>`; blocked validation exits nonzero.

## Gate
Do not claim "best", "perfect", or "production ready", and do not unlock
submission, without a validator-passing acceptance report and residual-risk
notes. A self-declared `status: pass` is not benchmark evidence.
