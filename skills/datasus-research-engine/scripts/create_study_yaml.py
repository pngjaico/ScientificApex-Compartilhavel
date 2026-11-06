#!/usr/bin/env python
"""Create a conservative DATASUS study YAML from a topic string.

This helper intentionally marks all codes as pending validation. It uses only
the Python standard library so it can run before project dependencies exist.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from unicodedata import combining, normalize


TOPIC_CATALOG = [
    {
        "needles": ("hernia inguinal", "hérnia inguinal"),
        "study_slug": "hernia_inguinal",
        "title_term": "hernia inguinal",
        "icd10": [("K40", "Inguinal hernia")],
        "dataset": ("SIH", "RD"),
    },
    {
        "needles": ("apendicite", "appendicitis"),
        "study_slug": "apendicite",
        "title_term": "apendicite",
        "icd10": [("K35", "Acute appendicitis"), ("K36", "Other appendicitis"), ("K37", "Unspecified appendicitis")],
        "dataset": ("SIH", "RD"),
    },
    {
        "needles": ("cancer colorretal", "câncer colorretal", "neoplasia colorretal", "colorectal cancer"),
        "study_slug": "cancer_colorretal",
        "title_term": "cancer colorretal",
        "icd10": [("C18", "Colon cancer"), ("C19", "Rectosigmoid junction cancer"), ("C20", "Rectal cancer"), ("C21", "Anal canal cancer")],
        "dataset": ("SIH", "RD"),
    },
    {
        "needles": ("obstrucao intestinal", "obstrução intestinal", "intestinal obstruction"),
        "study_slug": "obstrucao_intestinal",
        "title_term": "obstrucao intestinal",
        "icd10": [("K56", "Paralytic ileus and intestinal obstruction without hernia")],
        "dataset": ("SIH", "RD"),
    },
    {
        "needles": ("doenca diverticular", "doença diverticular", "diverticular disease"),
        "study_slug": "doenca_diverticular",
        "title_term": "doenca diverticular",
        "icd10": [("K57", "Diverticular disease of intestine")],
        "dataset": ("SIH", "RD"),
    },
]


def ascii_fold(value: str) -> str:
    return "".join(ch for ch in normalize("NFKD", value).lower() if not combining(ch))


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", ascii_fold(value)).strip("_") or "datasus_study"


def infer_years(topic: str, default_start: int, default_end: int) -> tuple[int, int]:
    years = [int(match) for match in re.findall(r"\b(20\d{2}|19\d{2})\b", topic)]
    if len(years) >= 2:
        return min(years), max(years)
    if len(years) == 1:
        return years[0], years[0]
    return default_start, default_end


def infer_topic(topic: str) -> dict:
    folded = ascii_fold(topic)
    for item in TOPIC_CATALOG:
        if any(ascii_fold(needle) in folded for needle in item["needles"]):
            return item
    return {
        "study_slug": slugify(topic)[:60],
        "title_term": topic.strip() or "DATASUS topic",
        "icd10": [],
        "dataset": ("SIH", "RD"),
    }


def yaml_list(values: list[str], indent: int = 4) -> str:
    pad = " " * indent
    if not values:
        return " []"
    return "\n" + "\n".join(f"{pad}- {value}" for value in values)


def build_yaml(topic: str, start_year: int, end_year: int, states: str, months: str) -> str:
    inferred = infer_topic(topic)
    dataset_name, dataset_group = inferred["dataset"]
    period_start, period_end = infer_years(topic, start_year, end_year)
    state_slug = "brazil" if states.lower() == "all" else slugify(states)
    study_id = f"{inferred['study_slug']}_{state_slug}_{period_start}_{period_end}"
    icd_codes = [code for code, _label in inferred["icd10"]]

    validation_lines = []
    for code, label in inferred["icd10"]:
        validation_lines.extend(
            [
                f"    - code: {code}",
                f'      label: "{label}"',
                "      status: suggested_pending_validation",
            ]
        )
    if not validation_lines:
        validation_lines = ["    []"]

    return f"""study_id: {study_id}
title: "DATASUS study: {inferred['title_term']}, {period_start}-{period_end}"
research_question: "What was the epidemiologic profile of {inferred['title_term']} in SUS administrative data from {period_start} to {period_end}?"
datasets:
  - name: {dataset_name}
    group: {dataset_group}
period:
  start_year: {period_start}
  end_year: {period_end}
  months: {months}
geography:
  country: Brazil
  states: {states}
filters:
  diagnosis:
    primary_icd10_prefixes:{yaml_list(icd_codes, 6)}
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
    - admissions_by_race_color
    - admissions_by_region
    - annual_trend
methodology:
  design: "Ecological time-series study using public administrative health data"
  data_source_description: "DATASUS {dataset_name}/{dataset_group}"
  statistical_plan: [descriptive_statistics, annual_trend_analysis, stratified_analysis]
quality_flags:
  requires_code_validation: true
  ecological_bias_warning: true
  administrative_data_limitation: true
code_validation:
  icd10:
{chr(10).join(validation_lines)}
  sigtap: []
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a conservative DATASUS study YAML.")
    parser.add_argument("topic", help="Natural-language topic, e.g. 'hernia inguinal no Brasil de 2018 a 2025'.")
    parser.add_argument("--start-year", type=int, default=2018)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--states", default="all")
    parser.add_argument("--months", default="all")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    content = build_yaml(args.topic, args.start_year, args.end_year, args.states, args.months)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
