# Citation And Reference Style Extension

Use this reference when a Portuguese scientific output needs ABNT, Vancouver/ICMJE/NLM, APA, IEEE, Chicago, AMA or another citation/reference style. This file is a routing and safety guide, not a replacement for paid standards or journal instructions.

## Authority Order

1. Portal or journal/congress instructions for the exact submission.
2. Current official style manual or standard.
3. Institutional library guide that explicitly names the edition used.
4. Reference manager output, only after manual metadata checks.

If these conflict, do not silently choose. State the conflict and follow the destination rule.

## ABNT Family

Use ABNT mainly for Brazilian theses, dissertations, TCCs, monographs, institutional reports and coursework. Do not assume a Brazilian journal wants ABNT; many health journals require Vancouver/ICMJE.

Current anchors to verify before formatting:

- `ABNT NBR 6023:2025`: references. It supersedes the 2018 edition plus the 2025 amendment. Use it for the reference list unless the institution explicitly freezes an older version.
- `ABNT NBR 10520:2023`: in-text citations.
- `ABNT NBR 14724:2024`: academic work presentation.
- `ABNT NBR 6028:2021`: abstracts, reviews and recensions.
- Related academic-work standards may include `NBR 6024`, `NBR 6027`, `NBR 6034`, `NBR 12225` and IBGE table rules when the deliverable is a thesis or dissertation.

Operational rules:

- Choose author-date or numeric citation mode according to the institution; do not mix.
- Direct quotation needs location detail when the rule requires it. If page/location is missing, do not invent it.
- Use `apud` only when the original source was not accessible; prefer retrieving the original.
- For Brazilian academic work, check whether the institution requires uppercase author names, local punctuation conventions, access date wording, DOI placement and typography. These details vary in local templates.
- Do not reproduce large sections of ABNT standards in generated files. Point to licensed ABNT access, Target GEDWeb, institutional library pages or official catalog records.

Minimal ABNT audit:

- Every in-text call has a matching reference.
- Every reference is cited, unless the destination allows bibliography beyond cited works.
- Edition year is explicit in the working note.
- URLs and access dates are present when required.
- DOI/URL are copied from source metadata, not guessed.

## Vancouver, ICMJE And NLM

Use this family for biomedical and health-science manuscripts when the destination asks for Vancouver, ICMJE, Uniform Requirements, NLM style or Citing Medicine.

Authority anchors:

- ICMJE Recommendations are the current medical-journal editorial baseline and were updated in January 2026.
- NLM "Samples of Formatted References" states that the recommended reference style is based on NISO Z39.29 as adapted by NLM, with fuller rules in Citing Medicine.
- NLM Citing Medicine, 2nd edition, is the detailed guide for journal articles, books, conference publications, reports, dissertations, electronic material, datasets and software.

Operational rules:

- Number citations in the order of first appearance unless the journal says otherwise.
- Keep the reference list in citation order, not alphabetical order.
- Use NLM journal title abbreviations for journals when required by the destination.
- Do not convert ABNT author-date calls into Vancouver numbers without rechecking order of first citation throughout the manuscript.
- Check author count rules, article identifiers, issue/month handling and electronic material rules against NLM/Citing Medicine or the journal instructions.
- For PubMed-indexed material, verify PMID/DOI/title/year against PubMed or Crossref before finalizing.

Minimal Vancouver audit:

- Citation numbers are consecutive and stable after edits.
- Every number points to exactly one reference.
- Repeated citations reuse the original number.
- Journal titles are abbreviated or expanded consistently with the target rule.
- DOI, PMID, PMCID, URL and access date are included only when required and verified.

## Other Common Families

Use these only when the destination asks for them:

| Style | Typical use | Core risk |
|---|---|---|
| APA 7 | psychology, education, social sciences | author-date punctuation and DOI/URL rules; do not turn into ABNT author-date by accident |
| IEEE | engineering, computing, technical conferences | numeric citation order and bracketed references; do not use Vancouver journal abbreviation rules blindly |
| Chicago | humanities, history, books, some social sciences | choose notes-bibliography or author-date before editing |
| AMA | medicine and allied health venues that name AMA, not just "Vancouver" | superscript numeric details and AMA-specific reference rules |

## Conversion Workflow

1. Freeze the target style and edition in a short working note.
2. Export or inspect current references as BibTeX/RIS/CSL-JSON when available.
3. Validate metadata against DOI, PubMed, Crossref, journal pages, books, theses or official reports.
4. Convert citation calls and reference list together. Never convert one without the other.
5. Re-run a citation consistency pass after any paragraph movement.
6. Preserve Evidence Lock: formatted references do not prove the cited claim is supported.

## Failure Modes

- "ABNT" used for a journal that asked for Vancouver.
- Vancouver references alphabetized instead of ordered by first citation.
- ABNT 2018 applied after a 2025 update without institutional justification.
- DOI fabricated from a title search.
- Journal title abbreviation copied from a random generator instead of NLM/PubMed or destination instructions.
- References formatted beautifully but missing from `drafts/references.bib`.
- Claim map cites one source while the manuscript citation points to another.

## Source Anchors

- ABNT catalog or licensed institutional access for current NBR text.
- NLM Samples of Formatted References: https://www.nlm.nih.gov/bsd/uniform_requirements.html
- NLM Citing Medicine: https://www.ncbi.nlm.nih.gov/books/NBK7256/
- ICMJE Recommendations: https://icmje.org/recommendations/
- APA Style references: https://apastyle.apa.org/style-grammar-guidelines/references
- IEEE Editorial Style Manual and Reference Guide: https://journals.ieeeauthorcenter.ieee.org/your-role-in-article-production/ieee-editorial-style-manual/
- Chicago citation guide: https://www.chicagomanualofstyle.org/tools_citationguide.html
