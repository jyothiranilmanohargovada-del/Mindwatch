"""Risk grading, context-aware crisis detection and symptom-theme tagging.

IMPORTANT: a screening aid, NOT a diagnostic tool. Crisis detection is rule based and
intentionally errs towards showing help; its limits are documented in docs/ETHICS.md.
"""
import re
from config import thresholds

# (pattern, negatable) - negatable patterns are suppressed by a nearby negation ("I would never kill myself")
_PATTERNS = [
    (r"\bkill(ing)? myself\b", True),
    (r"\bend(ing)? (my life|it all)\b", True),
    (r"\bwant(ed)? to die\b", True),
    (r"\bsuicid(e|al)\b", True),
    (r"\bbetter off (dead|without me)\b", True),
    (r"\bno reason to live\b", False),
    (r"\b(hurt(ing)?|harm(ing)?|cut(ting)?) myself\b(?! (some )?slack)", True),
    (r"\bself[- ]?harm\b", True),
    (r"\bdo(n't| not) want to (live|be alive|be here|wake up|exist)\b", False),
    (r"\bwish i (was|were) dead\b", False),
    (r"\bcan'?t go on\b", False),
    (r"\bjust want (the pain|it all|everything) to (stop|end)\b", False),
]
_COMPILED = [(re.compile(p, re.I), neg) for p, neg in _PATTERNS]
_NEGATION = re.compile(r"\b(never|not|no|wouldn'?t|won'?t|don'?t|doesn'?t|didn'?t|can'?t|cannot|n't|refuse to)\b", re.I)
_NON_PERSONAL = re.compile(r"suicide (prevention|awareness|squad|hotline|helpline|rate|rates|bomber|note)|self[- ]?harm (awareness|prevention)", re.I)
_HYPERBOLE = re.compile(r"\b(lol|lmao|haha+|jk|😂|🤣)\b|😂|🤣", re.I)

THEMES = {
    "sleep problems": r"\b(can'?t sleep|insomnia|lie awake|lying awake|sleeping all day|sleeping way too much|oversleep|wake up exhausted|broken sleep)\b",
    "low energy / fatigue": r"\b(no energy|exhausted|always tired|so tired|fatigue|drained|worn out|sluggish|no physical energy)\b",
    "hopelessness": r"\b(hopeless|no point|pointless|nothing will (ever )?(change|get better)|no future|what's the use|given up)\b",
    "worthlessness / guilt": r"\b(worthless|useless|burden|failure|not good enough|guilty|hate myself|disappointment|ashamed of myself)\b",
    "social withdrawal / loneliness": r"\b(alone|lonely|isolat\w+|stopped talking|avoiding my friends|ignore (all )?my messages|nobody understands|withdrawing|no one cares|alienated)\b",
    "loss of interest": r"\b(lost interest|don'?t enjoy|nothing makes me happy|no longer enjoy|numb|feels flat|anhedonia|nothing feels fun)\b",
    "appetite change": r"\b(no appetite|haven'?t eaten|not eating|skipping meals|eating too much|lost appetite|overeating)\b",
    "concentration difficulty": r"\b(can'?t concentrate|can not concentrate|foggy|can'?t focus|focus on anything|brain fog|mind wandering)\b",
    "persistent sadness": r"\b(empty|sad|crying|cry for no reason|heavy and grey|low for (months|ages)|miserable|deep sorrow)\b",
    "academic stress": r"\b(exam|exams|finals|midterm|midterms|studying|grades?|gpa|failing|assignments?|thesis|dissertation|academic|homework|submission|deadline|coursework|flunk(ed)?)\b",
    "social pressure & comparison": r"\b(falling behind|disappoint my parents|impostor|imposter|comparing myself|peer pressure|not measuring up|social pressure|everyone else is ahead)\b",
    "lack of motivation & burnout": r"\b(no motivation|can'?t get out of bed|procrastinat\w+|burnout|burned out|zero drive|executive dysfunction|can'?t bring myself to|can'?t start|stuck in bed|paralyzed with work)\b",
    "anxiety & panic": r"\b(panic attack|chest tight|racing heart|spiraling|freaking out|hyperventilat\w+|terrified|so anxious|constant dread|anxiety attack|overthinking)\b",
}



def _norm(text: str) -> str:
    return text.lower().replace("\u2019", "'")


def crisis_assessment(text: str) -> dict:
    """Return {'crisis': bool, 'suppressed': reason|None}.

    Suppression: negation within the 40 characters before the match, discussion of the topic
    ('suicide prevention', 'Suicide Squad'), or obvious hyperbole ('lol') on idiom-prone phrases.
    """
    t = _norm(text)
    t_clean = _NON_PERSONAL.sub(" ", t)
    reason = None
    for rx, negatable in _COMPILED:
        for m in rx.finditer(t_clean):
            window = t_clean[max(0, m.start() - 40): m.start()]
            # keep only the current clause
            window = re.split(r"[.!?;,]", window)[-1]
            if negatable and _NEGATION.search(window + " " + m.group(0)[:0]):
                reason = "negated"
                continue
            if negatable and _HYPERBOLE.search(t_clean) and re.search(r"kill(ing)? myself|want(ed)? to die", m.group(0)):
                reason = "hyperbole"
                continue
            return {"crisis": True, "suppressed": None}
    return {"crisis": False, "suppressed": reason}


def has_crisis_language(text: str) -> bool:
    return crisis_assessment(text)["crisis"]


def detect_themes(text: str):
    t = _norm(text)
    return [name for name, pat in THEMES.items() if re.search(pat, t)]


def grade(prob: float, crisis: bool) -> str:
    if crisis:
        return "CRISIS"
    moderate, high = thresholds()
    if prob >= high:
        return "HIGH"
    if prob >= moderate:
        return "MODERATE"
    return "LOW"
