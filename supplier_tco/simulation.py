"""Joint simulation with paired comparisons and explicitly conditional probabilities."""
import numpy as np
import pandas as pd
from .data import validate, RISK, SUBINDICATORS
from .model import Scenario, weights, pv_factor, fx_multiplier, cost_utility
from .config import CONFIG


def simulate(df, s=Scenario(), draws=None, seed=None, cost_weight=None, risk_weights=None, sub_weights=None):
    """Simulate long-run cost levels and residual evidence uncertainty, not country effects."""
    validate(df)
    assumptions = CONFIG['simulation']
    draws = assumptions['draws'] if draws is None else draws
    seed = assumptions['seed'] if seed is None else seed
    cost_weight = CONFIG['priorities']['Balanced'] if cost_weight is None else cost_weight
    if isinstance(draws,bool) or not isinstance(draws,int) or draws < 100:
        raise ValueError('At least 100 integer draws required')
    if not np.isfinite(cost_weight) or not 0 <= cost_weight <= 1:
        raise ValueError('Invalid cost weight')
    rng = np.random.default_rng(seed)
    n = len(df)

    def lognormal(cv, shape):
        if not np.isfinite(cv) or cv < 0:
            raise ValueError('Coefficient of variation must be finite and nonnegative')
        sigma = np.sqrt(np.log1p(cv**2))
        return rng.lognormal(-sigma**2/2,sigma,shape)

    energy = lognormal(assumptions['energy_cv'],(draws,1))
    fx = lognormal(assumptions['fx_cv'],(draws,1))*fx_multiplier(s)
    maintenance = lognormal(assumptions['maintenance_cv'],(draws,n))*s.maintenance_factor
    fx_effect = 1+df.fx_exposure.to_numpy()*(fx-1)
    downtime = lognormal(assumptions['downtime_cv'],(draws,n))*df.downtime_hours_year.to_numpy()
    upfront = df[['transport_eur','customs_eur','installation_eur','commissioning_eur']].sum(axis=1).to_numpy()
    costs = df.purchase_eur.to_numpy()*fx_effect+upfront
    costs += pv_factor(s,s.maintenance_growth)*maintenance*(df.maintenance_eur_year.to_numpy()+df.components_eur_year.to_numpy()*fx_effect)
    costs += pv_factor(s,s.energy_growth)*energy*s.energy_price*df.energy_kwh_year.to_numpy()
    costs += pv_factor(s)*downtime*s.downtime_eur_hour
    costs += df.decommission_eur.to_numpy()/(1+s.discount_rate)**s.years

    concentration = assumptions['risk_concentration']
    if not np.isfinite(concentration) or concentration <= 0:
        raise ValueError('Risk concentration must be positive')
    mean = np.clip(df[SUBINDICATORS].to_numpy()/100,.001,.999)
    uncertain = rng.beta(mean*concentration,(1-mean)*concentration,size=(draws,n,len(SUBINDICATORS)))*100
    rules = CONFIG['risk_pillars'] if sub_weights is None else sub_weights
    if set(rules) != set(RISK):
        raise ValueError('All four risk pillars required')
    pillar_draws = []
    for pillar, defaults in CONFIG['risk_pillars'].items():
        keys = list(defaults)
        w = weights(rules[pillar],keys)
        indexes = [SUBINDICATORS.index(key) for key in keys]
        pillar_draws.append(uncertain[:,:,indexes] @ w)
    w = weights(CONFIG['risk_weights'] if risk_weights is None else risk_weights,RISK)
    risk = np.stack(pillar_draws,axis=2) @ w
    utility = 100*(cost_weight*cost_utility(costs)+(1-cost_weight)*(1-risk/100))
    eligible = df.mandatory_compliance.to_numpy(dtype=bool)
    utility[:,~eligible] = -np.inf
    best = utility == utility.max(axis=1,keepdims=True)
    wins = best/best.sum(axis=1,keepdims=True) if eligible.any() else np.zeros_like(utility)
    mean_cost = costs.mean(axis=0)
    se = costs.std(axis=0,ddof=1)/np.sqrt(draws)
    p95 = np.quantile(costs,.95,axis=0)
    cvar = np.array([costs[costs[:,j]>=p95[j],j].mean() for j in range(n)])
    summary = pd.DataFrame({'supplier_id':df.supplier_id.to_numpy(),'region':df.region.to_numpy(),
        'mean_tco':mean_cost,'mean_ci_low':mean_cost-1.96*se,'mean_ci_high':mean_cost+1.96*se,
        'p025':np.quantile(costs,.025,axis=0),'p50':np.median(costs,axis=0),'p975':np.quantile(costs,.975,axis=0),
        'p95':p95,'cvar95':cvar,'mean_residual_risk':risk.mean(axis=0),
        'risk_p025':np.quantile(risk,.025,axis=0),'risk_p975':np.quantile(risk,.975,axis=0),
        'probability_best':wins.mean(axis=0)})
    samples = pd.DataFrame({'draw':np.repeat(np.arange(draws),n),'supplier_id':np.tile(df.supplier_id,draws),
        'region':np.tile(df.region,draws),'eligible':np.tile(eligible,draws),'tco_eur':costs.ravel(),
        'residual_risk':risk.ravel(),'mcda_score':np.where(np.isfinite(utility),utility,np.nan).ravel()})
    return summary,samples


def pairwise_probabilities(samples):
    """Paired P(score A > score B); report ties separately, only eligible options."""
    matrix = samples.loc[samples.eligible].pivot(index='draw',columns='supplier_id',values='mcda_score')
    rows = []
    for a in matrix.columns:
        for b in matrix.columns:
            if a == b:
                continue
            delta = matrix[a]-matrix[b]
            p = float((delta>0).mean())
            se = np.sqrt(p*(1-p)/len(delta))
            rows.append({'supplier_a':a,'supplier_b':b,'probability_a_better':p,
                         'probability_tie':float((delta==0).mean()),'mc_standard_error':se})
    return pd.DataFrame(rows,columns=['supplier_a','supplier_b','probability_a_better','probability_tie','mc_standard_error'])


def group_comparison(samples):
    """Compare shortlist group-mean utility per joint draw, not population quality."""
    eligible = samples.loc[samples.eligible]
    matrix = eligible.groupby(['draw','region']).mcda_score.mean().unstack()
    if not {'China','Europe'}.issubset(matrix.columns):
        return {'probability_china_mean_better':None,'probability_europe_mean_better':None,'probability_tie':None}
    delta = matrix['China']-matrix['Europe']
    return {'probability_china_mean_better':float((delta>0).mean()),
            'probability_europe_mean_better':float((delta<0).mean()),'probability_tie':float((delta==0).mean())}
