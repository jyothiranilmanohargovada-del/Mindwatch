"""Hand-crafted linguistic features used alongside TF-IDF.

Motivation from the literature: depressive language shows more first-person
singular pronouns (Rude et al., 2004), more absolutist words (Al-Mosaiwi &
Johnstone, 2018) and a higher share of negative-emotion words.
"""
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from src.preprocess import tokenize

FIRST_PERSON = {"i", "me", "my", "mine", "myself", "am"}
ABSOLUTIST = {"always", "never", "nothing", "everything", "completely", "totally",
              "entire", "forever", "nobody", "everyone", "all", "every", "constantly"}
NEGATIVE = {"sad", "empty", "hopeless", "worthless", "tired", "alone", "lonely", "hate",
            "cry", "numb", "guilty", "failure", "useless", "burden", "exhausted",
            "hurt", "pain", "dead", "disappear", "trapped", "heavy", "grey", "low",
            "depressed", "anxious", "upset", "ashamed", "afraid"}
POSITIVE = {"happy", "great", "good", "love", "excited", "fun", "amazing", "grateful",
            "calm", "lovely", "motivated", "enjoy", "wonderful", "best", "proud"}

FEATURE_NAMES = ["first_person_ratio", "absolutist_ratio", "negative_ratio",
                 "positive_ratio", "log_length", "neg_minus_pos"]


class LexiconFeatures(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = []
        for text in X:
            toks = tokenize(text)
            n = max(len(toks), 1)
            fp = sum(t in FIRST_PERSON for t in toks) / n
            ab = sum(t in ABSOLUTIST for t in toks) / n
            ng = sum(t in NEGATIVE for t in toks) / n
            ps = sum(t in POSITIVE for t in toks) / n
            rows.append([fp, ab, ng, ps, np.log1p(len(toks)), ng - ps])
        return np.array(rows)

    def get_feature_names_out(self, input_features=None):
        return np.array(FEATURE_NAMES)


EXTENDED_NEGATIVE = NEGATIVE | {
    "dread", "miserable", "overwhelmed", "crying", "scared", "terrified",
    "stress", "stressed", "stressful", "panic", "unbearable", "bleak",
    "paralyzed", "isolated", "broken", "suffering", "hurting", "failing",
    "helpless", "defeated", "ruined", "worthless", "anxious", "alone", "lonely"
}

EXTENDED_POSITIVE = POSITIVE | {
    "relieved", "hopeful", "peaceful", "cheerful", "enjoyed", "glad",
    "supported", "refreshed", "content", "accomplished", "bright", "optimistic",
    "recharged", "relaxed", "loved", "friendly", "energized"
}


def extract_emotional_signals(text: str) -> dict:
    """Extract fine-grained emotional and linguistic signals for MindWatch 2.0."""
    toks = tokenize(text)
    n = max(len(toks), 1)

    found_pos = [t for t in toks if t in EXTENDED_POSITIVE]
    found_neg = [t for t in toks if t in EXTENDED_NEGATIVE]
    found_ab = [t for t in toks if t in ABSOLUTIST]
    found_fp = [t for t in toks if t in FIRST_PERSON]

    pos_ratio = len(found_pos) / n
    neg_ratio = len(found_neg) / n
    ab_ratio = len(found_ab) / n
    fp_ratio = len(found_fp) / n

    # Neutral ratio represents descriptive/factual words not carrying heavy affective valence
    neu_ratio = max(0.0, 1.0 - (pos_ratio + neg_ratio))

    # Emotional intensity: higher when affective words or intensifiers are dense
    intensity = min(1.0, (len(found_pos) + len(found_neg) * 1.3 + len(found_ab) * 0.8) / (n * 0.4 or 1))

    if neg_ratio > 0.08 and neg_ratio > pos_ratio * 1.5:
        dominant_tone = "predominantly_negative"
        tone_label = "Elevated Distress & Heavy Emotion"
    elif pos_ratio > 0.08 and pos_ratio > neg_ratio * 1.5:
        dominant_tone = "predominantly_positive"
        tone_label = "Positive & Uplifting Signals"
    elif (pos_ratio + neg_ratio) > 0.06:
        dominant_tone = "mixed"
        tone_label = "Mixed / Ambivalent Signals"
    else:
        dominant_tone = "neutral_balanced"
        tone_label = "Primarily Factual / Balanced"

    return {
        "positive_ratio": round(pos_ratio, 3),
        "negative_ratio": round(neg_ratio, 3),
        "neutral_ratio": round(neu_ratio, 3),
        "absolutist_index": round(ab_ratio, 3),
        "self_focus_index": round(fp_ratio, 3),
        "emotional_intensity": round(intensity, 3),
        "dominant_tone": dominant_tone,
        "tone_label": tone_label,
        "positive_terms": sorted(list(set(found_pos))),
        "negative_terms": sorted(list(set(found_neg))),
        "absolutist_terms": sorted(list(set(found_ab))),
    }

