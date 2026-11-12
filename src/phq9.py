"""PHQ-9 depression screening questionnaire (public-domain instrument; Kroenke, Spitzer & Williams, 2001).

A score is a screening indicator, NOT a diagnosis. Item 9 (thoughts of death/self-harm) > 0
always triggers help-line information regardless of the total.
"""
ITEMS = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself - or that you are a failure or have let yourself or your family down",
    "Trouble concentrating on things, such as reading or watching television",
    "Moving or speaking so slowly that other people could have noticed - or the opposite, being so fidgety or restless that you have been moving around a lot more than usual",
    "Thoughts that you would be better off dead, or of hurting yourself in some way",
]
OPTIONS = [(0, "Not at all"), (1, "Several days"), (2, "More than half the days"), (3, "Nearly every day")]
BANDS = [(4, "Minimal"), (9, "Mild"), (14, "Moderate"), (19, "Moderately severe"), (27, "Severe")]
GUIDANCE = {
    "Minimal": "Your answers suggest few or no depressive symptoms. Keep up healthy routines and re-check if things change.",
    "Mild": "Your answers suggest mild symptoms. Self-care, staying connected and re-checking in a couple of weeks is reasonable; talk to someone if it persists.",
    "Moderate": "Your answers suggest moderate symptoms. Consider speaking to a doctor or counsellor.",
    "Moderately severe": "Your answers suggest moderately severe symptoms. Please consider contacting a doctor or mental-health professional soon.",
    "Severe": "Your answers suggest severe symptoms. Please contact a doctor or mental-health professional as soon as you can.",
}


def score(answers):
    if len(answers) != 9 or any((not isinstance(a, int)) or a < 0 or a > 3 for a in answers):
        raise ValueError("PHQ-9 needs 9 answers, each an integer 0-3")
    total = sum(answers)
    band = next(name for limit, name in BANDS if total <= limit)
    return {"total": total, "band": band, "guidance": GUIDANCE[band], "item9_flag": answers[8] > 0}
