# Source Notes

Verified on 2026-06-29.

## Official Surfaces

- DATASUS official transfer page exposes file selection by source, modality, file type, year, month, and UF: https://datasus.saude.gov.br/transferencia-de-arquivos/
- PySUS documentation current surface is 2.0+ and documents access to DATASUS datasets including SINAN, SIM, SINASC, SIH, SIA, CIHA, CNES, PNI, and IBGE: https://pysus.readthedocs.io/
- PySUS data-source docs show high-level functions from `pysus.api`: `sinan`, `sinasc`, `sim`, `sih`, `sia`, `pni`, `ibge`, `cnes`, `ciha`.
- PySUS docs also show a lower-level `PySUS` client with catalog query, download, and `read_parquet` modes: `union`, `intersection`, and `strict`.
- PySUS GitHub lists supported data sources as SINAN, SIM, SINASC, SIH, SIA, CIHA, CNES, PNI, and IBGE, and documents `PYSUS_CACHEPATH`.

## Practical Consequences

- Prefer official PySUS APIs when they work; keep a fallback path for direct DATASUS transfer/FTP only when PySUS fails or does not expose a needed file.
- Pin or log PySUS version because the API surface is active and may change.
- Use Parquet as the durable cache layer and DuckDB as the query layer.
- Use `strict` schema reads only for QC; use `union` or `intersection` intentionally and log the choice.

## Citation Boundary

Use these sources to justify extraction mechanics. They do not validate disease-specific CID/SIGTAP choices or scientific conclusions.
