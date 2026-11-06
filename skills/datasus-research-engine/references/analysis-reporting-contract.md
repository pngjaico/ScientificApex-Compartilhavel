# Analysis And Reporting Contract

## Required Indicators

- total admissions
- deaths
- in-hospital mortality rate
- total cost
- mean and median cost per admission
- total length of stay
- mean and median length of stay
- admissions by year and month
- admissions by sex
- admissions by age group
- admissions by race/color
- admissions by region and state
- admissions by admission type
- deaths and mortality rate by year
- cost and length of stay by year

Default age groups: `0-9`, `10-19`, `20-29`, `30-39`, `40-49`, `50-59`, `60-69`, `70-79`, `80+`.

Default regions: Norte, Nordeste, Centro-Oeste, Sudeste, Sul.

## Statistics

- Start with descriptive statistics.
- For temporal trend, report first-to-last percent change and CAGR when appropriate.
- Use Poisson or negative binomial regression only when counts and denominators support it.
- Use logistic regression for in-hospital mortality only when the study explicitly asks and confounding limitations are declared.
- Never write causal conclusions from administrative ecological data.

## Required Figures

- admissions by year
- deaths by year
- in-hospital mortality rate by year
- admissions by region
- admissions by UF
- admissions by sex
- admissions by age group
- admissions by race/color
- elective vs urgent admission type
- total cost by year
- mean length of stay by year
- optional UF x year heatmap

Export PNG and SVG. Use Portuguese labels when report language is Portuguese. Add source footer: `Fonte: DATASUS/SIH-SUS`.

## Required Tables

- Table 1: general hospitalization characteristics.
- Table 2: annual trend of outcomes.
- Table 3: stratification by sex, age, race/color.
- Table 4: stratification by region and UF.
- Table 5: admission type, cost, length of stay, mortality.
- Supplementary table 1: variable dictionary.
- Supplementary table 2: ICD/SIGTAP codes used.
- Supplementary table 3: quality log.

Export CSV, XLSX, and Markdown.

## Scientific Language Gate

Block or replace strong causal wording:

- `provou que` -> `foi observado que`
- `causou` -> `foi associado a`
- `foi responsavel por` -> `pode estar relacionado a`
- `garante` -> `sugere`

Every report must include:

- administrative data limitation
- SUS-financed hospitalization coverage limitation when applicable
- coding error/subnotification risk
- no causal inference
- no laboratory/intraoperative granularity
- dependence on CID/SIGTAP validation
- COVID/post-2020 disruption caveat when period crosses 2020

## Readiness Labels

- `Ready for exploration`
- `Ready for abstract`
- `Ready for manuscript draft`
- `Needs human validation`

Manuscript outputs must be labeled `draft for human review`.
