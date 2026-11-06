"""Cross-Artifact Numerical Ledger Auditor and Clinical ML Methodology Evaluator.

1. Audits numerical consistency between canonical analysis outputs (analysis/results_ledger.json)
   and paired PT-BR / English manuscripts (handling decimal point vs comma equivalence).
2. Evaluates TRIPOD+AI / PROBAST+AI clinical prediction requirements:
   - Patient-level partition leakage audit (zero patient overlap between train and test)
   - Discrimination (exact Mann-Whitney AUROC)
   - Calibration (Brier score, calibration-in-the-large, logit calibration slope, calibration error)
   - Decision Curve Analysis (DCA Net Benefit vs Treat-All and Treat-None)
   - Split-conformal evaluation on separate data; assumptions remain explicit
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def _pt_en_numeric_variants(val_str: str) -> set[str]:
    """Return acceptable string representations in PT-BR (comma/dot) and EN (dot)."""
    clean = str(val_str).strip()
    variants = {clean}
    if "." in clean:
        variants.add(clean.replace(".", ","))
    if "," in clean:
        variants.add(clean.replace(",", "."))
    return variants


def audit_numerical_consistency(
    project_dir: Path,
    ledger_rel_path: str = "analysis/results_ledger.json",
    *,
    draft_paths: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Audit explicit {{metric:key}} value bindings, never arbitrary substrings.

    Working manuscripts retain binding markers like claim markers. This checks
    canonical numeric identity, not scientific support or human semantic review.
    """
    import re
    from decimal import Decimal, InvalidOperation

    root = Path(project_dir).resolve()
    issues: list[str] = []
    verified: dict[str, list[str]] = {}
    checked: dict[str, str] = {}

    def confined(relative: str) -> Path:
        p = Path(relative)
        resolved = (root / p).resolve()
        if p.is_absolute() or ".." in p.parts or not resolved.is_relative_to(root):
            raise ValueError("Result ledger and manuscript paths must remain inside the project.")
        return resolved

    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate canonical key: {key}")
            result[key] = value
        return result

    def number(value: Any) -> Decimal:
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise ValueError("Canonical metrics must be finite numeric scalars.")
        try:
            result = Decimal(str(value).strip().replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError("Canonical metrics must be numeric.") from exc
        if not result.is_finite():
            raise ValueError("Canonical metrics must be finite.")
        return result

    try:
        payload = json.loads(confined(ledger_rel_path).read_text(encoding="utf-8-sig"), object_pairs_hook=no_duplicates)
        metrics = payload.get("metrics", payload) if isinstance(payload, dict) else None
        if not isinstance(metrics, dict) or not metrics:
            raise ValueError("A non-empty canonical metrics object is required.")
        canonical = {
            key: number(value["value"] if isinstance(value, dict) else value) for key, value in metrics.items()
        }
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return {
            "contract": "NumericalConsistencyAuditV2",
            "status": "blocked",
            "gate_eligible": False,
            "issues": [str(exc)],
        }
    files = draft_paths or {"portugues": "drafts/portugues/manuscrito.md", "ingles": "drafts/ingles/manuscrito.md"}
    if not all(language in files for language in ("portugues", "ingles")):
        issues.append("Both Portuguese and English manuscript paths are required.")
    pattern = re.compile(
        r"\{\{metric:([^{}]+)\}\}\s*(?:=|:)?\s*"
        r"([-+]?(?:\d+(?:[.,]\d+)?|[.,]\d+)(?:[eE][-+]?\d+)?)(?![\w]|[.,]\d)"
    )
    for language, relative in files.items():
        try:
            file_path = confined(relative)
            text = file_path.read_text(encoding="utf-8-sig")
            checked[language] = relative
        except (OSError, ValueError) as exc:
            issues.append(f"{language}: {exc}")
            continue
        bound: dict[str, list[Decimal]] = {}
        markers = list(re.finditer(r"\{\{metric:([^{}]*)\}\}", text))
        if text.count("{{metric:") != len(markers):
            issues.append(f"{language}: malformed metric marker.")
        for marker in markers:
            if marker[1] not in canonical:
                issues.append(f"{language}: unknown canonical metric {marker[1]}.")
            match = pattern.match(text, marker.start())
            if match is None:
                issues.append(f"{language}: metric {marker[1]} requires a valid finite numeric binding.")
            else:
                bound.setdefault(match[1], []).append(number(match[2]))
        verified[language] = []
        for key, expected in canonical.items():
            values = bound.get(key, [])
            if not values:
                issues.append(f"{language}: missing explicit metric binding for {key}.")
            elif any(value != expected for value in values):
                issues.append(f"{language}: metric {key} differs from its canonical value.")
            else:
                verified[language].append(key)
        for key in set(bound) - set(canonical):
            issues.append(f"{language}: unknown canonical metric {key}.")
    return {
        "contract": "NumericalConsistencyAuditV2",
        "status": "blocked" if issues else "pass",
        "gate_eligible": False,
        "scope": "explicit numeric bindings only; not semantic/scientific approval",
        "ledger_path": ledger_rel_path,
        "checked_drafts": checked,
        "verified_metrics": verified,
        "human_semantic_review_required": True,
        "issues": issues,
    }


def _clip_prob(p: float, eps: float = 1e-6) -> float:
    return max(eps, min(1.0 - eps, float(p)))


def _logit(p: float) -> float:
    cp = _clip_prob(p)
    return math.log(cp / (1.0 - cp))


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _compute_auroc(y_true: list[int], y_prob: list[float]) -> float | None:
    """Mann-Whitney rank AUROC with average ranks for ties; undefined for one class."""
    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos
    if not n_pos or not n_neg:
        return None
    ordered = sorted(zip(y_prob, y_true, strict=True))
    positive_ranks = 0.0
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][0] == ordered[start][0]:
            end += 1
        rank = (start + 1 + end) / 2
        positive_ranks += rank * sum(y for _, y in ordered[start:end])
        start = end
    return (positive_ranks - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def _average_precision(y_true: list[int], y_prob: list[float]) -> float | None:
    positives = sum(y_true)
    if not positives:
        return None
    ordered = sorted(zip(y_prob, y_true, strict=True), reverse=True)
    tp = seen = start = 0
    result = 0.0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][0] == ordered[start][0]:
            end += 1
        gained = sum(y for _, y in ordered[start:end])
        tp += gained
        seen += end - start
        result += (gained / positives) * (tp / seen)
        start = end
    return result


def _calibration_summary(y_true: list[int], y_prob: list[float]) -> dict[str, Any]:
    """Unpenalized logistic fits; singular/separated/nonconverged fits stay undefined."""
    clipped = sum(p in (0.0, 1.0) for p in y_prob)
    result: dict[str, Any] = {
        "calibration_intercept": None,
        "calibration_slope": None,
        "intercept_definition": "calibration-in-the-large, slope fixed to 1",
        "slope_definition": "joint logistic intercept and slope on logit(probability)",
        "intercept_status": "not-estimable",
        "slope_status": "not-estimable",
        "boundary_probabilities_clipped": clipped,
        "clip_epsilon": 1e-6,
    }
    if len(set(y_true)) < 2:
        result["reason"] = "Only one outcome class; no invented ideal calibration."
        return result
    x = [_logit(p) for p in y_prob]
    lo, hi = -100.0, 100.0
    for _ in range(120):
        mid = (lo + hi) / 2
        score = sum(y - _sigmoid(mid + xx) for y, xx in zip(y_true, x, strict=True))
        if score > 0:
            lo = mid
        else:
            hi = mid
    result.update(calibration_intercept=(lo + hi) / 2, intercept_status="estimated")
    if max(x) - min(x) < 1e-12:
        result["reason"] = "Constant predictions; calibration slope is not identifiable."
        return result
    pos = [xx for xx, y in zip(x, y_true, strict=True) if y == 1]
    neg = [xx for xx, y in zip(x, y_true, strict=True) if y == 0]
    if min(pos) >= max(neg) or max(pos) <= min(neg):
        result["reason"] = "Complete or quasi separation; finite slope MLE is not established."
        return result

    def likelihood(a: float, b: float) -> float:
        total = 0.0
        for yy, xx in zip(y_true, x, strict=True):
            z = a + b * xx
            total += yy * z - (max(z, 0) + math.log1p(math.exp(-abs(z))))
        return total

    a, b = _logit(sum(y_true) / len(y_true)), 0.0
    for _ in range(100):
        fitted = [_sigmoid(a + b * xx) for xx in x]
        w = [p * (1 - p) for p in fitted]
        g0 = sum(y - p for y, p in zip(y_true, fitted, strict=True))
        g1 = sum((y - p) * xx for y, p, xx in zip(y_true, fitted, x, strict=True))
        h00 = sum(w)
        h01 = sum(ww * xx for ww, xx in zip(w, x, strict=True))
        h11 = sum(ww * xx * xx for ww, xx in zip(w, x, strict=True))
        det = h00 * h11 - h01 * h01
        if det <= 1e-14 or not math.isfinite(det):
            break
        da, db = (h11 * g0 - h01 * g1) / det, (-h01 * g0 + h00 * g1) / det
        scale, previous = 1.0, likelihood(a, b)
        while scale > 1e-8 and likelihood(a + scale * da, b + scale * db) < previous - 1e-12:
            scale /= 2
        if scale <= 1e-8:
            break
        a, b = a + scale * da, b + scale * db
        if max(abs(scale * da), abs(scale * db)) < 1e-8:
            result.update(calibration_slope=b, joint_intercept=a, slope_status="estimated")
            return result
    result["reason"] = "Logistic calibration did not establish a converged finite MLE."
    return result


def _fit_logistic_calibration(y_true: list[int], y_prob: list[float]) -> tuple[float | None, float | None]:
    result = _calibration_summary(y_true, y_prob)
    return result["calibration_intercept"], result["calibration_slope"]


def _binary_input_issues(y_true: list[int], y_prob: list[float], label: str) -> list[str]:
    from numbers import Real

    issues = []
    if len(y_true) != len(y_prob) or not y_true:
        return [f"{label}: outcomes/probabilities must be non-empty and aligned."]
    if any(not isinstance(y, Real) or not math.isfinite(y) or y not in (0, 1) for y in y_true):
        issues.append(f"{label}: outcomes must be finite binary values.")
    if any(isinstance(p, bool) or not isinstance(p, Real) or not math.isfinite(p) or not 0 <= p <= 1 for p in y_prob):
        issues.append(f"{label}: probabilities must be finite numeric values in [0, 1].")
    return issues


def evaluate_clinical_prediction_metrics(
    y_true: list[int],
    y_prob: list[float],
    *,
    patient_ids_train: list[str] | None = None,
    patient_ids_test: list[str] | None = None,
    thresholds: list[float] | None = None,
    conformal_alpha: float = 0.10,
    calibration_y_true: list[int] | None = None,
    calibration_y_prob: list[float] | None = None,
    patient_ids_calibration: list[str] | None = None,
    bootstrap_repeats: int = 0,
    random_seed: int = 20261102,
) -> dict[str, Any]:
    """Patient-level binary prediction metrics, not certification of clinical validity.

    Conformal evaluation requires disjoint train/conformalization/test patient IDs.
    Missing IDs leave leakage unassessed. Finite-sample claims additionally depend
    on exchangeability, which cannot be established from predictions/IDs alone.
    """
    from numbers import Real

    issues = _binary_input_issues(y_true, y_prob, "test")
    if not isinstance(conformal_alpha, Real) or not math.isfinite(conformal_alpha) or not 0 < conformal_alpha < 1:
        issues.append("conformal_alpha must lie strictly between 0 and 1.")
    if (
        isinstance(bootstrap_repeats, bool)
        or not isinstance(bootstrap_repeats, int)
        or not 0 <= bootstrap_repeats <= 10000
        or bootstrap_repeats == 1
    ):
        issues.append("bootstrap_repeats must be an integer between 0 and 10000.")
    if not isinstance(random_seed, int) or isinstance(random_seed, bool):
        issues.append("random_seed must be an integer.")
    eval_thresholds = thresholds if thresholds is not None else [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
    if any(not isinstance(t, Real) or not math.isfinite(t) or not 0 < t < 1 for t in eval_thresholds):
        issues.append("Every decision threshold must be finite and strictly between 0 and 1.")
    partitions = {"train": patient_ids_train, "test": patient_ids_test, "calibration": patient_ids_calibration}
    sets = {}
    for name, ids in partitions.items():
        if ids is not None:
            if not ids or any(not isinstance(value, str) or not value.strip() for value in ids):
                issues.append(f"{name}: patient identifiers must be non-empty strings.")
                continue
            sets[name] = set(ids)
            if name != "train" and len(sets[name]) != len(ids):
                issues.append(f"{name}: repeated patients require an explicitly clustered/longitudinal analysis.")
    if patient_ids_test is not None and len(patient_ids_test) != len(y_true):
        issues.append("Test patient IDs must align with the evaluated predictions.")
    overlap = sum(
        len(sets[a] & sets[b])
        for a, b in [("train", "test"), ("train", "calibration"), ("test", "calibration")]
        if a in sets and b in sets
    )
    if overlap:
        issues.append(f"CRITICAL PATIENT LEAKAGE: overlapping patient partitions ({overlap} overlaps).")
    requested_conformal = (
        calibration_y_true is not None or calibration_y_prob is not None or patient_ids_calibration is not None
    )
    if requested_conformal:
        if calibration_y_true is None or calibration_y_prob is None:
            issues.append("Conformal evaluation requires both calibration outcomes and probabilities.")
        else:
            issues.extend(_binary_input_issues(calibration_y_true, calibration_y_prob, "calibration"))
            if patient_ids_calibration is not None and len(patient_ids_calibration) != len(calibration_y_true):
                issues.append("Calibration patient IDs must align with calibration predictions.")
        if not all(partitions[name] for name in ("train", "test", "calibration")):
            issues.append("Conformal evaluation requires identified, separate train/calibration/test partitions.")
    partition_verified = bool(patient_ids_train and patient_ids_test) and not overlap
    if bootstrap_repeats and not partition_verified:
        issues.append("Patient-level bootstrap requires identified, disjoint train/test partitions.")
    if issues:
        return {
            "contract": "ClinicalPredictionEvaluationV2",
            "status": "blocked",
            "gate_eligible": False,
            "issues": issues,
            "patient_overlap_count": overlap,
        }
    yy, pp = list(map(int, y_true)), list(map(float, y_prob))
    n, events = len(yy), sum(yy)
    prevalence = events / n
    calibration = _calibration_summary(yy, pp)
    calibration["brier_score"] = sum((p - y) ** 2 for y, p in zip(yy, pp, strict=True)) / n
    bins: list[list[tuple[float, int]]] = [[] for _ in range(5)]
    for p, y in zip(pp, yy, strict=True):
        bins[min(4, int(p * 5))].append((p, y))
    ece = sum(
        len(chunk) / n * abs(sum(p for p, _ in chunk) / len(chunk) - sum(y for _, y in chunk) / len(chunk))
        for chunk in bins
        if chunk
    )
    calibration.update(
        ece=ece,
        ece_bin_count=sum(bool(chunk) for chunk in bins),
        ece_definition="five fixed-width probability bins; ties stay together; descriptive only",
    )
    curve = []
    better_thresholds = []
    for threshold in eval_thresholds:
        tp = sum(y == 1 and p >= threshold for y, p in zip(yy, pp, strict=True))
        fp = sum(y == 0 and p >= threshold for y, p in zip(yy, pp, strict=True))
        odds = threshold / (1 - threshold)
        nb, nb_all = tp / n - fp / n * odds, prevalence - (1 - prevalence) * odds
        if nb > max(0.0, nb_all):
            better_thresholds.append(threshold)
        curve.append(
            {
                "threshold": threshold,
                "net_benefit_model": nb,
                "net_benefit_treat_all": nb_all,
                "net_benefit_treat_none": 0.0,
                "outperforms_default_strategies": nb > max(0.0, nb_all),
            }
        )
    conformal: dict[str, Any] = {
        "status": "not-assessed",
        "reason": "Separate conformalization data were not supplied.",
    }
    if requested_conformal:
        assert calibration_y_true is not None and calibration_y_prob is not None
        cy, cp = list(map(int, calibration_y_true)), list(map(float, calibration_y_prob))
        scores = sorted(1 - (p if y == 1 else 1 - p) for y, p in zip(cy, cp, strict=True))
        rank = math.ceil((len(scores) + 1) * (1 - conformal_alpha))
        infinite = rank > len(scores)
        q_hat = math.inf if infinite else scores[rank - 1]
        prediction_sets = [[label for label in (0, 1) if (p if label == 0 else 1 - p) <= q_hat] for p in pp]
        conformal = {
            "status": "computed-on-independent-partition",
            "alpha": conformal_alpha,
            "target_coverage": 1 - conformal_alpha,
            "calibration_n": len(scores),
            "test_n": n,
            "quantile_threshold": None if infinite else q_hat,
            "threshold_is_infinite": infinite,
            "empirical_coverage": sum(y in s for y, s in zip(yy, prediction_sets, strict=True)) / n,
            "ambiguous_set_fraction": sum(len(s) > 1 for s in prediction_sets) / n,
            "prediction_sets": prediction_sets,
            "exchangeability_verified": False,
            "scope": "marginal split-conformal evaluation; no subgroup/shift or clinical guarantee",
        }
    intervals: dict[str, Any] = {"status": "not-assessed", "reason": "Bootstrap was not requested."}
    if bootstrap_repeats:
        import random

        rng = random.Random(random_seed)
        auc_values, brier_values = [], []
        for _ in range(bootstrap_repeats):
            idx = [rng.randrange(n) for _ in range(n)]
            by, bp = [yy[i] for i in idx], [pp[i] for i in idx]
            auc = _compute_auroc(by, bp)
            if auc is not None:
                auc_values.append(auc)
            brier_values.append(sum((p - y) ** 2 for y, p in zip(by, bp, strict=True)) / n)

        def percentile(values: list[float], q: float) -> float | None:
            if len(values) < 2:
                return None
            values = sorted(values)
            index = (len(values) - 1) * q
            low, high = math.floor(index), math.ceil(index)
            return values[low] + (values[high] - values[low]) * (index - low)

        intervals = {
            "status": "computed",
            "method": "patient percentile bootstrap; linear quantile interpolation",
            "level": 0.95,
            "repeats": bootstrap_repeats,
            "seed": random_seed,
            "auroc_valid_repeats": len(auc_values),
            "auroc": [percentile(auc_values, 0.025), percentile(auc_values, 0.975)],
            "brier": [percentile(brier_values, 0.025), percentile(brier_values, 0.975)],
        }
    warnings = []
    if not partition_verified:
        warnings.append("Patient partition leakage was NOT assessed; absent IDs are not evidence of independence.")
    if calibration["slope_status"] != "estimated":
        warnings.append(calibration.get("reason", "Calibration slope not estimable."))
    if _compute_auroc(yy, pp) is None:
        warnings.append("AUROC is undefined for a single outcome class; it is not replaced by 0.5.")
    return {
        "contract": "ClinicalPredictionEvaluationV2",
        "status": "pass",
        "gate_eligible": False,
        "validation_scope": "numerical binary-prediction metrics only; independent scientific review required",
        "n": n,
        "events": events,
        "prevalence": prevalence,
        "partition_audit": {"status": "checked-provided-identifiers" if partition_verified else "not-assessed"},
        "patient_leakage_detected": False if partition_verified else None,
        "discrimination": {"auroc": _compute_auroc(yy, pp), "average_precision": _average_precision(yy, pp)},
        "calibration": calibration,
        "confidence_intervals": intervals,
        "decision_curve_analysis": {
            "thresholds_evaluated": curve,
            "thresholds_with_higher_net_benefit": better_thresholds,
            "clinical_benefit_established": False,
        },
        "conformal_prediction": conformal,
        "warnings": warnings,
        "issues": [],
    }
