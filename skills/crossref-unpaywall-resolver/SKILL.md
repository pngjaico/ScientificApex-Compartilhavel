---
name: crossref-unpaywall-resolver
description: Use when DOI metadata, Crossref member metadata, references, licenses, funders, ORCID/ROR fields, Crossmark updates, or Unpaywall open-access full-text links need verification.
---

# Crossref and Unpaywall Resolver

Use this skill to resolve publication identity and open-access availability before a citation is trusted in Article Machine.

## Gate
- Resolve DOI/title metadata through Crossref before final bibliography insertion when publisher DOI metadata is needed.
- Check Unpaywall for open-access status and legal full-text locations before downloading PDFs.
- Store raw provider responses under `sources/crossref/` and `sources/unpaywall/`.
- Add provider, endpoint, query, DOI/title, retrieved_at, contact route, record_count, and response hash to the retrieval manifest.
- Promote only verified bibliographic data to `drafts/references.bib`.

## Provider Rules
- Crossref requests must identify the tool and contact route with `mailto` or a User-Agent containing contact information.
- Unpaywall requests must include an email parameter.
- Cache DOI lookups; repeated DOI polling is wasteful and can get blocked.
- Treat Crossref metadata as publisher-deposited metadata, not as proof that the scientific claim is true.

## Required Checks
- DOI normalization and duplicate DOI detection.
- License and open-access location before storing full text.
- Crossmark/update/retraction-related signals when available.
- Funder, ORCID, ROR, and reference-list availability for provenance work.

## Red Flags
- Downloading a PDF without checking license/source.
- Building a reference from title search when an explicit DOI lookup is available.
- Treating absence of a Crossref warning as proof of integrity.
