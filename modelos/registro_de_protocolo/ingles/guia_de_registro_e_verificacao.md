# Operational guide to registration and local verification

## Start boundary

Preparing the question, completing this questionnaire, and freezing the protocol in **bootstrap/protocol-freeze** are allowed. For scientific projects, local policy requires a reviewed final PROSPERO or OSF registration **before** corpus building, formal searching/screening, extraction, analysis, discovery, or scientific writing. This policy is stricter than minimum timelines accepted by some registries.

A final registration means a submission that reached final accepted/published status or, on OSF, final approved status (public or embargoed under current options). A draft, OSF project, pending submission, protocol manuscript, reserved/fictitious number, or institutional repository does not replace a final registration. A clinical trial's applicable trial registry and ethics/regulatory approvals are additional obligations.

## Before external registration

1. Complete the questionnaire with the team and resolve pending questions affecting the question, eligibility, outcomes, collection, sample, estimand, analysis, privacy, or ethics.
2. Choose the registry route using the decision pathway. PROSPERO eligibility changes and must be checked against current rules/form; do not assume eligibility because the work concerns health.
3. Freeze the complete protocol, search strategy, extraction form, statistical plan, critical appraisal methods, and materials/attachments. Check that the protocol content matches the registry form responses.
4. Record authorship, contributions, funding, conflicts, ethics, sharing, and planned dates; do not invent answers to required fields.
5. Submission to PROSPERO/OSF is an external action. Do it only after the study owner authorizes and reviews the final package. Never include identifiable participant data.
6. Confirm final status on the registry itself. On OSF, a project and a registration are distinct objects; a public project does not turn a draft/pending registration into a final one. If chosen, embargo should be understood as a final private state under current OSF rules, not as absence of registration.

## Local evidence of registration

1. Save a dated copy of the final registration inside the project (for example, a print/PDF of the official page) and relevant attachments. Keep canonical URL, identifier, registration timestamp, protocol version, and amendment trail.
2. Calculate SHA-256 for the saved snapshot. Do not treat a link hash, unsaved screen, or locally held protocol as the hash of the external registry record.
3. A named reviewer compares registry, URL/ID, final status, protocol, attachments, and date; records name, review date, and match confirmation.
4. Declare locally the metadata for the registration that has already been completed externally:

```text
python -m article_machine registry register <project> --registry PROSPERO --id <real-ID> --url <canonical-final-record-URL> --registered-at <real-ISO-8601>
```

Replace every placeholder with real data only after external confirmation. For OSF, use `--registry OSF`, the real registration identifier, and canonical OSF URL. This command **does not submit** a protocol: it only writes `declared-unverified` status in `protocol.yaml`; gates remain blocked.

5. Complete a copy of the blank JSON with metadata identical to `protocol.yaml`, a relative path to the local snapshot, its SHA-256, the frozen protocol fingerprint, the reviewer's true match confirmation, literal method `reviewed-hashed-registry-record`, and real ISO 8601 timestamps. `protocol_sha256` is calculated by the service from `protocol.yaml` after excluding `registration` and `status`; do not invent it.
6. The reviewer may set `scientific_work_not_started_before_registration: true` only after reconciling the project history, including legacy files and work outside the pipeline. The service also checks `sources/registry.jsonl`, `.machine/runs/*/manifest.json`, and `.machine/scientific_start.json`; absence of these files does not prove that no work occurred. This field is a human attestation, not an automatic inference. If scientific work predates registration, set it to false and do not use the gate as if the study were prospective; resolve the situation under policy and report deviations.
7. Save the reviewed JSON inside the project and run:

```text
python -m article_machine registry verify <project> --record <local-path-to-reviewed-json>
```

8. Continue only if the command returns `status: pass` and the team confirms the review. The service imports the file, checks local consistency, dates, syntactic URL/ID identity, and hashes; writes `evidence/protocol_registration/verification.json` and updates protocol metadata.

Dates found in legacy records may block verification, but missing ledgers/manifests do not cover files or work outside the pipeline. The human statement about the full history is not automatically validated.

## What verification does and does not prove

- The service rejects IDs/hosts outside expected formats, a project/draft URL where a specific registration is required, field mismatches, a protocol changed after review, impossible dates, registration after a recorded scientific start, missing reviewer, missing file, or mismatched hash.
- It compares URL and ID locally; it does not contact the provider to authenticate the page, status, authorship, or current content. A hash proves the local file has not changed since hashing, not that the file came from the registry.
- A local review does not prove PROSPERO eligibility, methodological validity, ethics compliance, adequate sample size, or semantic fidelity.
- Keep a dated official-source snapshot and version-control the protocol and registration evidence. Recheck the external source if uncertain; this template does not perform external access or submission.

## Amendments and start of activity

If the frozen version changes, its fingerprint changes. Stop the affected scientific stage; record change, date, version, reason, decision owner, impact on outcomes/eligibility/analysis, work already started, need to amend the external registration, and ethics approval. Preserve old versions and report deviations. Repeat review and verification before resuming. Do not edit history to make the work appear prospective.

## Official references

- [PROSPERO guidance](https://www.crd.york.ac.uk/prospero/documents/Registering%20a%20review%20on%20PROSPERO.pdf)
- [OSF Registrations help](https://help.osf.io/article/330-welcome-to-registrations)
- [PRISMA-P](https://www.prisma-statement.org/protocols)
- [Implemented local policy](../../../article_machine/services/protocol_registration.py)
