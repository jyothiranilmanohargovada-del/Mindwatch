"""Evaluate the rule-based crisis detector on data/crisis_test.csv."""
import pandas as pd
from sklearn.metrics import precision_score, recall_score
from config import CRISIS_TEST_PATH
from src.risk import has_crisis_language


def evaluate_crisis(path=CRISIS_TEST_PATH) -> dict:
    d = pd.read_csv(path)
    pred = d.text.map(has_crisis_language).astype(int)
    return {"n": int(len(d)), "precision": float(precision_score(d.label, pred)),
            "recall": float(recall_score(d.label, pred)),
            "errors": d[pred != d.label].text.tolist()}


if __name__ == "__main__":
    print(evaluate_crisis())
