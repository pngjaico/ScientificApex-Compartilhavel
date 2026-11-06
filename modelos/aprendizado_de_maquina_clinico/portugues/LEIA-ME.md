# Aprendizado de Máquina Clínico e Inteligência Artificial Médica

Ambiente canônico consolidado para desenvolvimento, calibração, predição conformal, análise de sobrevida e explicabilidade de modelos preditivos clínicos sob as diretrizes **TRIPOD+AI** e **PROBAST+AI**.

## Estrutura do Ambiente

O ambiente Python 3.13 é gerenciado via `uv` com isolamento completo e reprodutibilidade determinística:

1. **Stack Principal de Machine Learning Tabular (`modelos/aprendizado_de_maquina_clinico`):**
   - **Modelagem Supervisionada e Ensembles:** `scikit-learn` (1.9.1), `xgboost` (3.4.1), `lightgbm` (4.7.0).
   - **Predição Conformal e Incerteza Finita:** `mapie` (1.6.0) com `SplitConformalClassifier` e `CrossConformalClassifier` para conjuntos de predição com cobertura marginal comprovada (ex: 90% ou 95%).
   - **Análise de Sobrevida e Riscos Proporcionais:** `lifelines` (0.30.3) para curvas de Kaplan-Meier com intervalos de confiança, testes de log-rank e modelos multivariáveis de Cox (`CoxPHFitter`).
   - **Otimização e Hiperparâmetros:** `optuna` (4.9.0) para busca Bayesiana eficiente com pruning de tentativas.
   - **Explicabilidade e Interpretabilidade (XAI):** `shap` (0.54.1) com `TreeExplainer` para cálculo exato de valores de Shapley locais e impacto global (beeswarm / summary plots).
   - **Validação de Dados e Contratos:** `pandera` (0.35.0) com verificação estrita de esquemas e limites fisiológicos.
   - **Manipulação e Visualização:** `pandas` (2.3.3), `numpy` (2.5.4), `scipy` (1.18.1), `statsmodels` (0.15.0), `matplotlib` (3.11.2), `seaborn` (0.13.2), `plotly` (6.9.0).

2. **Subambiente de Deep Learning Clínico (`ambientes/aprendizado_profundo`):**
   - `torch` (2.15.0+cpu), `torchvision`, `torchmetrics` para redes neurais profundas, embeddings biomédicos e análise de imagem ou séries temporais.

## Como Executar

### 1. Restauração do Ambiente
```powershell
uv sync --directory modelos/aprendizado_de_maquina_clinico
```

### 2. Execução de Scripts em Projetos Ativos
```powershell
modelos/aprendizado_de_maquina_clinico/.venv/Scripts/python.exe projects/<project_id>/analysis/<script>.py
```

### 3. Exemplo Prático de Script Completo
Consulte o script de referência validado:
`projects/article-machine-governance-2026/analysis/ambiente-r-2026-11-02/executar_bateria_python_ml.py`

## Diretrizes de Governança TRIPOD+AI
- **Nunca treinar sem validação cruzada aninhada (nested CV) ou separação estrita de teste independente.**
- **Curvas de calibração e Brier score são obrigatórios ao lado da AUROC e AUPRC.**
- **Conjuntos conformais (MAPIE) devem reportar cobertura empírica vs nominal.**
- **Figuras geradas devem ser salvas em 300 DPI (PNG) e formato vetorial (SVG).**
