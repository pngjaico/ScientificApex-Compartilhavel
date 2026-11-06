---
name: chembl-bindingdb-miner
description: Use when mining ChEMBL, BindingDB, PubChem, ChEBI, or related chemistry databases for compound activity, ligand-target binding, potency, selectivity, mechanism, assay metadata, SMILES, ADMET, medchem triage, or drug-discovery evidence.
---

# ChEMBL BindingDB Miner

Use this skill to collect small-molecule evidence without losing assay context.

## Workflow
1. Resolve target and molecule identifiers: UniProt, ChEMBL target, compound ID, InChIKey, SMILES.
2. Retrieve activity/binding records with assay type, organism, target confidence, units, relation, value, and source.
3. Normalize potency units and separate biochemical, cellular, phenotypic, and binding assays.
4. Flag ambiguous targets, inactive records, duplicates, salts, mixtures, and assay artifacts.
5. Produce a medchem triage table with potency, selectivity, drug-likeness, liabilities, and provenance.

## Gates
- Do not compare IC50/Ki/EC50 across assay contexts without caveats.
- Do not call a compound selective without counter-target evidence.
- Keep raw query outputs for audit.
