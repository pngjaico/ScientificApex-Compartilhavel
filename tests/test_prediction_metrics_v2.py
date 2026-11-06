"""Numerical/adversarial checks; synthetic predictions, never clinical evidence."""

import json
import math

import pytest

from article_machine.services.results_ledger import evaluate_clinical_prediction_metrics as evaluate

Y = [0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1]
P = [0.1, 0.2, 0.15, 0.4, 0.35, 0.55, 0.45, 0.65, 0.8, 0.75, 0.6, 0.9]


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), -0.1, 1.1, "0.5", None, True])
def test_invalid_probability_is_blocked(bad):
    report = evaluate([0, 1], [0.2, bad])
    assert report["status"] == "blocked"


def test_metrics_match_independent_reference_values():
    # Reference sklearn AUROC/AP/Brier and unpenalized statsmodels GLM, fixed fixture.
    report = evaluate(Y, P)
    assert report["status"] == "pass"
    assert report["discrimination"]["auroc"] == pytest.approx(2 / 3)
    assert report["discrimination"]["average_precision"] == pytest.approx(0.7529461279461279)
    assert report["calibration"]["brier_score"] == pytest.approx(0.23791666666666667)
    assert report["calibration"]["calibration_intercept"] == pytest.approx(0.04454879519279348, abs=1e-7)
    assert report["calibration"]["calibration_slope"] == pytest.approx(0.5428082539236202, abs=1e-7)
    assert report["patient_leakage_detected"] is None
    assert report["partition_audit"]["status"] == "not-assessed"
    assert report["gate_eligible"] is False
    assert report["conformal_prediction"]["status"] == "not-assessed"
    json.dumps(report, allow_nan=False)


def test_auc_ties_and_constant_calibration_do_not_invent_a_slope():
    report = evaluate([0, 1] * 10, [0.5] * 20)
    assert report["discrimination"]["auroc"] == 0.5
    assert report["discrimination"]["average_precision"] == 0.5
    assert report["calibration"]["calibration_slope"] is None
    assert report["calibration"]["ece"] == 0


def test_one_class_and_separation_are_not_ideal_calibration():
    single = evaluate([1, 1], [0.5, 0.8])
    assert single["discrimination"]["auroc"] is None
    assert single["calibration"]["calibration_slope"] is None
    perfect = evaluate([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
    assert perfect["discrimination"]["auroc"] == 1
    assert perfect["calibration"]["calibration_slope"] is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"patient_ids_train": ["a"], "patient_ids_test": ["a", "b"]},
        {"patient_ids_train": ["a"], "patient_ids_test": ["b"]},
        {"patient_ids_train": ["a"], "patient_ids_test": ["b", "b"]},
        {"thresholds": [0, 0.5]},
        {"thresholds": [1]},
        {"thresholds": [math.nan]},
        {"conformal_alpha": 1},
        {"conformal_alpha": 0},
        {"conformal_alpha": math.nan},
        {"bootstrap_repeats": 1},
        {"bootstrap_repeats": -1},
        {"random_seed": {}},
    ],
)
def test_bad_partitions_and_parameters_fail_closed(kwargs):
    assert evaluate([0, 1], [0.2, 0.8], **kwargs)["status"] == "blocked"


def _conformal_kwargs():
    return {
        "patient_ids_train": ["train0", "train1"],
        "patient_ids_test": ["test0", "test1", "test2"],
        "calibration_y_true": [0, 1, 0, 1, 0],
        "calibration_y_prob": [0.2, 0.8, 0.3, 0.7, 0.4],
        "patient_ids_calibration": [f"cal{i}" for i in range(5)],
    }


def test_conformal_uses_calibration_only_and_scores_separate_test():
    report = evaluate([0, 1, 1], [0.1, 0.5, 0.9], conformal_alpha=0.2, **_conformal_kwargs())
    conformal = report["conformal_prediction"]
    assert report["status"] == "pass"
    assert conformal["quantile_threshold"] == pytest.approx(0.4)
    assert conformal["empirical_coverage"] == pytest.approx(2 / 3)
    assert conformal["prediction_sets"] == [[0], [], [1]]
    assert conformal["exchangeability_verified"] is False
    changed = evaluate([1, 0, 0], [0.1, 0.5, 0.9], conformal_alpha=0.2, **_conformal_kwargs())
    assert changed["conformal_prediction"]["quantile_threshold"] == conformal["quantile_threshold"]


def test_conformal_small_calibration_uses_infinite_order_statistic_honestly():
    report = evaluate([0, 1, 1], [0.1, 0.5, 0.9], conformal_alpha=0.05, **_conformal_kwargs())
    conformal = report["conformal_prediction"]
    assert conformal["threshold_is_infinite"] is True
    assert conformal["quantile_threshold"] is None
    assert conformal["prediction_sets"] == [[0, 1]] * 3
    json.dumps(report, allow_nan=False)


def test_conformal_missing_or_overlapping_partitions_are_blocked():
    params = _conformal_kwargs()
    params.pop("patient_ids_calibration")
    assert evaluate([0, 1, 1], [0.1, 0.5, 0.9], **params)["status"] == "blocked"
    params = _conformal_kwargs()
    params["patient_ids_calibration"][0] = "test0"
    assert evaluate([0, 1, 1], [0.1, 0.5, 0.9], **params)["status"] == "blocked"


def test_patient_bootstrap_is_reproducible_and_does_not_claim_clinical_utility():
    kwargs = {
        "patient_ids_train": ["training"],
        "patient_ids_test": [f"t{i}" for i in range(len(Y))],
        "bootstrap_repeats": 50,
        "random_seed": 123,
    }
    a, b = evaluate(Y, P, **kwargs), evaluate(Y, P, **kwargs)
    assert a == b
    interval = a["confidence_intervals"]["brier"]
    assert interval[0] <= a["calibration"]["brier_score"] <= interval[1]
    assert a["decision_curve_analysis"]["clinical_benefit_established"] is False
