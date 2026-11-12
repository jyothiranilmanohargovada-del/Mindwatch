"""Text cleaning for social-media posts.

Design note: stop-word removal is intentionally NOT applied. First-person
pronouns ("i", "me", "my") and negations ("no", "never", "nothing") are
known linguistic markers of depressive language, so they must be kept.
"""
import html
import re
from sklearn.base import BaseEstimator, TransformerMixin

URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"@\w+")
HASH_RE = re.compile(r"#(\w+)")
ELONG_RE = re.compile(r"(.)\1{2,}")
SPACE_RE = re.compile(r"\s+")

CONTRACTIONS = {
    "can't": "can not", "won't": "will not", "don't": "do not", "didn't": "did not",
    "doesn't": "does not", "isn't": "is not", "i'm": "i am", "i've": "i have",
    "i'll": "i will", "it's": "it is", "haven't": "have not", "wasn't": "was not",
}


def clean_text(text: str) -> str:
    text = html.unescape(str(text)).lower()
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = HASH_RE.sub(r"\1", text)
    text = text.replace("’", "'")
    for k, v in CONTRACTIONS.items():
        text = text.replace(k, v)
    text = ELONG_RE.sub(r"\1\1", text)          # "soooo" -> "soo"
    text = re.sub(r"[^a-z0-9'\s]", " ", text)
    return SPACE_RE.sub(" ", text).strip()


def tokenize(text: str):
    return re.findall(r"[a-z0-9']+", text)


class TextCleaner(BaseEstimator, TransformerMixin):
    """sklearn-compatible wrapper so cleaning is part of the saved pipeline."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return [clean_text(t) for t in X]
