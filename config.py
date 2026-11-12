"""Central configuration for MindWatch."""
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "posts_dataset.csv"
CRISIS_TEST_PATH = BASE_DIR / "data" / "crisis_test.csv"
RESOURCES_PATH = BASE_DIR / "data" / "resources.json"
MODEL_PATH = BASE_DIR / "models" / "depression_model.joblib"
THRESHOLDS_PATH = BASE_DIR / "models" / "thresholds.json"
METRICS_PATH = BASE_DIR / "reports" / "metrics.json"
EVAL_MD_PATH = BASE_DIR / "reports" / "EVALUATION.md"
FIG_DIR = BASE_DIR / "reports" / "figures"
DB_PATH = Path(os.environ.get("MINDWATCH_DB", BASE_DIR / "app" / "mindwatch.db"))

# Defaults; replaced by values tuned on out-of-fold predictions when models/thresholds.json exists
DEFAULT_THRESH_MODERATE = 0.40
DEFAULT_THRESH_HIGH = 0.65

# Privacy: raw text is NOT stored unless this is explicitly switched on.
STORE_RAW_TEXT = os.environ.get("MINDWATCH_STORE_TEXT", "0") == "1"
MAX_TEXT_CHARS = 5000
RANDOM_STATE = 42


def thresholds():
    """Return (moderate, high) risk thresholds, tuned if available."""
    try:
        t = json.loads(THRESHOLDS_PATH.read_text())
        return float(t["moderate"]), float(t["high"])
    except (OSError, KeyError, ValueError):
        return DEFAULT_THRESH_MODERATE, DEFAULT_THRESH_HIGH
