---
name: scopus-search
description: High-performance academic search using the Elsevier Scopus API. Search by keywords, DOIs, authors, and affiliations with precise metadata extraction and citation tracking.
allowed-tools: Read Write Edit Bash
license: MIT License
metadata:
    skill-author: Antigravity / K-Dense Custom
---

# Scopus Search Skill

## Overview
This skill provides programmatic access to the **Elsevier Scopus API**, the world's largest abstract and citation database. It allows for deep literature mining, citation analysis, and systematic review support.

## When to Use This Skill
- Systematic literature reviews requiring Scopus coverage.
- Tracking citation counts for specific papers.
- Finding all publications by a specific author or affiliation.
- Large-scale metadata extraction for bibliometric analysis.

## Usage
### Basic Keyword Search
```bash
python scripts/search_scopus.py "TITLE-ABS-KEY(machine learning AND protein folding)" --limit 50 -o sources/scopus_results.md
```

### Search by DOI
```bash
python scripts/search_scopus.py "DOI(10.1016/j.cell.2023.01.001)" -o sources/paper_info.md
```

### Search by Author
```bash
python scripts/search_scopus.py "AUTHOR-NAME(Church, G)" --limit 100 -o sources/church_publications.md
```

## Quota Saver Protocol
Every call to `search_scopus.py` **MUST** include the `-o` flag pointing to the `sources/` directory. This ensures that expensive API results are cached locally and can be re-read by the [CONTEXT MANAGER] layer without making new requests.

---
> **Tip:** Scopus uses specialized field codes (e.g., `AFFIL(Harvard)`, `PUBYEAR > 2020`). Combine these for highly targeted searches.
