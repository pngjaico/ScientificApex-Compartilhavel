# Study YAML Contract

Generate a YAML before downloading data. Treat it as the protocol for extraction and analysis.

## Required Fields

- `study_id`
- `title`
- `research_question`
- `datasets`
- `period`
- `geography`
- `filters`
- `variables`
- `outcomes`
- `methodology`
- `quality_flags`
- `code_validation`

## Code Validation States

- `suggested_pending_validation`: produced by catalog or LLM; not acceptable for final analysis.
- `user_confirmed`: explicitly confirmed by the user or domain reviewer.
- `analysis_used`: exact codes applied in the final cohort.
- `rejected`: considered and excluded, with reason.

## Minimal Example

```yaml
study_id: hernia_inguinal_brazil_2018_2025
title: "Hospitalizations for inguinal hernia in Brazil, 2018-2025"
research_question: "What was the trend in SUS-financed hospitalizations for inguinal hernia from 2018 to 2025?"
datasets:
  - name: SIH
    group: RD
period:
  start_year: 2018
  end_year: 2025
  months: all
geography:
  country: Brazil
  states: all
filters:
  diagnosis:
    primary_icd10_prefixes: ["K40"]
    secondary_icd10_prefixes: []
  procedures:
    sigtap_codes: []
variables:
  time: [ANO_CMPT, MES_CMPT]
  demographics: [SEXO, IDADE, RACA_COR]
  geography: [UF_ZI, MUNIC_RES]
  hospitalization: [CAR_INT, DIAS_PERM, MORTE, VAL_TOT]
outcomes:
  primary: [admissions]
  secondary:
    - deaths
    - in_hospital_mortality_rate
    - total_cost
    - mean_length_of_stay
    - admissions_by_sex
    - admissions_by_age_group
    - admissions_by_region
    - annual_trend
methodology:
  design: "Ecological time-series study using public administrative health data"
  data_source_description: "SIH/SUS - Hospital Information System of the Brazilian Unified Health System"
  statistical_plan: [descriptive_statistics, annual_trend_analysis, stratified_analysis]
quality_flags:
  requires_code_validation: true
  ecological_bias_warning: true
  administrative_data_limitation: true
code_validation:
  icd10:
    - code: K40
      label: "Inguinal hernia"
      status: suggested_pending_validation
  sigtap: []
```
