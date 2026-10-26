from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_dashboard_default_and_scenarios():
    at = AppTest.from_file(Path(__file__).resolve().parents[1] / 'app.py', default_timeout=30).run()
    assert not at.exception
    assert at.metric[2].value == '12'
    at.sidebar.selectbox[0].select('Resilience-led').run()
    assert not at.exception
    at.sidebar.slider[0].set_value(20).run()
    assert not at.exception
    # Zero risk weights should display a clear validation error rather than crash.
    for control in at.sidebar.slider:
        if control.label in ['Quality Governance','Compliance Sustainability','Service Governance','Supply Continuity']:
            control.set_value(0)
    at.run()
    assert not at.exception
    assert at.error
