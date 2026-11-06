---
name: zotero-reference-manager
description: Use when Article Machine projects need Zotero integration, local Zotero Desktop API checks, Zotero library search, collection/tag inventory, BibTeX export, references.bib synchronization, citation insertion into Markdown/LaTeX drafts, DOI/PMID/reference organization, attachment paths, indexed full-text retrieval, or explicit BibTeX/RIS import into Zotero. Use for prompts mentioning Zotero, full text, PDF attachments, bibliography, reference library, citation keys, references.bib, local API localhost:23119, pyzotero, or organizing references.
---

# Zotero Reference Manager

## Purpose

Connect Article Machine projects to Zotero without weakening Evidence Lock. Zotero organizes references and can expose local indexed full text or attachments; it does not make paywalled content legally available by itself.

## Mandatory Flow

1. Identify the active project before touching manuscript citations or claim maps.
2. Resolve `plugin:zotero` through `.machine/plugin_bindings.json`. Exactly one
   explicit binding is required; absent or multiple bindings block execution.
   Read `<binding-root>/skills/zotero/SKILL.md`.
3. Check local readiness first:

```powershell
python <binding-root>/skills/zotero/scripts/zotero.py status --json
```

4. If `local_api_enabled_pref` is true but `api_running` is false, start the
   installed desktop app and retry status:

```powershell
Start-Process -FilePath "C:\Program Files\Zotero\zotero.exe"
Start-Sleep -Seconds 25
python <binding-root>/skills/zotero/scripts/zotero.py status --json
```

5. For Article Machine projects, write or sync outputs to:
   - `sources/zotero/` for search, inventory, export, and full-text manifests;
   - `drafts/references.bib` for manuscript bibliography;
   - `evidence/claim_map.jsonl` only after citation-source-claim support is verified.
6. Use Zotero item keys and BibTeX keys correctly. They are not the same identifier.
7. Retrieve full text only when requested, and prefer indexed text or local attachment paths. Do not bulk-download or stage copyrighted PDFs.
8. Confirm before writing into Zotero with BibTeX/RIS import unless the user explicitly asked to add/import records.

## Commands

```powershell
python <binding-root>/skills/zotero/scripts/zotero.py inventory
python <binding-root>/skills/zotero/scripts/zotero.py search "query" --json
python <binding-root>/skills/zotero/scripts/zotero.py export-bibtex --out drafts\references.bib
python <binding-root>/skills/zotero/scripts/zotero.py fulltext ITEMKEY --out sources\zotero\fulltext\ITEMKEY.txt
```

## Integration Rules

- Pair with `citation-management`, `paper-lookup`, `crossref-unpaywall-resolver`, and `opencitations-citation-audit` when metadata or citation integrity is uncertain.
- Pair with `evidence-lock-hardener` before manuscript readiness.
- If Zotero local API is disabled, report the exact blocker; do not manually edit profiles unless the Zotero plugin helper says to.
- The desktop executable path is machine-local configuration; do not assume it
  is on `PATH` or hard-code it in a portable skill.
- If using Web API instead of local Desktop, use `pyzotero` and require `ZOTERO_API_KEY`, `ZOTERO_LIBRARY_ID`, and `ZOTERO_LIBRARY_TYPE`.

## Reference

Read `references/zotero-article-machine-bridge.md` before project-level sync or full-text work.
