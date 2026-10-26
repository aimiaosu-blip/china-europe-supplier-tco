# Synthetic supplier data dictionary

Source: `python generate_synthetic_data.py`; generation assumptions live in `config/model.json`. Seed 42, 12 fictional packages, 6 per region. Every distribution is identical across region labels. Uniform bounds are design assumptions, not observed market ranges. All cash inputs are real base-year EUR. Fractions use 4 decimal places; other numeric inputs use 2.

| Field | Unit / type | Bounds or value | Meaning and use |
|---|---|---|---|
| supplier_id | string | SYN-01…SYN-12 | Fictional unique identifier |
| region | category | China / Europe | Display and finite-shortlist comparison only |
| synthetic | boolean | True | Mandatory provenance label |
| mandatory_compliance | boolean | True in generated sample | Synthetic eligibility gate, not certification |
| purchase_eur | real EUR | Uniform 800000–1500000 | Year-0 equipment price; CNY-exposed fraction stressed |
| transport_eur | real EUR | Uniform 30000–100000 | Year-0 freight/logistics; excludes customs |
| customs_eur | real EUR | Uniform 0–65000 | Fixed synthetic customs allowance; excludes recoverable VAT |
| installation_eur | real EUR | Uniform 90000–180000 | Physical equipment installation; excludes commissioning |
| commissioning_eur | real EUR | Uniform 20000–70000 | Year-0 startup and acceptance testing |
| maintenance_eur_year | real EUR/year | Uniform 25000–65000 | Year-1 service/labour, excludes spare parts |
| components_eur_year | real EUR/year | Uniform 10000–35000 | Year-1 replacement-parts allowance, excludes labour |
| energy_kwh_year | kWh/year | Uniform 600000–1300000 | Expected energy for common production output |
| downtime_hours_year | hours/year | Uniform 10–60 | Unconditional expected lost productive hours, monetized once |
| reliability | fraction | Uniform 0.9–0.995 | Mission-success diagnostic only, no extra loss multiplier |
| fx_exposure | fraction | Uniform 0–1 | CNY-denominated share of price and components |
| decommission_eur | real EUR | Uniform 20000–50000 | Final-year disposal, zero salvage |
| quality_rework_probability | fraction | Uniform 0.005–0.06 | Synthetic lot-rework likelihood; diagnostic, not an additional charge |
| parts_lead_days | days | Uniform 5–90 | Synthetic spare-part delivery lead time; diagnostic only |
| support_response_hours | hours | Uniform 2–48 | After-sales first response proxy, not repair completion; diagnostic |
| disruption_probability | fraction/year | Uniform 0.01–0.15 | Synthetic chance of a supply disruption; diagnostic, not double-charged |
| quality_control_gap | 0–100 residual risk | Uniform 10–75 | quality_governance; lower preferred |
| traceability_gap | 0–100 residual risk | Uniform 10–75 | quality_governance; lower preferred |
| compliance_evidence_gap | 0–100 residual risk | Uniform 10–75 | compliance_sustainability; lower preferred |
| esg_evidence_gap | 0–100 residual risk | Uniform 10–75 | compliance_sustainability; lower preferred |
| service_contract_gap | 0–100 residual risk | Uniform 10–75 | service_governance; lower preferred |
| spare_strategy_gap | 0–100 residual risk | Uniform 10–75 | service_governance; lower preferred |
| geopolitical_controls_gap | 0–100 residual risk | Uniform 10–75 | supply_continuity; lower preferred |
| logistics_contingency_gap | 0–100 residual risk | Uniform 10–75 | supply_continuity; lower preferred |

## Pillars and explicit aggregation
Each pillar is the normalized weighted mean of its two sub-indicators (default equal weights); overall risk is the weighted mean of four pillars (default equal weights). Zero means verified control/evidence and 100 means absent/unacceptable evidence. Scores are synthetic; no actual audit took place.

| Pillar | Sub-indicators | Default split |
|---|---|---|
| quality_governance | quality_control_gap, traceability_gap | 50% / 50% |
| compliance_sustainability | compliance_evidence_gap, esg_evidence_gap | 50% / 50% |
| service_governance | service_contract_gap, spare_strategy_gap | 50% / 50% |
| supply_continuity | geopolitical_controls_gap, logistics_contingency_gap | 50% / 50% |

## Main outputs
- Cost components are mutually exclusive present values in EUR. `tco_eur` sums them; `equivalent_annual_eur` divides by the discounted annuity factor.
- `residual_risk` is the aggregate 0–100 score. `cost_utility` and `risk_utility` are 0–1. `score` is weighted utility ×100. `rank` is descending with tied ranks retained. Failed compliance produces null score/rank.
- Sensitivity: `parameter`, `value`, `delta_eur` (change from active baseline).
- Simulation: `mean_tco`, `p50`, `p025`, `p975`, `p95`, `cvar95`; `mean_ci_low/high` are approximate 95% Monte Carlo mean CIs. `risk_p025/p975` are simulated residual-risk interval endpoints.
- `probability_best` is joint-draw maximal-score frequency, splitting ties. `draw` identifies paired scenarios. `mcda_score` is per-draw utility; null for ineligible suppliers.
- Pairwise output: `supplier_a`, `supplier_b`, `probability_a_better`, `probability_tie`, `mc_standard_error`.
- Group output: probability that eligible China-label mean utility is higher, Europe-label mean utility is higher, or means tie. This is not a national population inference.
- Price comparison: `purchase_rank`, `tco_rank`, `rank_change` (positive = improves under TCO).

Diagnostic rework, lead-time, response, reliability and disruption fields are shown for due-diligence context. They do not feed scores or extra monetary charges. An empirical extension must reconcile them with downtime and avoid counting the same losses twice.
