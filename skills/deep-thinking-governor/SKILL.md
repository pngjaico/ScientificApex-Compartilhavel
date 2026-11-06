---
name: deep-thinking-governor
description: Use when a scientific, clinical, analytical, manuscript, grant, thesis, or Article Machine decision needs deeper reasoning before action including hypothesis comparison, causal caution, alternative explanations, premortem, steelman/red-team, assumption audit, decision matrix, uncertainty mapping, or when the user asks for deep thinking, pensar profundamente, raciocínio profundo, análise crítica, não seja superficial, deixe perfeito, or strong conclusions. Do not reveal hidden chain-of-thought; produce a concise reasoning audit and decision-ready summary.
---

# Deep Thinking Governor

## Purpose

Force deliberate scientific reasoning before conclusions, implementation, manuscript claims, or irreversible workflow choices. This skill is not a license to be verbose; it is a gate for better decisions.

## Mandatory Flow

1. Identify the active `projects/<project_id>/` when the task touches evidence, analysis, discovery, manuscript, thesis, grant, deck, poster, or submission.
2. State the decision or claim being tested in one sentence.
3. Map the evidence surface: what is known, what is missing, what is only assumed, and what would change the conclusion.
4. Generate at least three competing options or hypotheses, including a null/status-quo option when applicable.
5. Steelman the best opposing view before selecting a direction.
6. Red-team the preferred option for bias, leakage, overclaiming, feasibility, cost, data quality, and external validity.
7. Produce a decision summary with:
   - preferred option;
   - rejected options and why;
   - assumptions that must stay visible;
   - stop conditions;
   - next test or verification.

## Article Machine Contract

- Use `scientific-critical-thinking` for methodological critique and evidence-quality assessment.
- Use `hypothesis-tournament` when the task is idea generation or hypothesis ranking.
- Use `scientific-red-team-reviewer` before strong claims, submission, thesis, congress, or publication.
- Use `agent-benchmark-harness` before accepting claims like perfect, production-grade, best, or world-class.
- Save persistent reasoning artifacts under `reviews/deep_thinking/` or `context/task_packets/` only when the task creates durable project state.

## Output Rule

Do not expose hidden chain-of-thought. Return a concise reasoning audit: assumptions, options, tradeoffs, selected path, residual risks, and verification plan.

## Reference

Read `references/deep-thinking-protocol.md` when the task is high-stakes, ambiguous, or asks for "perfeito".
