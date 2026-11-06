---
name: alphafold-pdb-structure-router
description: Use when protein structure, AlphaFold DB, RCSB PDB, UniProt, domains, binding pockets, variants, complexes, docking preparation, pLDDT confidence, or structure-based mechanism evidence is needed.
---

# AlphaFold PDB Structure Router

Use this skill to choose the right structure source and prepare structure evidence responsibly.

## Workflow
1. Resolve the protein to UniProt accession, isoform, species, and sequence region.
2. Prefer experimental PDB structures for binding-site or ligand questions when quality is adequate.
3. Use AlphaFold DB for coverage, domain context, or missing experimental structures.
4. Record confidence: method, resolution for PDB, pLDDT/PAE for AlphaFold, chain/ligand/biological assembly.
5. Flag low-confidence regions before docking, variant interpretation, or mechanistic claims.
6. Save structure metadata and selected files under `analysis/structures/`.

## Gates
- Do not dock into low-confidence AlphaFold regions without explicit caveat.
- Do not treat monomeric predictions as validated complexes.
- Keep structure source, accession, and retrieval date.
