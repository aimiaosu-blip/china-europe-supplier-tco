# Methodology and research design

## Decision context
An independent portfolio demonstration inspired by the supplied thesis title, “Chinese vs. European Paint Shop Equipment Suppliers: Looking Beyond Price.” No affiliation, endorsement, official JD verification or company-specific specification is implied. No BMW or Volvo data is used.

Functional unit: one hypothetical, functionally equivalent paint-shop equipment package at a European plant, meeting the same capacity and finish specification, operating 4,000 planned hours/year. All suppliers share a common evaluation horizon. Scope is the package rather than the complete paint-shop line. Costs are synthetic base-year real EUR, excluding recoverable VAT, financing and taxes. The region label has no direct effect on generation, discounting, risk or utility.

## Research questions and illustrative hypotheses
- RQ1: When does the lowest purchase price fail to minimize discounted lifecycle cost? H1: supplier heterogeneity can change the winner after operations costs are included.
- RQ2: How do sourcing priorities alter supplier choice? H2: changing cost-versus-residual-risk weights can change the preferred supplier.
- RQ3: How robust are rankings to input uncertainty? H3: overlapping simulated cost intervals can produce less certain preferences than deterministic ranks suggest.
- RQ4: What evidence is required for a defensible China–Europe comparison? The next empirical stage needs comparable RFQs, sampling criteria, verified records and controls for specification, contract terms, scale and technology.

These are exploratory demonstrations, not statistical hypothesis tests using empirical supplier observations. Six suppliers per region are not representative samples. Generated countries are labels; country superiority cannot be inferred.

## Discounted lifecycle TCO
For supplier i, lifetime N and real discount rate r:

TCO_i = purchase_i × FX_i + transport_i + customs_i + installation_i + commissioning_i
+ sum over t=1..N of [(maintenance_i × M + parts_i × M × FX_i) × (1+g_m)^(t−1) + kWh_i × energy_price × (1+g_e)^(t−1) + downtime_hours_i × lost_margin_per_hour] / (1+r)^t
+ decommission_i / (1+r)^N.

FX_i = 1 + exposure_i × (FX_multiplier × reference_CNY_per_EUR / scenario_CNY_per_EUR − 1). A multiplier >1 increases EUR cost of exposed purchase and components. Reference CNY per EUR is 7.8, an invented base conversion, not a live FX quote. The exposed share is assumed CNY-denominated even for some European-labelled packages (e.g. imported subcomponents). This is a contract-currency stress, not a claim about real invoicing patterns. The generic FX multiplier is an additional stress; leave it at 1 when testing only CNY/EUR. Maintenance labour, logistics, customs, installation and commissioning are assumed EUR contracted. Customs is a fixed synthetic all-in allowance, not a tariff rate calculation; recoverable import VAT is excluded. Installation covers physical setup; commissioning covers acceptance/startup, excluding installation labour already counted. Both groups can have import content; no regional tariff assumption is imposed. M applies to labour maintenance and components, which are mutually exclusive cost buckets. g_m is annual real maintenance/parts escalation (default 2%); g_e is annual real energy escalation (default 0%). Year 1 uses the base amount, subsequent years escalate. Because all values are real, do not mix nominal inflation or nominal WACC without consistent conversion. Upfront payments occur at t=0; recurring payments at year end; disposal at N. Zero discount rates are handled directly without division by r.

Expected downtime is already unconditional expected lost productive hours per year. Do not multiply it again by failure probability or (1−reliability). Lost contribution margin excludes energy/material savings and service invoices already represented elsewhere. Reliability is a separate synthetic mission-success diagnostic with no assumed mapping to annual downtime; it is deliberately not charged or scored. Actual calibration should reconcile the two measures.

Equivalent annual cost is TCO divided by the discounted annuity factor. For lifetime sensitivity, longer service changes total output; equivalent annual cost helps comparison but does not replace a full common-horizon replacement-chain model. No claimed optimal replacement age is calculated.

## Residual risk rubric and evidence
All scores range from 0 (low residual evidence/governance risk) to 100 (high). Demonstration values are random draws, not audited observations. A practical rubric could use 0=verified and independently evidenced; 25=documented with minor gaps; 50=material verification gaps; 75=weak or incomplete controls; 100=unacceptable/absent controls. These rubric anchors are normative assumptions. Two sub-indicators feed each pillar as a normalized weighted average (defaults 50/50). The exact mapping and both weight levels are in `config/model.json`. Within-pillar rules and values are validated; zero-sum or negative weights are rejected. These are evidence-gap scores, not automatically inferred from the diagnostic operational proxies.

| Dimension | Illustrative evidence to collect | Boundary against monetary overlap |
|---|---|---|
| Quality and reliability governance | Acceptance-test traceability, change control, quality audits | Excludes expected failures/downtime already monetized |
| Compliance and sustainability | Verified regulatory documentation, chemical stewardship, supplier environmental reporting | Mandatory legality is a gate; no duplicate energy/emissions cost |
| Lifecycle service governance | Contract enforceability, technical documentation access, skills transfer, escalation ownership | Excludes maintenance prices, component invoices and expected repair delays |
| Geopolitical and supply continuity | Contract/jurisdiction due diligence, alternative route readiness, export-control screening evidence | No expected disruption losses added; residual readiness only |

Compliance here is an invented Boolean scenario gate; neither scores nor the gate are legal assessments. No claims are made about current regulatory requirements. Sustainability is evidence/governance maturity, not a measured carbon footprint or full lifecycle assessment.

Four dimension weights are normalized after validation. Default: equal weights. A quality-control score may correlate with failure cost in practice, so conceptual separation alone does not prove statistical independence. Empirical use requires an overlap workshop, correlation checks and removal/orthogonalization of duplicated criteria.

## MCDA
Additive utility = 100 × [w_cost × U_cost + (1−w_cost) × U_residual_risk].
U_cost = clip((EUR 8m − TCO)/EUR 6m, 0, 1); U_residual_risk = 1 − weighted_risk/100.

Fixed EUR 2m (best) and EUR 8m (worst) cost anchors are illustrative preference anchors, not market benchmarks. They avoid normalization changing when suppliers are added or removed, but clip extreme scenarios and create ties. Inspect raw costs alongside scores, and recalibrate anchors with stakeholders for a different equipment scope. Scores are not cardinal monetary value. Mandatory compliance failure excludes a supplier even if price is attractive. No feasible option means no recommendation. Tied ranks are retained.

Priorities: cost-led 90% cost; balanced 60%; resilience-led 20%. Default within-risk weights are equal, so resilience-led means broad residual-risk preference, not solely geopolitical weight. Users can change individual dimensions. A compensatory model assumes preferential independence; severe non-compensatory concerns belong in additional gates before ranking.

## Monte Carlo
5,000 default joint draws, deterministic seed 2026. Costs are propagated with positive mean-one lognormal multipliers: energy coefficient of variation 20%; exposed FX 10%; supplier-specific maintenance/parts 20%; supplier-specific downtime 35%. Energy and FX shocks are shared across suppliers in each draw for fair paired comparison. They are independent of each other. Supplier maintenance and downtime shocks are independent; maintenance and parts share their supplier's multiplier. Multipliers persist through the full horizon, representing uncertainty in long-run levels, not annual stochastic paths.

Each of the eight residual sub-indicators follows a Beta(mean×30, (1−mean)×30) distribution scaled to 0–100; boundary means are clipped to .001/.999. Sub-indicator scores are assumed independent of each other and costs, then aggregated through the same within-pillar and pillar weights as deterministic MCDA. Concentration 30 is an uncalibrated uncertainty assumption. The model does not simulate named geopolitical events or falsely equate governance scores to disruption probabilities.

Outputs: mean, median, 2.5th/97.5th percentiles, 95th percentile and CVaR95 (conditional average above the sampled 95th percentile); approximate 95% Monte Carlo mean CI = mean ±1.96×sample SD/sqrt(draws). The mean CI describes numerical estimation error under the model, not confidence in real supplier costs. Probability-best is the fraction of joint draws with maximal feasible MCDA utility, splitting exact ties. The dashboard's tail comparison replaces mean TCO with CVaR95. It never adds CVaR or a generic risk premium to already monetized losses.

## Sensitivity design
One-factor-at-a-time grids include the active baseline: energy .08/.15/.25 EUR/kWh; maintenance and components .7/1/1.3; FX .8/1/1.2; lifetime 10/15/20 years; real discount rate 2/6/10%. These are stress choices, not forecasts. Interactive controls allow combined scenarios. Additional grids: real maintenance escalation 0/2/5% annually and CNY per EUR 6.5/7.8/9.0. The dashboard also permits real energy escalation. No global Sobol sensitivity, dependence estimation, calibrated inflation forecast or dynamic event simulation is claimed.

## Limitations and empirical extension
No real quotes, certifications, failure records or country-risk ratings. Equal functional output is assumed rather than established through engineering acceptance tests. No salvage, statutory tariff calculation, tax, financing, working capital, ramp-up, technical obsolescence, non-energy consumables, emissions pricing or detailed annual replacement schedules. Replacement components are a smoothed annual allowance, excluding maintenance labour. No full lifecycle emissions claim. Synthetic quality-rework probability, spare-part lead days, support-response hours and annual disruption probability are diagnostic proxies only. They are not separately charged or scored because expected downtime already summarizes operational disruption and scrap/rework costs are not independently specified. No empirical regional conclusion, cost savings or business impact may be reported.

For field research: define sampling and selection bias controls; obtain matched specifications and Incoterms; verify compulsory compliance; reconcile cost buckets with finance; fit distributions and correlations from records; elicit risk weights and utility anchors; validate out of sample; interview service/engineering stakeholders; report uncertainty and sensitivity before recommending a shortlist.

## Probability questions must remain distinct
1. P(A > B): frequency with which A has higher MCDA utility than B in the same joint draw. Exact ties are reported separately. `mc_standard_error` is the Monte Carlo standard error of this frequency, not empirical confidence in the supplier.
2. Probability-best: frequency of maximal utility across the whole eligible shortlist, with ties split.
3. Group-mean comparison: frequency that average utility across eligible China-labelled profiles exceeds that across eligible Europe-labelled profiles. It is a finite-shortlist statistic and is not a probability of national supplier superiority. Group results are regenerated for all three configured priority settings.

## Configuration and reproducibility
All model defaults, generation bounds, risk maps/weights, simulation distributions, utility anchors and sensitivity grids are externalized in `config/model.json`. Restart Streamlit after editing it, regenerate data only when generator settings change, then rerun tests and reports. Hard-coded input-validation bounds are software safeguards, not calibrated procurement assumptions. Closed-form discounted cash-flow aggregation and vectorized Monte Carlo implement the formulas above directly without trained/black-box models. The derivation and manual-calculation tests are the formula reference; this is not a claim of compliance with a particular costing standard.
