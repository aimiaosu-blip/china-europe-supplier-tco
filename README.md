# China–Europe Industrial Supplier Evaluation & TCO Analytics

**A reproducible procurement research prototype: purchase price → lifecycle cost → residual-risk scorecard → sourcing decision.**

Built as an independent portfolio project for the thesis topic *Chinese vs. European Paint Shop Equipment Suppliers: Looking Beyond Price*. No affiliation or endorsement is implied.

> **100% SYNTHETIC DATA.** The 12 suppliers are fictional. No BMW, Volvo, confidential company data or real supplier ratings are included. Simulation findings do not establish differences between Chinese and European suppliers.

## What works
- Reproducible dataset: 6 China-labelled and 6 Europe-labelled suppliers generated from identical distributions.
- Discounted real-EUR lifecycle TCO: acquisition, logistics/customs, installation/commissioning, maintenance, components, energy, expected downtime and decommissioning.
- Sensitivity analysis: energy price, maintenance level and annual real escalation, FX exposure and CNY/EUR, equipment lifetime and discount rate; equivalent annual cost is reported alongside lifetime cost.
- Transparent residual-risk assessment across four dimensions and eight sub-indicators, configurable weights and a mandatory-compliance gate.
- Fixed-anchor MCDA rankings for cost-led, balanced and resilience-led purchasing priorities.
- Seeded Monte Carlo with shared market shocks, supplier-specific uncertainty, residual risk distributions, cost percentiles, mean confidence intervals, CVaR95, paired supplier probabilities and group-mean comparisons under three priorities.
- Streamlit/Plotly dashboard, CSV exports, offline interactive chart and pytest tests, including dashboard execution.

## Quick start
Python 3.12 is the tested runtime; Python 3.11+ is declared. From the repository root:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m supplier_tco.report
python -m streamlit run app.py
```

Open the local address printed by Streamlit. No API keys, login, databases or external data services are needed. Installation needs package-registry access; model execution is local. This is a local dashboard, not a deployed public web service.

To regenerate the committed dataset exactly (defaults, distributions and scoring rules are in `config/model.json`; restart the app after config changes):

```bash
python generate_synthetic_data.py
python -m supplier_tco.report
```

Dataset seed: **42**. Simulation seed: **2026**. Default simulation: **5,000 joint draws × 12 suppliers**. Top-level dependencies are pinned; transitive dependencies are resolved by pip, so this is not a byte-for-byte environment lock. Numerical tolerances and seeds support reproducibility across compatible environments.

## Dashboard walkthrough
Choose a purchasing priority, then change energy price, CNY/EUR or real maintenance escalation. Review the dynamic ranking, cost waterfall and residual-risk heatmap. Inspect paired supplier probabilities and cost/risk distributions, then use the sensitivity tornado to identify the largest model drivers. Download CSV outputs for procurement review.

## Model integrity
Expected downtime is monetized once. Reliability is a diagnostic, not a second loss multiplier. Non-monetary risk criteria cover residual evidence/governance gaps and do not repeat maintenance, energy or expected failure losses. Mandatory compliance is an eligibility gate. CVaR replaces expected cost in the tail-cost comparison rather than being added to it. Region labels do not determine scores.

Base assumptions: 15-year common horizon; 6% real discount rate; 2% real annual maintenance escalation; EUR 0.15/kWh; EUR 2,500/hour lost contribution margin. These numbers and the EUR 2m/8m MCDA utility anchors are illustrative assumptions, not market benchmarks.

## Example findings from the default synthetic run
Purchase-price leader: **SYN-09**; lifecycle-cost leader: **SYN-12**. The three default cost-versus-risk mixes all prefer SYN-12. Single-pillar stress cases demonstrate how concentrated priorities can change the preferred supplier; they are diagnostics, not recommended procurement weights. These observations describe only this artificial dataset.

## Review the evidence
- [Methodology, research questions, assumptions and limitations](docs/methodology.md)
- [Complete data dictionary](docs/data_dictionary.md)
- [Generated results interpretation](docs/results_interpretation.md)
- [Baseline cost breakdown](results/baseline_tco.csv)
- [Sensitivity outputs](results/sensitivity.csv)
- [Monte Carlo summary](results/monte_carlo_summary.csv)
- [Offline interactive comparison](results/supplier_comparison.html) — download and open locally
- [Reproduction manifest](results/run_manifest.json)
- [CV wording](docs/cv_bullets.md)
- [Validation record](docs/validation.md)
- [Purchase-price versus TCO ranks](results/purchase_vs_tco_ranks.csv)
- [Paired supplier probabilities](results/pairwise_probabilities.csv)
- [Group comparisons by priority](results/group_probabilities.csv)

## Repository map
```
app.py                       Interactive dashboard
config/model.json            Externalized modelling assumptions
generate_synthetic_data.py   Dataset generation entry point
supplier_tco/data.py         Generator, schema validation and loading
supplier_tco/model.py        TCO, residual score, MCDA and sensitivity
supplier_tco/simulation.py   Joint simulation and uncertainty metrics
supplier_tco/report.py       Rebuild results and interpretation
 data/                       Labelled synthetic supplier CSV
 docs/                       Research documentation
 results/                    Reproducible numerical outputs and chart
 tests/                      Analytical, validation and UI smoke tests
```

## Interpretation boundaries
This prototype demonstrates methods, not real procurement recommendations. Actual sourcing requires matched engineering specifications, supplier evidence, verified mandatory compliance, calibrated uncertainty, agreed weights and finance review. Real service/governance scores can correlate with monetary losses; criterion overlap must be reassessed with empirical data. Cost and uncertainty assumptions can change rankings substantially. No real-world cost savings are claimed.

## License
MIT for code and synthetic data; see [LICENSE](LICENSE).
