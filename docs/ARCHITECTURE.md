# Architecture and Contracts

## Production Components

| Component | Reads | Writes | Contract |
|---|---|---|---|
| `data_pipeline.py` | `datasets/raw/*.csv`, config | interim, processed, Excel, KPI reports | Stable keys, normalized tables, provenance |
| `train_models.py` | processed features, config | four models, metrics, forecasts, manifest | Group/chronological holdouts and artifact hashes |
| `shap_explainability.py` | registered models and features | SHAP CSV/PDF, updated manifest | Explanation model hash must match deployment model |
| `generate_executive_report.py` | governed KPI and insight files | executive PDF | Observed views lead; insight reliability is visible |
| `validate_project.py` | all production outputs | validation summary | Fails closed on relational or lineage defects |
| `load_mysql.py` | processed warehouse tables | MySQL tables | FK-order load and source/target row-count checks |
| `verify_mysql_deployment.py` | populated MySQL warehouse | status, table-count and KPI evidence reports | Database version, schema objects and exact query results |
| `streamlit/app.py` | CSV or explicitly selected MySQL, registry | interactive UI/downloads | No silent source fallback; model hash verification |

## Data Layers

- `raw`: immutable supplied files.
- `interim`: cleaned, source-shaped staging tables.
- `processed`: normalized dimensions/facts plus the model feature table.
- `reports`: governed analytical outputs and explanations.
- `models`: only production artifacts plus their registry.
- `models/experiments`: notebook artifacts that Streamlit never loads.

## Failure Behavior

The pipeline stops when a script fails. Project validation fails when keys,
foreign keys, dates, model hashes, dataset hashes, patient splits, target
provenance, or explanation lineage are invalid. MySQL mode fails visibly when
the database is unavailable rather than switching to CSV.

## Deployment Sequence

```text
ETL -> model evaluation/refit -> SHAP -> executive report -> validation
    -> optional MySQL load -> Streamlit/Power BI
```

Models are first evaluated on untouched holdouts. The selected estimator is
then refit on all development data for deployment. Holdout metrics remain the
reported performance; the refit is never re-evaluated on its training rows.
