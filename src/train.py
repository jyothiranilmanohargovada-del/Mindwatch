"""Train, compare, tune and persist the depression-indicative-language classifier.

  python -m src.train                                   # uses data/posts_dataset.csv (synthetic)
  python -m src.train --data my.csv --text-col body --label-col is_depressed [--split-col split]

If the CSV has a split column with 'train' plus one or more other values, every non-train
split is used as a separate test set; otherwise a stratified 80/20 split is made.
"""
import argparse
import json
import warnings

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix, f1_score,
                             precision_recall_curve, precision_score, recall_score, roc_auc_score,
                             roc_curve)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score, train_test_split

from config import (DATA_PATH, EVAL_MD_PATH, FIG_DIR, METRICS_PATH, MODEL_PATH, RANDOM_STATE,
                    THRESHOLDS_PATH)
from src.crisis_eval import evaluate_crisis
from src.model import build_pipeline, candidate_models

warnings.filterwarnings("ignore")
DEPLOYED = "Logistic Regression"   # interpretable + calibrated-ish probabilities in a sensitive domain


def metrics_at(y, prob, thr=0.5):
    pred = (prob >= thr).astype(int)
    return {"accuracy": accuracy_score(y, pred), "precision": precision_score(y, pred, zero_division=0),
            "recall": recall_score(y, pred), "f1": f1_score(y, pred),
            "roc_auc": roc_auc_score(y, prob), "pr_auc": average_precision_score(y, prob)}


def tune_thresholds(y, oof):
    """MODERATE = max F2 (recall-weighted) on out-of-fold probs; HIGH = lowest thr with precision >= 0.90."""
    p, r, t = precision_recall_curve(y, oof)
    f2 = 5 * p[:-1] * r[:-1] / np.maximum(4 * p[:-1] + r[:-1], 1e-9)
    moderate = float(np.clip(t[int(np.argmax(f2))], 0.20, 0.50))
    ok = np.where(p[:-1] >= 0.90)[0]
    high = float(t[ok[0]]) if len(ok) else 0.65
    high = float(np.clip(high, 0.55, 0.90))
    if high < moderate + 0.10:
        high = moderate + 0.10
    return round(moderate, 3), round(high, 3)


def load(args):
    df = pd.read_csv(args.data).rename(columns={args.text_col: "text", args.label_col: "label"})
    df = df.dropna(subset=["text", "label"])
    df["label"] = df["label"].astype(int)
    if args.split_col in df.columns and (df[args.split_col] == "train").any():
        train = df[df[args.split_col] == "train"]
        tests = {n: g for n, g in df[df[args.split_col] != "train"].groupby(args.split_col)}
    else:
        train, test = train_test_split(df, test_size=0.2, stratify=df.label, random_state=RANDOM_STATE)
        tests = {"test": test}
    return train, tests


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DATA_PATH))
    ap.add_argument("--text-col", default="text")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--split-col", default="split")
    args = ap.parse_args()

    train, tests = load(args)
    Xtr, ytr = train.text, train.label
    print(f"train={len(train)}  tests={ {k: len(v) for k, v in tests.items()} }")
    cv = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)

    results, probs, fitted = {}, {}, {}
    for name, clf in candidate_models().items():
        pipe = build_pipeline(clf, use_lexicon=(name != "Multinomial NB"))   # NB needs non-negative input
        cvf1 = cross_val_score(pipe, Xtr, ytr, cv=cv, scoring="f1")
        pipe.fit(Xtr, ytr)
        res = {"cv_f1_mean": float(cvf1.mean()), "cv_f1_std": float(cvf1.std())}
        for tname, tdf in tests.items():
            p = pipe.predict_proba(tdf.text)[:, 1]
            res[tname] = metrics_at(tdf.label, p)
            probs[(name, tname)] = p
        results[name], fitted[name] = res, pipe
        print(f"{name:26s} CV-F1={cvf1.mean():.3f}  " +
              "  ".join(f"{t}: F1={res[t]['f1']:.3f} AUC={res[t]['roc_auc']:.3f}" for t in tests))

    deployed = fitted[DEPLOYED]
    # Ablation: TF-IDF only
    abl = build_pipeline(candidate_models()[DEPLOYED], use_lexicon=False).fit(Xtr, ytr)
    ablation = {t: metrics_at(d.label, abl.predict_proba(d.text)[:, 1]) for t, d in tests.items()}

    # Threshold tuning on out-of-fold training predictions (no test leakage)
    oof = cross_val_predict(build_pipeline(candidate_models()[DEPLOYED]), Xtr, ytr, cv=cv, method="predict_proba")[:, 1]
    moderate, high = tune_thresholds(ytr, oof)
    THRESHOLDS_PATH.write_text(json.dumps({"moderate": moderate, "high": high}, indent=2))
    print(f"Tuned thresholds: moderate={moderate} high={high}")
    operating = {t: metrics_at(d.label, probs[(DEPLOYED, t)], moderate) for t, d in tests.items()}

    joblib.dump(deployed, MODEL_PATH)
    crisis = evaluate_crisis()
    print("Crisis detector:", {k: round(v, 3) if isinstance(v, float) else v for k, v in crisis.items()})

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    names_t = list(tests)
    primary = "iid_test" if "iid_test" in tests else names_t[0]

    fig, axes = plt.subplots(1, len(names_t), figsize=(3.8 * len(names_t), 3.5))
    for ax, tname in zip(np.atleast_1d(axes), names_t):
        y = tests[tname].label
        pred = (probs[(DEPLOYED, tname)] >= 0.5).astype(int)
        cm = confusion_matrix(y, pred)
        ax.imshow(cm, cmap="Blues")
        for (i, j), v in np.ndenumerate(cm):
            ax.text(j, i, v, ha="center", va="center", color="white" if v > cm.max() / 2 else "black", fontsize=13)
        ax.set_xticks([0, 1], ["Non-dep.", "Dep."]); ax.set_yticks([0, 1], ["Non-dep.", "Dep."])
        ax.set_title(f"{tname}", fontsize=10); ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    fig.tight_layout(); fig.savefig(FIG_DIR / "confusion_matrix.png", dpi=200); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    for tname in names_t:
        y, p = tests[tname].label, probs[(DEPLOYED, tname)]
        fpr, tpr, _ = roc_curve(y, p); axes[0].plot(fpr, tpr, label=f"{tname} (AUC {roc_auc_score(y, p):.3f})")
        pr, rc, _ = precision_recall_curve(y, p); axes[1].plot(rc, pr, label=tname)
        fo, mp = calibration_curve(y, p, n_bins=8); axes[2].plot(mp, fo, "o-", label=tname)
    axes[0].plot([0, 1], [0, 1], "k--", lw=.8); axes[0].set_title("ROC"); axes[0].legend(fontsize=7)
    axes[1].set_title("Precision-Recall"); axes[1].set_xlabel("Recall"); axes[1].set_ylabel("Precision"); axes[1].legend(fontsize=7)
    axes[2].plot([0, 1], [0, 1], "k--", lw=.8); axes[2].set_title("Calibration"); axes[2].set_xlabel("Predicted"); axes[2].set_ylabel("Observed")
    fig.tight_layout(); fig.savefig(FIG_DIR / "roc_pr_calibration.png", dpi=200); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 3.6)); w = 0.8 / len(names_t); mn = list(results)
    for k, tname in enumerate(names_t):
        ax.bar(np.arange(len(mn)) + k * w, [results[n][tname]["f1"] for n in mn], w, label=f"F1 on {tname}")
    ax.set_xticks(np.arange(len(mn)) + w * (len(names_t) - 1) / 2, [n.replace(" (calibrated)", "") for n in mn], fontsize=8)
    ax.set_ylim(0.5, 1.0); ax.legend(fontsize=8); ax.set_title("Model comparison")
    fig.tight_layout(); fig.savefig(FIG_DIR / "model_comparison.png", dpi=200); plt.close(fig)

    feats = deployed.named_steps["features"].get_feature_names_out()
    coef = deployed.named_steps["clf"].coef_[0]; order = np.argsort(coef)
    top_dep = [(feats[i].split("__")[-1], float(coef[i])) for i in order[::-1][:12]]
    top_non = [(feats[i].split("__")[-1], float(coef[i])) for i in order[:12]]
    fig, ax = plt.subplots(figsize=(6, 4.2))
    labels = [t for t, _ in top_non[::-1]] + [t for t, _ in top_dep[::-1]]
    vals = [v for _, v in top_non[::-1]] + [v for _, v in top_dep[::-1]]
    ax.barh(labels, vals, color=["#4c9f70" if v < 0 else "#c0504d" for v in vals])
    ax.set_title("Most influential features (Logistic Regression)"); ax.tick_params(labelsize=7)
    fig.tight_layout(); fig.savefig(FIG_DIR / "top_features.png", dpi=200); plt.close(fig)

    out = {"n_train": int(len(train)), "tests": {k: int(len(v)) for k, v in tests.items()},
           "deployed_model": DEPLOYED, "models": results, "ablation_tfidf_only": ablation,
           "thresholds": {"moderate": moderate, "high": high}, "at_moderate_threshold": operating,
           "crisis_detector": crisis, "top_depressive_terms": top_dep, "top_non_depressive_terms": top_non,
           "data_source": str(args.data),
           "data_note": "Default dataset is SYNTHETIC. Metrics are not real-world performance."}
    METRICS_PATH.write_text(json.dumps(out, indent=2))

    md = ["# Evaluation (auto-generated by `python -m src.train`)", "",
          f"> Data: `{args.data}`. The bundled dataset is **synthetic**; treat all numbers as pipeline checks, not real-world accuracy.", "",
          "| Model | Test set | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |", "|---|---|---|---|---|---|---|---|"]
    for n, r in results.items():
        for t in names_t:
            m = r[t]
            md.append(f"| {n}{' (deployed)' if n == DEPLOYED else ''} | {t} | {m['accuracy']:.3f} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {m['roc_auc']:.3f} | {m['pr_auc']:.3f} |")
    md += ["", f"Tuned thresholds (out-of-fold, training data only): MODERATE >= {moderate}, HIGH >= {high}.", "",
           "Deployed model at the MODERATE (screening) threshold:", "", "| Test set | Precision | Recall | F1 |", "|---|---|---|---|"]
    md += [f"| {t} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} |" for t, m in operating.items()]
    md += ["", "Ablation (TF-IDF only, no linguistic features), F1: " + ", ".join(f"{t} {m['f1']:.3f}" for t, m in ablation.items()), "",
           f"Crisis-phrase detector on `data/crisis_test.csv` ({crisis['n']} author-written examples; the rules were developed against this same set, so it is optimistic): "
           f"precision {crisis['precision']:.2f}, recall {crisis['recall']:.2f}."]
    EVAL_MD_PATH.write_text("\n".join(md) + "\n")
    print("Saved model, thresholds, metrics, figures, EVALUATION.md")


if __name__ == "__main__":
    main()
