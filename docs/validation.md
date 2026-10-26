# Validation record

Validated locally on Python 3.12, 2026-10-26.

- `python -m pytest -q`: **30 passed**.
- Analytical checks: manual zero-rate cost reconciliation, discount timing, FX scope and five core sensitivity monotonicity checks, real annual escalation, and CNY conversion direction.
- Decision checks: region-label invariance, fixed-anchor shortlist stability, within-pillar weight validation, hard gates and all-ineligible handling.
- Simulation checks: seeded reproducibility, cost positivity, interval order, probability normalization, CVaR tail ordering, paired/group probability reconciliation, and simulated mean within 1.5% of analytical expectation over 10,000 draws.
- Dashboard checks: default run, purchasing-priority switch, lifetime change and invalid zero-weight handling via Streamlit AppTest.
- `python -m supplier_tco.report`: completed and regenerated numerical outputs, interpretation and offline Plotly chart.

This is local execution validation. GitHub Actions workflow is supplied but no remote CI run is claimed. AppTest verifies Streamlit execution and interactions, not pixel-level browser layout or a public deployment.

Tested direct dependencies:

```text
numpy==2.3.5
pandas==2.2.3
plotly==7.1.0
streamlit==1.66.1
pytest==9.1.1
```
