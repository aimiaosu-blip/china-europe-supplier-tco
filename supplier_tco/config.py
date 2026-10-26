"""Load the reviewable assumptions file; no hidden market calibrations."""
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / 'config/model.json'
CONFIG = json.loads(CONFIG_PATH.read_text())
