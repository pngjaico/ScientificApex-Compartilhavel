# Zotero And Article Machine Bridge

## What Zotero Is Good For

- Keeping a curated reference library.
- Exporting BibTeX/CSL metadata.
- Searching titles, creators, tags, collections, and indexed full text.
- Providing local attachment paths when PDFs are already in the user's Zotero library.
- Importing BibTeX/RIS records when the user explicitly asks to add them.

## What Zotero Does Not Prove

- A Zotero item is not evidence support by itself.
- A full-text attachment does not mean the claim was checked.
- A formatted reference can still cite the wrong source.
- Zotero cannot lawfully bypass paywalls; use open-access resolvers and user-provided PDFs.

## Project Artifact Layout

- `sources/zotero/inventory.json`: library or collection snapshot.
- `sources/zotero/search_<slug>.json`: Zotero search output.
- `sources/zotero/export_<date>.bib`: raw Zotero export.
- `sources/zotero/fulltext/<item_key>.txt`: indexed full text when requested.
- `drafts/references.bib`: manuscript bibliography synchronized from checked records.
- `evidence/claim_map.jsonl`: only supported claims with `reference_key` and source excerpt.

## Local Desktop Readiness

On this workstation, the reliable executable path is
`C:\Program Files\Zotero\zotero.exe`. If the plugin helper reports
`local_api_enabled_pref: true` but `api_running: false`, start Zotero from that
absolute path, wait, then rerun `status --json` or `probe --json`.

## Full-Text Policy

Use full text in this order:

1. Local Zotero indexed full text when present.
2. Local attachment path, if the user already has the PDF.
3. Open-access resolver such as Unpaywall/Crossref.
4. User-provided PDF inbox.

Do not mass-download PDFs or commit raw full texts.
