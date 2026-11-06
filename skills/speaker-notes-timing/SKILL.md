---
name: speaker-notes-timing
description: Use when fitting scientific slides to a strict oral presentation duration or generating speaker notes for a congress talk.
---

# Speaker Notes Timing

Turn a storyboard into a timed oral script.

## Profiles
- `3-min`: 3 to 4 slides, one message per slide.
- `5-min`: up to 6 slides, concise problem-method-finding-implication structure.
- `10-min`: up to 10 slides, room for one methods slide and multiple findings.
- `15-min`: up to 15 slides, add nuance and limitations.

## Contract
- Every slide needs `duration_seconds` and `speaker_notes`.
- Total duration must not exceed `conference.yaml.presentation.duration_minutes`.
- Notes must not introduce unsupported factual claims.
- Put details in backup slides only after the main talk fits.
