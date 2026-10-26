"""Reproducible, region-neutral synthetic paint-shop supplier design."""
from pathlib import Path
import numpy as np
import pandas as pd
from .config import CONFIG

RISK = list(CONFIG['risk_pillars'])
SUBINDICATORS = [key for pillar in CONFIG['risk_pillars'].values() for key in pillar]
FRACTIONS = ['reliability', 'fx_exposure', 'quality_rework_probability', 'disruption_probability']
NUMERIC = list(CONFIG['generator']['ranges'])
POSITIVE = [key for key in NUMERIC if key not in FRACTIONS]


def generate(seed=None):
    """Draw from identical bounded uniform assumptions in both regions."""
    settings = CONFIG['generator']
    rng = np.random.default_rng(settings['seed'] if seed is None else seed)
    count = settings['suppliers_per_region']
    rows = []
    for i in range(count * 2):
        row = dict(supplier_id=f'SYN-{i+1:02d}', region='China' if i < count else 'Europe',
                   synthetic=True, mandatory_compliance=True)
        for field, bounds in settings['ranges'].items():
            decimals = 4 if field in FRACTIONS else 2
            row[field] = round(rng.uniform(*bounds), decimals)
        for field in SUBINDICATORS:
            row[field] = round(rng.uniform(*settings['risk_bounds']), 2)
        rows.append(row)
    return pd.DataFrame(rows)


def validate(df):
    """Reject malformed identifiers, provenance, gates and numeric inputs."""
    required = ['supplier_id', 'region', 'synthetic', 'mandatory_compliance'] + NUMERIC + SUBINDICATORS
    if not set(required).issubset(df.columns) or df.empty:
        raise ValueError('Missing columns or empty supplier dataset')
    if df.supplier_id.duplicated().any() or df[required].isna().any().any():
        raise ValueError('Duplicate IDs or missing values')
    if not df.region.isin(['China', 'Europe']).all() or not df.synthetic.eq(True).all():
        raise ValueError('Only labelled synthetic China/Europe data supported')
    if not df.mandatory_compliance.isin([True, False]).all():
        raise ValueError('Compliance gate must be boolean')
    for cols, lo, hi in [(POSITIVE, 0, np.inf), (SUBINDICATORS, 0, 100), (FRACTIONS, 0, 1)]:
        a = df[cols].to_numpy(dtype=float)
        if not np.isfinite(a).all() or (a < lo).any() or (a > hi).any():
            raise ValueError('Invalid numeric supplier inputs')
    return df


def load(path=None):
    path = path or Path(__file__).resolve().parents[1] / 'data/suppliers.csv'
    return validate(pd.read_csv(path))


def main():
    path = Path(__file__).resolve().parents[1] / 'data/suppliers.csv'
    generate().to_csv(path, index=False)


if __name__ == '__main__':
    main()
