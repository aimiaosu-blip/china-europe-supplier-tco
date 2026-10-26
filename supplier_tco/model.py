"""Discounted EUR lifecycle costs, residual risk scorecards and MCDA."""
from dataclasses import dataclass, replace
import numpy as np
import pandas as pd
from .data import validate, RISK
from .config import CONFIG

DEFAULT = CONFIG['scenario']
COMPONENTS = ['purchase', 'transport', 'customs', 'installation', 'commissioning',
              'maintenance', 'components', 'energy', 'downtime', 'decommission']

@dataclass(frozen=True)
class Scenario:
    years: int = DEFAULT['years']
    discount_rate: float = DEFAULT['discount_rate']
    energy_price: float = DEFAULT['energy_price']
    maintenance_factor: float = DEFAULT['maintenance_factor']
    fx_factor: float = DEFAULT['fx_factor']
    downtime_eur_hour: float = DEFAULT['downtime_eur_hour']
    maintenance_growth: float = DEFAULT['maintenance_growth']
    energy_growth: float = DEFAULT['energy_growth']
    cny_per_eur: float = DEFAULT['cny_per_eur']

    def __post_init__(self):
        if isinstance(self.years, bool) or not isinstance(self.years, (int, np.integer)) or not 1 <= self.years <= 40:
            raise ValueError('Lifetime must be an integer from 1 to 40 years')
        for key in ['discount_rate','energy_price','maintenance_factor','fx_factor','downtime_eur_hour','cny_per_eur']:
            value = getattr(self, key)
            if not np.isfinite(value) or value < 0:
                raise ValueError(f'{key} must be finite and nonnegative')
        for key in ['maintenance_growth', 'energy_growth']:
            value = getattr(self, key)
            if not np.isfinite(value) or not -.5 <= value <= .5:
                raise ValueError(f'{key} must be in [-0.5,0.5]')
        if self.discount_rate > 1 or self.fx_factor == 0 or self.cny_per_eur == 0:
            raise ValueError('Discount rate must be <=1; FX and CNY/EUR must be positive')


def pv_factor(s, growth=0):
    """Year-1 base operating amount, then real escalation through year N."""
    return sum((1+growth)**(year-1)/(1+s.discount_rate)**year for year in range(1,s.years+1))


def fx_multiplier(s):
    """CNY quote: fewer CNY per EUR means higher EUR acquisition cost."""
    return s.fx_factor * CONFIG['reference_cny_per_eur'] / s.cny_per_eur


def tco(df, s=Scenario()):
    """Present-value components; maintenance labour and parts are disjoint."""
    validate(df)
    annuity = pv_factor(s)
    maintenance_pv = pv_factor(s, s.maintenance_growth)
    energy_pv = pv_factor(s, s.energy_growth)
    fx = 1 + df.fx_exposure * (fx_multiplier(s)-1)
    out = df[['supplier_id', 'region']].copy()
    out['purchase'] = df.purchase_eur * fx
    for field in ['transport', 'customs', 'installation', 'commissioning']:
        out[field] = df[f'{field}_eur']
    out['maintenance'] = df.maintenance_eur_year*s.maintenance_factor*maintenance_pv
    out['components'] = df.components_eur_year*s.maintenance_factor*fx*maintenance_pv
    out['energy'] = df.energy_kwh_year*s.energy_price*energy_pv
    # Downtime already contains expected operational losses: do not reapply reliability.
    out['downtime'] = df.downtime_hours_year*s.downtime_eur_hour*annuity
    out['decommission'] = df.decommission_eur/(1+s.discount_rate)**s.years
    out['tco_eur'] = out[COMPONENTS].sum(axis=1)
    out['equivalent_annual_eur'] = out.tco_eur/annuity
    return out


def weights(values, keys):
    if set(values) != set(keys):
        raise ValueError(f'Expected weights: {keys}')
    arr = np.array([values[k] for k in keys], dtype=float)
    if not np.isfinite(arr).all() or (arr < 0).any() or arr.sum() <= 0:
        raise ValueError('Weights must be finite, nonnegative and have positive sum')
    return arr/arr.sum()


def risk_pillars(df, sub_weights=None):
    """Within-pillar weighted evidence gaps; rules live in config/model.json."""
    validate(df)
    rules = CONFIG['risk_pillars'] if sub_weights is None else sub_weights
    if set(rules) != set(RISK):
        raise ValueError('All four risk pillars required')
    out = pd.DataFrame(index=df.index)
    for pillar, default_indicators in CONFIG['risk_pillars'].items():
        keys = list(default_indicators)
        w = weights(rules[pillar], keys)
        out[pillar] = df[keys].to_numpy() @ w
    return out


def risk_score(df, risk_weights=None, sub_weights=None):
    w = weights(CONFIG['risk_weights'] if risk_weights is None else risk_weights, RISK)
    return pd.Series(risk_pillars(df,sub_weights).to_numpy() @ w, index=df.index, name='residual_risk')


def cost_utility(costs):
    low, high = CONFIG['cost_anchors_eur']
    if not np.isfinite([low,high]).all() or high <= low:
        raise ValueError('Cost anchors must be finite and increasing')
    return np.clip((high-costs)/(high-low),0,1)


def rank(df, s=Scenario(), cost_weight=None, risk_weights=None, costs=None, sub_weights=None):
    """Return fixed-anchor MCDA; external cost statistics replace the cost stream."""
    cost_weight = CONFIG['priorities']['Balanced'] if cost_weight is None else cost_weight
    if not np.isfinite(cost_weight) or not 0 <= cost_weight <= 1:
        raise ValueError('Cost weight must be in [0,1]')
    out = tco(df,s)[['supplier_id','region','tco_eur']].copy()
    if costs is not None:
        c = np.asarray(costs,dtype=float)
        if c.shape != (len(df),) or not np.isfinite(c).all() or (c<0).any():
            raise ValueError('Invalid cost vector')
        out['tco_eur'] = c
    out['residual_risk'] = risk_score(df,risk_weights,sub_weights)
    out['cost_utility'] = cost_utility(out.tco_eur)
    out['risk_utility'] = 1-out.residual_risk/100
    out['eligible'] = df.mandatory_compliance.astype(bool)
    out['score'] = 100*(cost_weight*out.cost_utility+(1-cost_weight)*out.risk_utility)
    out.loc[~out.eligible,'score'] = np.nan
    out['rank'] = out.score.rank(ascending=False,method='min').astype('Int64')
    return out.sort_values(['rank','supplier_id'],na_position='last')


def sensitivity(df, s=Scenario()):
    """One factor at a time; return raw PV, equivalent annual cost and changes."""
    baseline = tco(df,s).set_index('supplier_id').tco_eur
    rows = []
    for parameter, values in CONFIG['sensitivity'].items():
        for value in sorted(set(values+[getattr(s,parameter)])):
            result = tco(df,replace(s,**{parameter:value}))
            result['parameter'],result['value'] = parameter,value
            result['delta_eur'] = result.tco_eur-result.supplier_id.map(baseline)
            rows.append(result)
    return pd.concat(rows,ignore_index=True)
