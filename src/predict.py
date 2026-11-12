"""Inference: probability, risk level, crisis flag, themes and term-level explanation."""
import joblib
import numpy as np
from config import MODEL_PATH
from src.features import extract_emotional_signals
from src.lang import is_supported
from src.risk import crisis_assessment, detect_themes, grade

_model = None


def load_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def explain(text: str, top_k: int = 5):
    """Terms that pushed the score up (deployed model is linear, so this is exact)."""
    m = load_model()
    cleaned = m.named_steps["clean"].transform([text])
    X = m.named_steps["features"].transform(cleaned)
    contrib = np.asarray(X.multiply(m.named_steps["clf"].coef_[0]).todense()).ravel()
    names = m.named_steps["features"].get_feature_names_out()
    idx = np.argsort(contrib)[::-1][:top_k]
    return [names[i].split("__")[-1].replace("_", " ") for i in idx if contrib[i] > 0]


def explain_detailed(text: str, top_k: int = 6):
    """Detailed feature contribution breakdown with interpretable rationale."""
    m = load_model()
    cleaned = m.named_steps["clean"].transform([text])
    X = m.named_steps["features"].transform(cleaned)
    contrib = np.asarray(X.multiply(m.named_steps["clf"].coef_[0]).todense()).ravel()
    names = m.named_steps["features"].get_feature_names_out()

    # Positive contributors (elevating distress score)
    pos_idx = [i for i in np.argsort(contrib)[::-1] if contrib[i] > 0.01][:top_k]
    # Negative contributors (protective / mitigating score)
    neg_idx = [i for i in np.argsort(contrib) if contrib[i] < -0.01][:top_k]

    def _clean_name(raw):
        clean = raw.split("__")[-1].replace("_", " ")
        if clean.startswith("tfidf "):
            clean = clean[6:]
        return clean

    elevating = [{"term": _clean_name(names[i]), "weight": round(float(contrib[i]), 3), "direction": "elevating"}
                 for i in pos_idx]
    mitigating = [{"term": _clean_name(names[i]), "weight": round(float(contrib[i]), 3), "direction": "mitigating"}
                  for i in neg_idx]

    # Synthesize plain-language summary of why terms influenced the result
    reasons = []
    if elevating:
        top_terms = [f"'{item['term']}'" for item in elevating[:3]]
        reasons.append(f"Phrases such as {', '.join(top_terms)} contributed positively toward the distress language marker.")
    if mitigating:
        top_mit = [f"'{item['term']}'" for item in mitigating[:3]]
        reasons.append(f"In contrast, words such as {', '.join(top_mit)} acted as buffering or positive language cues.")
    if not reasons:
        reasons.append("Text language is predominantly balanced without strong distress-specific linguistic markers.")

    return {
        "elevating_terms": elevating,
        "mitigating_terms": mitigating,
        "summary": " ".join(reasons)
    }


def compare_with_previous(current_prob, current_level, prev):
    """Compare current post analysis with the user's previous entry."""
    if not prev or not isinstance(prev, dict):
        return None
    prev_prob = prev.get("probability")
    prev_level = prev.get("level")
    if prev_prob is None or current_prob is None:
        return {"previous_level": prev_level, "delta": None, "note": f"Previous submission was rated {prev_level}."}

    delta = round(current_prob - prev_prob, 3)
    if delta > 0.10:
        summary = f"Distress marker score increased by {int(abs(delta)*100)}% compared to your previous entry."
        trend = "increased"
    elif delta < -0.10:
        summary = f"Distress marker score decreased by {int(abs(delta)*100)}% compared to your previous entry."
        trend = "decreased"
    else:
        summary = "Distress markers are broadly comparable with your previous entry."
        trend = "stable"

    return {
        "previous_level": prev_level,
        "previous_probability": prev_prob,
        "delta": delta,
        "trend": trend,
        "summary": summary
    }


def analyze_post(text: str, previous_analysis: dict = None) -> dict:
    ca = crisis_assessment(text)
    signals = extract_emotional_signals(text)

    if not is_supported(text):
        # never report "low risk" for text the model cannot read
        return {
            "probability": None,
            "level": "CRISIS" if ca["crisis"] else "UNSUPPORTED",
            "crisis": ca["crisis"],
            "themes": [],
            "key_terms": [],
            "signals": signals,
            "explanation": {"elevating_terms": [], "mitigating_terms": [], "summary": "Language not supported for Latin-script text analysis."},
            "comparison": None,
            "note": "This model reads English (Latin-script) text only.",
            "limitations": "Screening aid only. Text pattern analysis reflects momentary expression and does not constitute a clinical diagnosis.",
            "clinical_distinction": "Linguistic markers assess written vocabulary, not clinical depression status."
        }

    prob = float(load_model().predict_proba([text])[0, 1])
    lvl = grade(prob, ca["crisis"])
    themes = detect_themes(text)
    key_terms = explain(text)
    detailed_exp = explain_detailed(text)
    comparison = compare_with_previous(prob, lvl, previous_analysis)

    return {
        "probability": round(prob, 4),
        "level": lvl,
        "crisis": ca["crisis"],
        "themes": themes,
        "key_terms": key_terms,
        "signals": signals,
        "explanation": detailed_exp,
        "comparison": comparison,
        "note": None,
        "limitations": "Screening aid only. Social media text reflects momentary thoughts and does NOT constitute a medical or clinical diagnosis.",
        "clinical_distinction": "Model score measures statistical alignment with known distress language markers, NOT a clinical probability of clinical depression."
    }

