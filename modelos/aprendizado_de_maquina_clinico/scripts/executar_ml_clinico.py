"""Script canônico de avaliação metodológica para Modelos de Predição Clínica (TRIPOD+AI / PROBAST+AI).

Executa auditoria de vazamento por paciente, discriminação, calibração (intercepto, inclinação, Brier, ECE),
Análise de Curva de Decisão (DCA Net Benefit) e Predição Conforme (Split-Conformal), exportando
o results_ledger.json e relatórios bilíngues pareados (portugues/ e ingles/).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from article_machine.services.results_ledger import evaluate_clinical_prediction_metrics


def run_clinical_ml_pipeline(project_dir: Path, input_json: Path | None = None) -> dict[str, Any]:
    root = Path(project_dir).resolve()
    if input_json and Path(input_json).is_file():
        payload = json.loads(Path(input_json).read_text(encoding="utf-8"))
        y_true = [int(v) for v in payload["y_true"]]
        y_prob = [float(v) for v in payload["y_prob"]]
        train_ids = [str(v) for v in payload.get("patient_ids_train", [])] or None
        test_ids = [str(v) for v in payload.get("patient_ids_test", [])] or None
        is_synthetic = bool(payload.get("synthetic", False))
    else:
        # Demonstração determinística agrupada por paciente (uso exclusivamente mecânico/teste)
        y_true = [0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0]
        y_prob = [
            0.08, 0.12, 0.15, 0.78, 0.22, 0.84, 0.71, 0.19, 0.88, 0.67,
            0.11, 0.25, 0.74, 0.14, 0.81, 0.91, 0.09, 0.29, 0.76, 0.18,
        ]
        train_ids = [f"PAT_TRAIN_{i:03d}" for i in range(1, 41)]
        test_ids = [f"PAT_TEST_{i:03d}" for i in range(1, 21)]
        is_synthetic = True

    eval_report = evaluate_clinical_prediction_metrics(
        y_true,
        y_prob,
        patient_ids_train=train_ids,
        patient_ids_test=test_ids,
        conformal_alpha=0.10,
    )
    if eval_report["status"] != "pass":
        return eval_report

    analysis_dir = root / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    auroc = eval_report["discrimination"]["auroc"]
    brier = eval_report["calibration"]["brier_score"]
    citl = eval_report["calibration"]["calibration_intercept"]
    slope = eval_report["calibration"]["calibration_slope"]
    cov = eval_report["conformal_prediction"]["empirical_coverage"]

    ledger = {
        "contract": "ResultsLedgerV1",
        "synthetic_demonstration": is_synthetic,
        "metrics": {
            "n_test": str(eval_report["n"]),
            "events_test": str(eval_report["events"]),
            "auroc": f"{auroc:.3f}",
            "brier_score": f"{brier:.3f}",
            "calibration_intercept": f"{citl:.3f}",
            "calibration_slope": f"{slope:.3f}",
            "conformal_coverage": f"{cov:.3f}",
        },
        "full_evaluation": eval_report,
    }

    ledger_path = analysis_dir / "results_ledger.json"
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    pt_dir = analysis_dir / "portugues"
    en_dir = analysis_dir / "ingles"
    pt_dir.mkdir(parents=True, exist_ok=True)
    en_dir.mkdir(parents=True, exist_ok=True)

    aviso_pt = "Demonstração sintética de verificação mecânica (não representa coorte clínica real)." if is_synthetic else "Análise de coorte."
    aviso_en = "Synthetic mechanical verification run (does not represent a real clinical cohort)." if is_synthetic else "Cohort analysis."

    pt_md = (
        f"# Relatório Metodológico de Predição Clínica (TRIPOD+AI / PROBAST+AI)\n\n"
        f"> **Nota:** {aviso_pt}\n\n"
        f"- **Amostra avaliada ($N$):** {eval_report['n']} (eventos: {eval_report['events']})\n"
        f"- **Vazamento entre pacientes (treino vs. teste):** Zero sobreposição (`patient_leakage_detected: false`)\n"
        f"- **AUROC:** {auroc:.3f}\n"
        f"- **Brier Score:** {brier:.3f}\n"
        f"- **Calibração (Intercepto / In-the-large):** {citl:.3f}\n"
        f"- **Calibração (Inclinação / Slope):** {slope:.3f}\n"
        f"- **Cobertura Empírica Conforme ($1 - \\alpha = 0,90$):** {cov:.3f}\n"
        f"- **Limiares com Benefício Líquido Positivo (DCA):** {eval_report['decision_curve_analysis']['clinically_useful_thresholds']}\n"
    )

    en_md = (
        f"# Clinical Prediction Methodological Report (TRIPOD+AI / PROBAST+AI)\n\n"
        f"> **Note:** {aviso_en}\n\n"
        f"- **Evaluated sample ($N$):** {eval_report['n']} (events: {eval_report['events']})\n"
        f"- **Patient-level leakage (train vs. test):** Zero overlap (`patient_leakage_detected: false`)\n"
        f"- **AUROC:** {auroc:.3f}\n"
        f"- **Brier Score:** {brier:.3f}\n"
        f"- **Calibration Intercept (In-the-large):** {citl:.3f}\n"
        f"- **Calibration Slope:** {slope:.3f}\n"
        f"- **Empirical Conformal Coverage ($1 - \\alpha = 0.90$):** {cov:.3f}\n"
        f"- **Clinically Useful Net Benefit Thresholds (DCA):** {eval_report['decision_curve_analysis']['clinically_useful_thresholds']}\n"
    )

    (pt_dir / "relatorio_ml_clinico.md").write_text(pt_md, encoding="utf-8")
    (en_dir / "relatorio_ml_clinico.md").write_text(en_md, encoding="utf-8")

    return {
        "status": "pass",
        "ledger_path": ledger_path.relative_to(root).as_posix(),
        "portugues_report": (pt_dir / "relatorio_ml_clinico.md").relative_to(root).as_posix(),
        "ingles_report": (en_dir / "relatorio_ml_clinico.md").relative_to(root).as_posix(),
        "metrics": ledger["metrics"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Executa pipeline canônico de avaliação de ML clínico.")
    parser.add_argument("project_dir", help="Caminho do projeto ativo")
    parser.add_argument("--input", default=None, help="JSON opcional com y_true, y_prob e IDs de pacientes")
    args = parser.parse_args()
    res = run_clinical_ml_pipeline(Path(args.project_dir), Path(args.input) if args.input else None)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
