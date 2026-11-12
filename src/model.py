"""Pipeline: cleaning -> (TF-IDF + linguistic features) -> classifier."""
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

from config import RANDOM_STATE
from src.features import LexiconFeatures
from src.preprocess import TextCleaner


def build_pipeline(clf, use_lexicon=True):
    tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.9,
                            sublinear_tf=True, token_pattern=r"[a-z0-9']+")
    parts = [("tfidf", tfidf)]
    if use_lexicon:
        parts.append(("lex", Pipeline([("f", LexiconFeatures()),
                                       ("s", StandardScaler(with_mean=False))])))
    return Pipeline([("clean", TextCleaner()),
                     ("features", FeatureUnion(parts)),
                     ("clf", clf)])


def candidate_models():
    return {
        "Logistic Regression": LogisticRegression(max_iter=2000, C=2.0, random_state=RANDOM_STATE),
        "Linear SVM (calibrated)": CalibratedClassifierCV(
            LinearSVC(C=1.0, max_iter=10000, random_state=RANDOM_STATE), cv=3),
        "Multinomial NB": MultinomialNB(alpha=0.5),
    }
