# Data Governance and Decision Use

## Source Limitation

Admissions and claims do not share a patient or encounter identifier. The
project cannot prove which claim belongs to which admission. It preserves the
original claim identifiers and creates a deterministic surrogate link only to
demonstrate an end-to-end warehouse and application.

## Interpretation Rules

| Reliability | Use |
|---|---|
| Observed | Descriptive evidence within the supplied source data |
| Derived from observed fields | Screening, segmentation, and reproducible analysis |
| Simulated | Demonstration of a future workflow; never an operational conclusion |
| Mixed surrogate/simulated | Scenario planning only |
| Assumption | Sensitivity analysis; replace before deployment |

The hospital efficiency score is a transparent portfolio composite: 40%
patient outcomes, 30% collections, 20% capacity balance, and 10% patient flow.
Department scores use a derived dimension, emergency waiting time is simulated,
and capacity uses the configured 500-bed assumption. The score is suitable for
portfolio demonstration, not approved hospital performance management.

## Model Gates

- Readmission predictions require local clinical validation, calibration,
  fairness testing, and prospective monitoring before care use.
- Waiting-time modeling requires arrival, triage, service-start, and discharge
  timestamps from a real queue system.
- Revenue attribution requires a governed encounter-to-claim key and audited
  cost/reimbursement definitions.
- Occupancy deployment requires authoritative staffed-bed capacity, closures,
  transfers, reservations, and service-line constraints.

## Operationalization Checklist

1. Replace deterministic dimensions with master patient, provider, department,
   and medication identifiers.
2. Replace the surrogate claim link with a governed encounter key.
3. Add role-based access, encryption, secrets management, and audit logging.
4. Remove or tokenize direct identifiers and complete privacy review.
5. Add temporal/site external validation, calibration, drift, and fairness
   monitoring.
6. Define KPI ownership, refresh SLAs, escalation thresholds, and approval.
7. Require human review for every clinical or staffing recommendation.

The generated `reports/feature_provenance.csv` is the machine-readable source of
truth for field classification. `reports/business_insights.csv` is the
governed insight layer consumed by reports and dashboards.
