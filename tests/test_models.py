from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
from supplier_tco.data import generate, validate, RISK, SUBINDICATORS
from supplier_tco.model import Scenario, tco, rank, sensitivity, risk_score, risk_pillars, COMPONENTS
from supplier_tco.simulation import simulate


def test_seed_and_regions():
    pd.testing.assert_frame_equal(generate(), generate())
    assert generate().region.value_counts().to_dict() == {'China':6, 'Europe':6}
    validate(generate())


def test_hand_calculation_and_no_double_count():
    df = generate().iloc[:1].copy()
    for c in ['purchase_eur','transport_eur','installation_eur','maintenance_eur_year','components_eur_year','energy_kwh_year','downtime_hours_year','decommission_eur']:
        df[c] = 10.
    df['fx_exposure'] = 1.
    df['customs_eur'] = 0.
    df['commissioning_eur'] = 0.
    s = Scenario(years=2, discount_rate=0, energy_price=2, downtime_eur_hour=3, maintenance_growth=0)
    # 30 upfront + 2*(10+10+20+30) + 10 disposal = 180.
    assert tco(df, s).tco_eur.iloc[0] == 180
    df['reliability'] = .1
    assert tco(df, s).tco_eur.iloc[0] == 180
    df[SUBINDICATORS] = 100
    assert tco(df, s).tco_eur.iloc[0] == 180


def test_discount_timing():
    df = generate().iloc[:1].copy()
    s = Scenario(years=1, discount_rate=.1)
    r = tco(df,s).iloc[0]
    assert r.decommission == pytest.approx(df.decommission_eur.iloc[0]/1.1)
    assert r.energy == pytest.approx(df.energy_kwh_year.iloc[0]*.15/1.1)


@pytest.mark.parametrize('field,value,direction', [('energy_price',.3,1),('maintenance_factor',1.5,1),('fx_factor',1.2,1),('years',20,1),('discount_rate',.1,-1)])
def test_sensitivity_monotonicity(field,value,direction):
    df=generate()
    delta=tco(df,replace(Scenario(),**{field:value})).tco_eur-tco(df).tco_eur
    assert (delta*direction > 0).all()


def test_fx_only_exposed_costs():
    df=generate(); df['fx_exposure']=0.
    np.testing.assert_allclose(tco(df).tco_eur,tco(df,Scenario(fx_factor=2)).tco_eur)


def test_score_weights_gate_and_region_neutrality():
    df=generate()
    df['mandatory_compliance']=False
    assert rank(df).score.isna().all()
    assert rank(df)['rank'].isna().all()
    assert simulate(df,draws=100)[0].probability_best.sum() == 0
    df=generate(); before=rank(df)
    df['region']=df.region.map({'China':'Europe','Europe':'China'})
    np.testing.assert_allclose(before.score,rank(df).score)
    with pytest.raises(ValueError): risk_score(df,dict.fromkeys(RISK,0))


def test_priority_changes_choice_and_shortlist_stability():
    df=generate()
    tradeoff = df.iloc[:2].copy()
    tradeoff.loc[tradeoff.index[0],SUBINDICATORS] = 80
    tradeoff.loc[tradeoff.index[1],SUBINDICATORS] = 10
    assert rank(tradeoff,cost_weight=.9,costs=[2e6,5e6]).iloc[0].supplier_id != rank(tradeoff,cost_weight=.2,costs=[2e6,5e6]).iloc[0].supplier_id
    full=rank(df).set_index('supplier_id').score
    sub=rank(df.iloc[:5]).set_index('supplier_id').score
    np.testing.assert_allclose(sub,full.loc[sub.index])


def test_simulation_reproducibility_intervals_and_expectation():
    df=generate()
    a,samples=simulate(df,draws=10000)
    b,_=simulate(df,draws=10000)
    pd.testing.assert_frame_equal(a,b)
    assert a.probability_best.sum() == pytest.approx(1)
    assert (a.p025<a.p50).all() and (a.p50<a.p975).all()
    assert (a.cvar95>=a.p95).all()
    assert (samples.tco_eur>0).all()
    np.testing.assert_allclose(a.mean_tco,tco(df).tco_eur,rtol=.015)


def test_gate_excluded_in_simulation():
    df=generate(); df.loc[0,'mandatory_compliance']=False
    assert simulate(df,draws=100)[0].probability_best.iloc[0] == 0


@pytest.mark.parametrize('kwargs',[{'years':0},{'years':2.5},{'discount_rate':-1},{'energy_price':np.nan},{'fx_factor':0}])
def test_invalid_scenarios(kwargs):
    with pytest.raises(ValueError): Scenario(**kwargs)


@pytest.mark.parametrize('column,value',[('energy_kwh_year',-1),('reliability',1.1),('quality_control_gap',101),('purchase_eur',np.inf)])
def test_invalid_data(column,value):
    df=generate(); df[column]=df[column].astype(float); df.loc[0,column]=value
    with pytest.raises(ValueError): validate(df)


def test_duplicate_and_missing():
    df=generate(); df.loc[1,'supplier_id']=df.loc[0,'supplier_id']
    with pytest.raises(ValueError): validate(df)
    with pytest.raises(ValueError): validate(generate().drop(columns='purchase_eur'))


def test_sensitivity_coverage_and_cost_reconciliation():
    df=generate(); out=tco(df)
    parts=COMPONENTS
    np.testing.assert_allclose(out[parts].sum(axis=1),out.tco_eur)
    assert sensitivity(df).parameter.nunique()==7


def test_real_escalation_and_cny_direction():
    df=generate()
    s=Scenario(years=2,discount_rate=.1,maintenance_growth=.05)
    expected_factor=1/1.1+1.05/1.1**2
    assert tco(df,s).maintenance.iloc[0] == pytest.approx(df.maintenance_eur_year.iloc[0]*expected_factor)
    assert (tco(df,Scenario(cny_per_eur=6.5)).tco_eur > tco(df,Scenario()).tco_eur).all()


def test_subindicator_weight_rule():
    from copy import deepcopy
    from supplier_tco.config import CONFIG
    df=generate()
    rules=deepcopy(CONFIG['risk_pillars'])
    rules['quality_governance']={'quality_control_gap':1,'traceability_gap':0}
    np.testing.assert_allclose(risk_pillars(df,rules).quality_governance,df.quality_control_gap)
    rules['quality_governance']={'quality_control_gap':0,'traceability_gap':0}
    with pytest.raises(ValueError): risk_pillars(df,rules)


def test_diagnostic_proxies_not_charged_twice():
    df=generate(); before=tco(df).tco_eur.copy(); scores=risk_score(df).copy()
    df['quality_rework_probability']=1.
    df['parts_lead_days']=500.
    df['support_response_hours']=200.
    df['disruption_probability']=1.
    np.testing.assert_allclose(tco(df).tco_eur,before)
    np.testing.assert_allclose(risk_score(df),scores)


def test_pairwise_and_group_probabilities():
    from supplier_tco.simulation import pairwise_probabilities,group_comparison
    _,samples=simulate(generate(),draws=100)
    pairs=pairwise_probabilities(samples).set_index(['supplier_a','supplier_b'])
    a,b=pairs.index[0]
    assert pairs.loc[(a,b),'probability_a_better']+pairs.loc[(b,a),'probability_a_better']+pairs.loc[(a,b),'probability_tie'] == pytest.approx(1)
    assert sum(group_comparison(samples).values()) == pytest.approx(1)
    samples['mcda_score']=50.
    assert pairwise_probabilities(samples).probability_tie.eq(1).all()
    assert group_comparison(samples)['probability_tie']==1


def test_simulation_escalation_matches_analytic_mean():
    df=generate(); s=Scenario(maintenance_growth=.05,energy_growth=.03,cny_per_eur=6.5)
    summary,_=simulate(df,s,draws=10000)
    np.testing.assert_allclose(summary.mean_tco,tco(df,s).tco_eur,rtol=.015)
