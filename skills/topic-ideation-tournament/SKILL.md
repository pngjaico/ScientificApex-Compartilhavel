---
name: topic-ideation-tournament
description: Use when generating, comparing, ranking, or rejecting manuscript topics, research questions, thesis ideas, database-driven projects, or publication strategies.
---

# Topic Ideation Tournament

Use this skill to prevent attractive but weak ideas from becoming projects.

## Gate
- Save candidates in `context/ideas/idea_candidates.json`.
- Run `article-machine idea tournament <project_dir>`.
- Do not promote an idea unless it has `novelty_status`, `database_plan`, and `red_team_notes`.

## Scoring Inputs
- novelty
- feasibility
- database availability
- journal fit
- moderate author fit
- ethical risk
- statistical risk
- publication chance

## Required Skepticism
- A prestigious journal fit does not rescue a weak design.
- A searchable database does not guarantee usable variables.
- A famous author name is not author fit unless identity and topic evidence are verified.
