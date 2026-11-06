# Decision pathway for design, question, and registration

This guide supports planning. It does not automatically choose a method or infer a topic from older protocols or questions.

## 1. Is the work an evidence review?

- **Focused question about intervention/effect or exposure with comprehensive searching and reproducible methods:** consider a systematic review. PICO/PICOS is useful when population, intervention/exposure, comparator, and outcomes are defined. Meta-analysis is not mandatory; pool only clinically and methodologically compatible evidence.
- **Map concepts, evidence types, definitions, or gaps using a broad question:** consider a scoping review. PCC often structures population, concept, and context. JBI guides conduct; PRISMA-ScR guides reporting. Study counts do not prove benefit.
- **Explain context, mechanism, history, or a broad debate:** a narrative review can fit if scope, source selection, and limitations are explicit. Do not call it systematic unless its search/selection meet that method.
- **A decision-useful synthesis is needed on a short timeline:** consider a rapid review only if restrictions (sources, dates, languages, reviewers, omitted steps) are prespecified and justified. Speed does not remove bias; report deviations and effects on confidence.
- **Relevant systematic reviews already exist:** an overview/umbrella review can synthesize them. Set criteria, do not silently mix primary studies, map overlap, and appraise the quality/risk of bias of included reviews.
- **New evidence is likely and continued updating is sustainable:** a living review is a way to maintain a systematic review, not a separate method. Define surveillance, triggers, cycles, versioning, and closure; do not promise continuity without team and resources.
- **Diagnostic test against a reference standard:** use a diagnostic accuracy review; plan thresholds, population, reference standard, paired sensitivity/specificity, QUADAS-3 v1.2, and a bivariate/HSROC model when compatible. Reserve QUADAS-2 for a specified historical assessment or dated requirement.
- **Time course or prognostic factors:** define event, horizon, source population, censoring, and competing risks; choose QUIPS for factors or PROBAST/PROBAST+AI for models, as appropriate.
- **Three or more interventions connected in a network:** use NMA only when network, transitivity, and consistency/coherence are defensible; define nodes and modifiers before looking at rankings.
- **None of these fits:** state and justify the synthesis type; do not force a familiar label.

PRISMA is reporting guidance, not a conduct method or validity seal. For a systematic review, use PRISMA-P while preparing the protocol, applicable method-specific guidance, and the relevant reporting checklist for the manuscript. Check current extensions and versions.

## 2. Does the question need a primary study?

- **Allocated intervention:** define trial design, randomization, concealment, comparator, estimand, outcome, horizon, safety, contamination, and ethics. Use SPIRIT 2025 for the protocol and CONSORT 2025 for results reporting, with applicable extensions; older versions only for historical context or a dated requirement. A specific trial registry and ethics approval may be additional obligations; PROSPERO/OSF do not replace them.
- **Non-allocated exposure:** choose cohort, case-control, cross-sectional, or another design based on the temporal question and data source; define confounders, selection bias, estimand, and causal-inference limits.
- **Diagnosis:** index test, threshold, reference standard, sampling, verification, and participant spectrum.
- **Prognosis/future risk:** target population, prediction time, horizon, event, available predictors, and validation.
- **Prediction model/ML:** state intended use and decision, comparator, temporal/geographic validation, and leakage prevention at each step. Performance does not imply clinical benefit.
- **Simulation or preclinical study:** specify system, unit, model, and intended external validity; do not extrapolate to people without appropriate validation.
- For another design, state the logic connecting question to unit, sample, and method. Do not derive it from existing questions.

## 3. Registration choice and start boundary

1. Complete the questionnaire and protocol during preparation/bootstrap or protocol freeze. These planning stages are allowed before registration.
2. For a health systematic review, check current PROSPERO eligibility; do not assume acceptance because the topic is medicine. An ineligible protocol should use OSF Registries or an appropriate registry.
3. For primary observational, prediction/ML, simulation, and other scientific projects outside PROSPERO scope, use a final OSF registration under local policy. Also check institutional and journal requirements.
4. For a clinical trial, use OSF/PROSPERO as applicable and also register in an applicable recognized public trial registry; check ethics-board approval, consent, and legal requirements before recruitment/intervention.
5. Finalize and compare protocol, form, attachments, and methods. Submit externally only with specific appropriate authorization; never upload identifiable participant data.
6. Wait for final registry confirmation. A draft, OSF project, pending submission, project DOI, protocol manuscript, or fictitious number does not meet local policy.
7. Archive a dated snapshot of the final registry record inside the project, calculate SHA-256, and have a named reviewer check registry identity and correspondence with the frozen protocol.
8. Use the local registry register command to declare metadata for a registration already completed; it does not submit anything. Use registry verify to check reviewed local evidence and its hash. Only then can the local gate permit scientific work.
9. Before corpus building, formal search/screening, extraction, analysis, discovery, or scientific writing, check the gate. If the protocol changes later, document an amendment, reason, and impact; reassess registration, ethics, and fingerprint before resuming.

**Stricter workspace policy:** requires a reviewed final PROSPERO or OSF registration before any scientific work, even if a journal or registry accepts later submission. Never call retrospective registration prospective. Local verification checks documentary consistency and SHA-256; by itself it does not prove external authenticity or scientific validity.

## Official sources consulted

- [PROSPERO — registration guidance and eligibility](https://www.crd.york.ac.uk/prospero/documents/Registering%20a%20review%20on%20PROSPERO.pdf)
- [OSF — registrations and preregistrations](https://help.osf.io/article/330-welcome-to-registrations)
- [PRISMA-P — systematic review protocols](https://www.prisma-statement.org/protocols)
- [PRISMA — scoping extension](https://www.prisma-statement.org/scoping)
- [EQUATOR — reporting guidelines](https://www.equator-network.org/reporting-guidelines/)
- [PROBAST/PROBAST+AI](https://www.probast.org/)
- [QUADAS-3 v1.2 — Bristol](https://www.bristol.ac.uk/population-health-sciences/projects/quadas/quadas-3/)
- [SPIRIT 2025/CONSORT 2025](https://www.consort-spirit.org/)
