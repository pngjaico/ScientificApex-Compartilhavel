#!/usr/bin/env python
"""Lightweight DATASUS study YAML validator.

This is not a full YAML parser. It catches missing required sections and unsafe
validation states before a study is run.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_KEYS = [
    "study_id:",
    "title:",
    "research_question:",
    "datasets:",
    "period:",
    "geography:",
    "filters:",
    "variables:",
    "outcomes:",
    "methodology:",
    "quality_flags:",
    "code_validation:",
]


def validate_text(text: str) -> dict:
    issues: list[str] = []
    for key in REQUIRED_KEYS:
        if key not in text:
            issues.append(f"Missing required key: {key.rstrip(':')}")

    if "requires_code_validation: true" not in text:
        issues.append("quality_flags.requires_code_validation should remain true until human validation is documented.")

    has_icd = bool(re.search(r"primary_icd10_prefixes:\s*(\n\s*-\s*\w+|\[[^\]]+\])", text))
    has_sigtap = bool(re.search(r"sigtap_codes:\s*(\n\s*-\s*\w+|\[[^\]]+\])", text))
    if not has_icd and not has_sigtap:
        issues.append("No ICD-10 prefix or SIGTAP code found; extraction would be too broad.")

    if "analysis_used" in text and "user_confirmed" not in text:
        issues.append("Codes marked analysis_used without a user_confirmed validation record.")

    if "ecological_bias_warning: true" not in text:
        issues.append("Missing ecological_bias_warning: true.")
    if "administrative_data_limitation: true" not in text:
        issues.append("Missing administrative_data_limitation: true.")

    return {
        "status": "pass" if not issues else "needs_human_validation",
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a DATASUS study YAML.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    report = validate_text(args.path.read_text(encoding="utf-8"))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
