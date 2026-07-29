# Notebook R&D Pipeline

These notebooks document experimentation before logic is promoted into `src/`
and `streamlit/`. They are not the production runtime.

```text
datasets/raw/
  -> 01 Data cleaning
  -> 02 EDA
  -> 03 Feature engineering
  -> 04-07 Model experiments
  -> 08 Experiment SHAP
  -> models/experiments/ and reports/experiments/
```

Each notebook contains the business objective, imports, loading, validation,
stage-specific transformation or modeling, evaluation, visualization,
conclusions, and output persistence.

Run from the project root:

```powershell
python -m jupyter lab
```

Execute notebooks in numerical order. The maintained source is
`src/create_notebooks.py`; regenerate all eight with:

```powershell
python src/create_notebooks.py
```

Production artifacts are created only by `src/data_pipeline.py`,
`src/train_models.py`, and `src/shap_explainability.py`. Notebook models are
saved under `models/experiments/` so they cannot replace the registered
Streamlit models.

The source admissions and claims files have no shared identifiers. Claim links,
doctor aliases, demographics, department assignment, waiting time, and
capacity values are portfolio derivations or simulations, not observed facts.
