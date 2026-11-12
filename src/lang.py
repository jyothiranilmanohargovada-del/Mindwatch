"""Script check. The model is English-only; non-Latin text must not be scored as 'low risk'."""
import re

_LETTER = re.compile(r"[^\W\d_]", re.UNICODE)
_LATIN = re.compile(r"[A-Za-z\u00C0-\u024F]")


def non_latin_ratio(text: str) -> float:
    letters = _LETTER.findall(text)
    if not letters:
        return 0.0
    return 1 - sum(bool(_LATIN.match(c)) for c in letters) / len(letters)


def is_supported(text: str) -> bool:
    """True if the text is mostly Latin script (English or romanised). Romanised
    Tamil/Hindi cannot be detected here and is a documented limitation."""
    return non_latin_ratio(text) < 0.30
