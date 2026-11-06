# Distribution verification

Date: 2026-11-06. Scope: Article Machine 0.3.0 core on Windows.

- Locked installation in a clean local clone in a different directory: PASS.
- CLI and strict operational machine audit in that clone: PASS.
- Selected core suite: 84 tests PASS, covering lifecycle guards, registration,
  contracts, evidence, reviews, metrics and portability regressions.
- AI-disclosure scaffolds do not presume a provider and explicitly retain
  pending author verification: regression test PASS.
- Documentary license scope: PASS for 117 skills; 65 original-layer components
  released under Apache-2.0 and 52 third-party components retaining upstream terms.
- Shell installer syntax checked with Bash; no local Unix/macOS execution.
  CI is configured for Windows and Linux. Check Actions for the commit's remote
  result rather than inferring macOS support.
- PROSPERO author/contact/affiliation do not inherit an identity: targeted test PASS.
- Operational graph with absent optional documents: PASS; relationships to absent
  entities are omitted and counted in the graph manifest.
- Source selection excludes original study projects, research data, manuscripts,
  researcher profile, credentials and original Git history.
- Targeted personal-identifier search found no remaining owner identifiers in the
  distributed text. Textual XML in 24 DOCX templates was also checked.
- Secret detector: 581 candidates in 32 files. Reviewed candidates were hashes,
  upstream metadata, public IDs, placeholders and fixtures; no real credential
  was identified among reviewed candidates. This does not prove universal absence.

Synthetic test fixtures, blank editorial templates and third-party bibliographic
metadata remain part of the software. Public upstream maintainer contacts and
license notices are preserved.

Not executed: R, ML/DL, browser/Quarto, Zotero, external APIs and remote catalogs,
clinical validation, human review of all templates, and agent/editor layout QA.
No third-party computer or Linux/macOS was tested. The clean clone was installed
on the same computer using an existing uv cache; future package availability
and other environments are not established by this test.
