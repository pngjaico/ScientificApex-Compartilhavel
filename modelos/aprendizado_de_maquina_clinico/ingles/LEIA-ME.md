# Clinical Machine Learning and Medical Artificial Intelligence

Canonical, consolidated environment for development, calibration, conformal prediction, survival analysis, and explainability of clinical predictive models following **TRIPOD+AI** and **PROBAST+AI** guidelines.

## Environment Architecture

The Python 3.13 environment is managed via `uv` with strict isolation and deterministic reproducibility:

1. **Core Tabular Machine Learning Stack (`modelos/aprendizado_de_maquina_clinico`):**
   - **Supervised Modeling & Ensembles:** `scikit-learn` (1.9.1), `xgboost` (3.4.1), `lightgbm` (4.7.0).
   - **Conformal Prediction & Finite-Sample Uncertainty:** `mapie` (1.6.0) with `SplitConformalClassifier` and `CrossConformalClassifier` providing prediction sets with finite-sample marginal coverage guarantees (e.g., 90% or 95%).
   - **Survival Analysis & Proportional Hazards:** `lifelines` (0.30.3) for Kaplan-Meier curves with confidence intervals, log-rank hypothesis testing, and multivariable Cox proportional hazards models (`CoxPHFitter`).
   - **Hyperparameter Optimization:** `optuna` (4.9.0) for efficient Bayesian optimization with pruning.
   - **Explainability & Interpretability (XAI):** `shap` (0.54.1) with `TreeExplainer` for exact local Shapley values and global feature impact (beeswarm and summary plots).
   - **Data Validation & Schema Contracts:** `pandera` (0.35.0) for strict schema checking and physiological bounds enforcement.
   - **Data Processing & Visualization:** `pandas` (2.3.3), `numpy` (2.5.4), `scipy` (1.18.1), `statsmodels` (0.15.0), `matplotlib` (3.11.2), `seaborn` (0.13.2), `plotly` (6.9.0).

2. **Deep Learning Sub-Environment (`ambientes/aprendizado_profundo`):**
   - `torch` (2.15.0+cpu), `torchvision`, `torchmetrics` for deep neural networks, biomedical embeddings, medical imaging, and physiological time-series analysis.

## Execution Guide

### 1. Environment Restoration
```powershell
uv sync --directory modelos/aprendizado_de_maquina_clinico
```

### 2. Running Scripts in Active Projects
```powershell
modelos/aprendizado_de_maquina_clinico/.venv/Scripts/python.exe projects/<project_id>/analysis/<script>.py
```

### 3. Validated Reference Implementation
Refer to the tested reference benchmark script:
`projects/article-machine-governance-2026/analysis/ambiente-r-2026-11-02/executar_bateria_python_ml.py`

## TRIPOD+AI Governance Rules
- **Never fit models without nested cross-validation or strict independent holdout test evaluation.**
- **Calibration curves and Brier score are mandatory alongside AUROC and AUPRC.**
- **Conformal prediction sets (MAPIE) must state empirical vs nominal coverage.**
- **Figures must be exported in 300 DPI (PNG) and vector format (SVG).**
