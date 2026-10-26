"""Run from repository root: python -m streamlit run app.py."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from supplier_tco.config import CONFIG
from supplier_tco.data import load, RISK
from supplier_tco.model import Scenario, tco, rank, sensitivity, risk_pillars, COMPONENTS
from supplier_tco.simulation import simulate, pairwise_probabilities, group_comparison

st.set_page_config(page_title='Supplier TCO Lab', page_icon='◈', layout='wide')
st.title('Supplier TCO Lab')
st.caption('CHINA–EUROPE · INDUSTRIAL EQUIPMENT · SYNTHETIC RESEARCH')
st.warning('100% synthetic data. These rankings are model demonstrations, not evidence about Chinese or European suppliers. No company or confidential data is used.')
df = load()
default = CONFIG['scenario']
with st.sidebar:
    st.header('Purchasing assumptions')
    years = st.slider('Equipment lifetime (years)', 1, 40, default['years'])
    discount = st.slider('Real discount rate (%)', 0, 20, round(default['discount_rate']*100))/100
    energy = st.number_input('Energy price (EUR/kWh)', .0, 1., default['energy_price'], .01)
    maintenance = st.slider('Maintenance and parts multiplier', .0, 2., default['maintenance_factor'], .05)
    fx = st.slider('FX multiplier (EUR cost of exposed spend)', .5, 1.5, default['fx_factor'], .05)
    cny = st.number_input('CNY per EUR (synthetic reference: 7.8)', 1., 20., default['cny_per_eur'], .1)
    growth = st.slider('Real annual maintenance escalation (%)', -5, 10, round(default['maintenance_growth']*100))/100
    energy_growth = st.slider('Real annual energy escalation (%)', -5, 10, round(default['energy_growth']*100))/100
    downtime = st.number_input('Lost contribution margin (EUR/hour)', 0., 20000., default['downtime_eur_hour'], 100.)
    priority = st.selectbox('Purchasing priority', ['Balanced', 'Cost-led', 'Resilience-led', 'Custom'])
    defaults = {**CONFIG['priorities'], 'Custom': CONFIG['priorities']['Balanced']}
    cost_weight = st.slider('TCO weight', 0., 1., defaults[priority], .05, key=f'weight_{priority}')
    st.caption('Remaining weight applies to residual non-monetary risk. Weights below are normalized.')
    risk_weights = {k: st.slider(k.replace('_', ' ').title(), 0, 10, CONFIG['risk_weights'][k]) for k in RISK}
    draws = st.select_slider('Monte Carlo draws', [1000, 5000, 10000], value=CONFIG['simulation']['draws'])
    if sum(risk_weights.values()) == 0:
        st.error('At least one risk dimension must have a positive weight.')
        st.stop()
s = Scenario(years, discount, energy, maintenance, fx, downtime, growth, energy_growth, cny)
base = tco(df, s)
ranking = rank(df, s, cost_weight, risk_weights)
left, middle, right = st.columns(3)
left.metric('Illustrative preferred supplier', ranking.iloc[0].supplier_id)
middle.metric('Lowest lifecycle TCO', f'€{base.tco_eur.min()/1e6:.2f}m')
right.metric('Synthetic suppliers', len(df))
tabs = st.tabs(['Comparison', 'TCO breakdown', 'Decision scorecard', 'Uncertainty', 'Sensitivity', 'Methodology'])
with tabs[0]:
    st.plotly_chart(px.scatter(ranking, x='tco_eur', y='residual_risk', color='region', hover_name='supplier_id',
                              labels={'tco_eur':'Discounted TCO (EUR)', 'residual_risk':'Residual risk (lower is better)'}), width='stretch')
    st.dataframe(df, hide_index=True)
    st.download_button('Download synthetic dataset', df.to_csv(index=False), 'synthetic_suppliers.csv')
with tabs[1]:
    parts = COMPONENTS
    st.plotly_chart(px.bar(base.melt(id_vars='supplier_id', value_vars=parts, var_name='component', value_name='EUR'),
                          x='supplier_id', y='EUR', color='component'), width='stretch')
    chosen = st.selectbox('Cost waterfall supplier', df.supplier_id)
    values = base.set_index('supplier_id').loc[chosen, parts].astype(float)
    fig = go.Figure(go.Waterfall(x=parts+['Total'], y=values.tolist()+[0], measure=['relative']*len(parts)+['total']))
    fig.update_layout(yaxis_title='Discounted EUR', title=f'{chosen}: lifecycle cost build-up')
    st.plotly_chart(fig, width='stretch')
    st.dataframe(base, hide_index=True)
with tabs[2]:
    st.dataframe(ranking[['rank','supplier_id','region','tco_eur','residual_risk','score','eligible']], hide_index=True)
    st.plotly_chart(px.imshow(risk_pillars(df).set_axis(df.supplier_id), zmin=0, zmax=100,
                              color_continuous_scale='YlOrRd', aspect='auto', labels={'color':'Residual risk'}), width='stretch')
    st.caption('Sub-indicator weights and scoring assumptions are editable in config/model.json; restart after edits.')
    st.caption('All demo suppliers pass the synthetic mandatory-compliance gate. A failed gate excludes a supplier regardless of price. Scores do not certify actual compliance.')
    st.download_button('Download scorecard', ranking.to_csv(index=False), 'scorecard.csv')
with tabs[3]:
    @st.cache_data
    def run_sim(scenario, count, cw, rw):
        return simulate(load(), scenario, count, cost_weight=cw, risk_weights=rw)
    summary, samples = run_sim(s, draws, cost_weight, risk_weights)
    selected = st.selectbox('Supplier distribution', df.supplier_id)
    st.plotly_chart(px.histogram(samples[samples.supplier_id == selected], x='tco_eur', nbins=60,
                                histnorm='probability density'), width='stretch')
    st.plotly_chart(px.bar(summary, x='supplier_id', y='probability_best'), width='stretch')
    st.dataframe(summary, hide_index=True)
    pairs = pairwise_probabilities(samples)
    compared = st.selectbox('Compare selected supplier against', df.loc[df.supplier_id != selected, 'supplier_id'])
    pair = pairs[(pairs.supplier_a == selected) & (pairs.supplier_b == compared)].iloc[0]
    st.metric(f'P({selected} scores higher than {compared})', f'{pair.probability_a_better:.1%}')
    st.caption(f'Paired draw comparison; ties: {pair.probability_tie:.1%}. Conditional on this synthetic model.')
    st.write('Group-mean utility comparison (current priority):', group_comparison(samples))
    st.caption('Group means compare only this artificial shortlist, not real country populations. They differ from the probability that any group member ranks first.')
    st.plotly_chart(px.histogram(samples[samples.supplier_id == selected], x='residual_risk', nbins=50), width='stretch')
    st.caption('p025–p975: 95% simulated cost interval. mean_ci: approximate 95% Monte Carlo confidence interval for the model mean, not real-world uncertainty. CVaR95: average cost in the worst 5% of draws; never added on top of expected TCO.')
    tail = rank(df, s, cost_weight, risk_weights, costs=summary.set_index('supplier_id').loc[df.supplier_id, 'cvar95'].to_numpy())
    st.subheader('Tail-cost alternative')
    st.dataframe(tail[['rank', 'supplier_id', 'tco_eur', 'score']], hide_index=True)
    st.caption('This alternative replaces expected TCO with CVaR95; it does not add a second loss charge. Probability-best above uses joint draw-level MCDA.')
with tabs[4]:
    sens = sensitivity(df, s)
    param = st.selectbox('Sensitivity driver', sens.parameter.unique())
    st.plotly_chart(px.line(sens[sens.parameter == param], x='value', y='tco_eur', color='supplier_id', markers=True), width='stretch')
    tornado_supplier = st.selectbox('Tornado supplier', df.supplier_id)
    tornado = sens[sens.supplier_id == tornado_supplier].groupby('parameter').delta_eur.agg(['min','max'])
    tornado['span'] = tornado['max']-tornado['min']
    tornado = tornado.sort_values('span')
    fig = go.Figure()
    fig.add_trace(go.Bar(y=tornado.index, x=tornado['min'], name='Minimum change', orientation='h'))
    fig.add_trace(go.Bar(y=tornado.index, x=tornado['max'], name='Maximum change', orientation='h'))
    fig.update_layout(barmode='relative', xaxis_title='Change from active baseline (EUR)', title='One-factor sensitivity envelope')
    st.plotly_chart(fig, width='stretch')
    st.caption('One factor changes at a time. For different lifetimes, equivalent annual cost complements total present cost; longer service is not identical output.')
    st.dataframe(sens[sens.parameter == param][['supplier_id','value','tco_eur','equivalent_annual_eur','delta_eur']], hide_index=True)
    st.download_button('Download all sensitivity results', sens.to_csv(index=False), 'sensitivity.csv')
with tabs[5]:
    st.markdown('''**Scope:** one functionally equivalent paint-shop equipment package installed at a hypothetical European plant; equal throughput and finish specification, 4,000 planned hours/year.

**Discounting:** upfront costs at year 0; year-end operating costs with configurable real escalation; decommissioning at final year. Base case: 15 years, 6% real discount rate, EUR 0.15/kWh.

**No double counting:** expected downtime is charged once using lost contribution margin. Reliability is a diagnostic only. Risk scores measure residual governance/evidence gaps; they do not reuse downtime, energy or maintenance costs. Mandatory compliance is a gate.

**Limits:** hypothetical quotes, risk scores and uncertainty distributions; no field calibration, certification, taxes, financing, demand growth, salvage or full emissions LCA. See docs/methodology.md for evidence requirements before real procurement use.''')
