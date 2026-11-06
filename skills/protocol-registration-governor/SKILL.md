---
name: protocol-registration-governor
description: Use when preregistration, PROSPERO, OSF registration, ClinicalTrials.gov registration, protocol freeze, amendments, or registry-to-manuscript consistency is needed.
---

# Protocol Registration Governor

Use this skill before corpus build, screening, extraction, analysis, discovery, or manuscript execution. This workspace applies the user's stricter registration policy to every scientific project. Protocol preparation in bootstrap/protocol-freeze and machine-governance synthetic software tests are exempt.

## Gate
- Require a final PROSPERO or OSF registration before scientific execution. An OSF project, draft, submitted-but-pending record, protocol manuscript or institutional repository alone does not satisfy this local policy.
- Use `registry register` only to declare metadata: it deliberately leaves status `declared-unverified`. Use `registry verify <project> --record <project-local-json>` after a named reviewer checks the actual final registry record. Read `article_machine/services/protocol_registration.py` for the schema and `modelos/registro_de_protocolo/` for paired questionnaires.
- Preserve a local dated registry snapshot, SHA256, reviewer, verification date and frozen-protocol fingerprint. Review hashes prove local consistency, not external registry authenticity. Never fabricate registration IDs, signatures, reviewer decisions or prospective status.
- Compare `protocol.yaml` against registry records, protocol PDFs, amendments, and dated snapshots.
- Record registry URL, identifier, registered_at, amendment history, and unresolved deviations in `protocol.yaml`.
- Block "prospective", "registered", "prespecified", or "protocol-driven" wording unless the registry evidence supports it.

## Registry Routes
- Systematic review: PROSPERO when eligible; otherwise final OSF registration.
- Clinical trial: OSF/PROSPERO as applicable to the workspace policy PLUS an appropriate recognized trial registry and ethics approval when required. OSF does not replace trial registration.
- Observational, secondary-data, prediction, simulation or preclinical study: final OSF registration, with applicable additional ethics/venue obligations.
- Registry submission is an external action: prepare a reviewable protocol first and obtain study-specific authorization before submitting. Never upload patient data to a registration.

## Required Outputs
- `context/protocol_registration_audit.md`
- registry metadata in `protocol.yaml`
- deviations table when methods changed after protocol freeze
- Paired Portuguese/English deliverables, with Portuguese filenames; identical numbers, IDs and references. Record amendments before resuming when the protocol fingerprint changes.

## Red Flags
- Registering after extraction and calling the study prospective.
- Hiding amendments that affect outcomes, eligibility, or analysis plan.
- Citing a registry page without a dated snapshot or retrieval manifest.
