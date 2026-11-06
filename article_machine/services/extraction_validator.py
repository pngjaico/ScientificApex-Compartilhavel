"""Mathematical & Epidemiological Extraction Validator for Systematic Reviews, NMA, and Diagnostic Studies.

Prevents denominator mismatches (events > total), SD vs SE confusion, unvalidated median/IQR pooling,
disconnected Network Meta-Analysis (NMA) treatment graphs, and 2x2 diagnostic table arithmetic errors.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


def load_extraction_records(path: Path) -> list[dict[str, Any]]:
    """Load extraction records from JSON, JSONL, or CSV."""
    file_path = Path(path).resolve()
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [dict(item) for item in payload]
        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            return [dict(item) for item in payload["records"]]
        raise ValueError("JSON extraction file must contain a list of records or a 'records' list.")
    if suffix == ".jsonl":
        return [json.loads(line) for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle, delimiter=delimiter)]
    raise ValueError(f"Unsupported extraction file format: {suffix}")


def _to_float(val: Any) -> float | None:
    if val is None or val == "" or isinstance(val, bool):
        return None
    try:
        result = float(val)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _to_int(val: Any) -> int | None:
    fval = _to_float(val)
    if fval is None:
        return None
    if int(fval) != fval:
        return None
    return int(fval)


def validate_extraction_records(
    records: list[dict[str, Any]],
    *,
    mode: str = "pairwise",
) -> dict[str, Any]:
    """Validate extracted study rows for mathematical, denominator, and network integrity.

    Modes:
    - 'pairwise': Standard binary/continuous meta-analysis checks.
    - 'nma': Pairwise checks + multi-arm count, treatment label hygiene, and graph connectivity.
    - 'diagnostic': 2x2 contingency table checks (TP, FP, FN, TN, N, sensitivity, specificity).
    """
    issues: list[str] = []
    warnings: list[str] = []
    normalized_mode = mode.strip().lower()

    if normalized_mode not in {"pairwise", "nma", "diagnostic"}:
        return {
            "contract": "ExtractionValidationReportV1",
            "status": "blocked",
            "mode": normalized_mode,
            "record_count": len(records),
            "issues": ["Unknown extraction validation mode."],
            "warnings": [],
            "gate_eligible": False,
        }

    if not records:
        return {
            "contract": "ExtractionValidationReportV1",
            "status": "blocked",
            "mode": normalized_mode,
            "record_count": 0,
            "issues": ["Extraction table is empty."],
            "warnings": [],
        }

    study_arms: dict[str, list[str]] = defaultdict(list)
    raw_treatments: set[str] = set()

    for idx, row in enumerate(records, start=1):
        if not isinstance(row, dict) or not row:
            issues.append(f"Row {idx}: a nonempty structured extraction record is required.")
            continue
        study_id = str(row.get("study_id") or row.get("study") or f"row_{idx}").strip()
        label = f"Row {idx} ({study_id})"
        count_fields = {
            "events",
            "total",
            "n",
            "events_intervention",
            "n_intervention",
            "events_control",
            "n_control",
            "e_i",
            "n_i",
            "e_c",
            "n_c",
            "tp",
            "fp",
            "fn",
            "tn",
        }
        numeric_fields = count_fields | {
            "mean",
            "mean_intervention",
            "mean_control",
            "mean_i",
            "mean_c",
            "sd",
            "sd_intervention",
            "sd_control",
            "sd_i",
            "sd_c",
            "sensitivity",
            "specificity",
            "subgroup_n_sum",
        }
        for key in numeric_fields & row.keys():
            value = _to_int(row[key]) if key in count_fields else _to_float(row[key])
            if value is None:
                issues.append(f"{label}: present field '{key}' must be a finite valid numeric value.")
            elif key in count_fields and value < (
                1 if key in {"total", "n", "n_i", "n_c", "n_intervention", "n_control"} else 0
            ):
                issues.append(f"{label}: count/denominator '{key}' is outside its valid range.")
            elif key in {"sensitivity", "specificity"} and not 0 <= value <= 1:
                issues.append(f"{label}: '{key}' must be a proportion between 0 and 1.")
        for event, denominators in [
            ("events", {"total", "n"}),
            ("events_intervention", {"n_intervention"}),
            ("events_control", {"n_control"}),
            ("e_i", {"n_i"}),
            ("e_c", {"n_c"}),
        ]:
            if event in row and not denominators.intersection(row):
                issues.append(f"{label}: '{event}' requires its denominator.")
        if not (
            set(row)
            & (
                count_fields
                | {"mean", "mean_intervention", "mean_control", "mean_i", "mean_c", "treatment", "arm", "treat1"}
            )
        ):
            issues.append(f"{label}: no supported outcome/count or network arm schema was identified.")

        # 1. Binary denominator & event checks
        for ev_key, n_key in [
            ("events", "total"),
            ("events", "n"),
            ("events_intervention", "n_intervention"),
            ("events_control", "n_control"),
            ("e_i", "n_i"),
            ("e_c", "n_c"),
        ]:
            if ev_key in row and n_key in row:
                ev = _to_int(row.get(ev_key))
                tot = _to_int(row.get(n_key))
                if ev is None or tot is None:
                    issues.append(f"{label}: '{ev_key}' and '{n_key}' must be valid integers.")
                else:
                    if tot <= 0:
                        issues.append(f"{label}: denominator '{n_key}' must be > 0 (got {tot}).")
                    if ev < 0:
                        issues.append(f"{label}: event count '{ev_key}' cannot be negative (got {ev}).")
                    if tot > 0 and ev > tot:
                        issues.append(f"{label}: impossible denominator mismatch: {ev_key}={ev} exceeds {n_key}={tot}.")

        # 2. Subgroup sum reconciliation if subgroup_counts and total are both present
        if "subgroup_n_sum" in row and ("total" in row or "n" in row):
            sub_sum = _to_int(row.get("subgroup_n_sum"))
            tot = _to_int(row.get("total") if "total" in row else row.get("n"))
            if sub_sum is not None and tot is not None and sub_sum != tot:
                issues.append(f"{label}: subgroup denominator sum ({sub_sum}) does not equal study total ({tot}).")

        # 3. Continuous outcome checks (SD > 0, SE vs SD confusion, Median/IQR mixing)
        for sd_key in ("sd", "sd_intervention", "sd_control", "sd_i", "sd_c"):
            if sd_key in row and row.get(sd_key) not in (None, ""):
                sd_val = _to_float(row.get(sd_key))
                if sd_val is None or sd_val <= 0:
                    issues.append(f"{label}: standard deviation '{sd_key}' must be > 0 (got {row.get(sd_key)}).")

        dispersion_type = str(row.get("dispersion_type") or "SD").strip().upper()
        if dispersion_type == "SE" and not row.get("converted_se_to_sd"):
            issues.append(
                f"{label}: dispersion is marked as Standard Error (SE) without explicit SE->SD "
                "conversion (SD = SE * sqrt(n))."
            )

        summary_type = str(row.get("summary_type") or "MEAN").strip().upper()
        if summary_type in {"MEDIAN", "MEDIANA", "IQR"} and not row.get("conversion_method"):
            issues.append(
                f"{label}: median/IQR reported without validated conversion method (e.g., Wan/Luo) "
                "or separate synthesis."
            )

        # 4. Diagnostic 2x2 checks
        if normalized_mode == "diagnostic" or all(k in row for k in ("tp", "fp", "fn", "tn")):
            tp = _to_int(row.get("tp"))
            fp = _to_int(row.get("fp"))
            fn = _to_int(row.get("fn"))
            tn = _to_int(row.get("tn"))
            if None in (tp, fp, fn, tn):
                issues.append(f"{label}: diagnostic mode requires integer tp, fp, fn, and tn.")
            else:
                assert tp is not None and fp is not None and fn is not None and tn is not None
                if any(v < 0 for v in (tp, fp, fn, tn)):
                    issues.append(f"{label}: 2x2 cell counts (tp, fp, fn, tn) cannot be negative.")
                if (tp + fn) <= 0 or (tn + fp) <= 0:
                    issues.append(f"{label}: diseased (tp+fn) and non-diseased (tn+fp) totals must both be > 0.")
                tot_n = _to_int(row.get("total") if "total" in row else row.get("n"))
                if tot_n is not None and (tp + fp + fn + tn) != tot_n:
                    issues.append(f"{label}: 2x2 sum ({tp + fp + fn + tn}) does not match declared total N ({tot_n}).")
                rep_sens = _to_float(row.get("sensitivity"))
                if rep_sens is not None and (tp + fn) > 0:
                    calc_sens = tp / (tp + fn)
                    if abs(calc_sens - rep_sens) > 0.02:
                        issues.append(
                            f"{label}: reported sensitivity ({rep_sens:.3f}) disagrees with TP/(TP+FN) "
                            f"({calc_sens:.3f})."
                        )
                rep_spec = _to_float(row.get("specificity"))
                if rep_spec is not None and (tn + fp) > 0:
                    calc_spec = tn / (tn + fp)
                    if abs(calc_spec - rep_spec) > 0.02:
                        issues.append(
                            f"{label}: reported specificity ({rep_spec:.3f}) disagrees with TN/(TN+FP) "
                            f"({calc_spec:.3f})."
                        )

        # 5. Collect NMA arm/treatment topology
        if "treatment" in row or "arm" in row:
            raw_t = str(row.get("treatment") or row.get("arm") or "")
            raw_treatments.add(raw_t)
            study_arms[study_id].append(raw_t.strip())
        elif "treat1" in row and "treat2" in row:
            t1 = str(row.get("treat1") or "")
            t2 = str(row.get("treat2") or "")
            raw_treatments.update([t1, t2])
            study_arms[study_id].extend([t1.strip(), t2.strip()])

    # 6. NMA Network Geometry & Connectivity Validation
    network_summary: dict[str, Any] = {}
    if normalized_mode == "nma":
        # Check whitespace/case drift in treatment names
        lower_map: dict[str, set[str]] = defaultdict(set)
        for rt in raw_treatments:
            if rt != rt.strip():
                issues.append(f"NMA treatment label '{rt}' has leading or trailing whitespace.")
            lower_map[rt.strip().lower()].add(rt.strip())
        for _, variants in lower_map.items():
            if len(variants) > 1:
                issues.append(f"NMA treatment label case inconsistency detected: {sorted(variants)}.")

        adjacency: dict[str, set[str]] = defaultdict(set)
        all_nodes: set[str] = set()
        for study_id, arms in study_arms.items():
            unique_arms = sorted(set(a for a in arms if a))
            if len(unique_arms) < 2:
                issues.append(
                    f"Study '{study_id}' has fewer than 2 distinct treatment arms ({unique_arms}); "
                    "orphan single-arm studies break contrast NMA."
                )
            for a in unique_arms:
                all_nodes.add(a)
                for b in unique_arms:
                    if a != b:
                        adjacency[a].add(b)

        if not all_nodes:
            issues.append(
                "NMA mode requires 'treatment'/'arm' (long format) or 'treat1'/'treat2' (contrast format) columns."
            )
        else:
            start_node = sorted(all_nodes)[0]
            visited: set[str] = {start_node}
            queue: deque[str] = deque([start_node])
            while queue:
                curr = queue.popleft()
                for neighbor in adjacency[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            disconnected = sorted(all_nodes - visited)
            if disconnected:
                issues.append(
                    f"NMA treatment network is disconnected! Isolated/disconnected treatments: {disconnected}."
                )
            network_summary = {
                "treatment_count": len(all_nodes),
                "treatments": sorted(all_nodes),
                "study_count": len(study_arms),
                "connected": len(disconnected) == 0,
                "disconnected_treatments": disconnected,
            }

    return {
        "contract": "ExtractionValidationReportV1",
        "status": "pass" if not issues else "blocked",
        "mode": normalized_mode,
        "record_count": len(records),
        "network_summary": network_summary,
        "issues": issues,
        "warnings": warnings,
        "gate_eligible": False,
        "scope": "Arithmetic and topology checks only; source verification and methodological review remain required.",
    }
