"""Supportive-assistance module: non-diagnostic messages, tips and help-line information."""
import json
from config import RESOURCES_PATH

DISCLAIMER = ("This tool looks for language patterns only. It cannot diagnose depression and can be wrong. "
              "Please speak to a qualified mental-health professional if you are worried about how you feel.")

MESSAGES = {
    "LOW": "Thanks for sharing. Nothing in this text strongly suggests distress, but how you feel always matters. If things change, reaching out early is a good idea.",
    "MODERATE": "Some of what you wrote sounds heavy. Many people go through stretches like this, and you do not have to carry it alone.",
    "HIGH": "What you wrote sounds really painful, and I'm glad you put it into words. Talking to someone you trust, or a professional, can make a real difference.",
    "CRISIS": "I'm concerned about your safety. Please reach out right now to someone who can help - a crisis line below, a trusted person near you, or local emergency services if you may act on these thoughts.",
    "UNSUPPORTED": "I can only read English (Latin-script) text, so I can't assess this. If you are struggling, the contacts below can help in many languages.",
}
TIPS = {
    "sleep problems": "Keep a regular sleep and wake time and keep screens away for the last hour before bed.",
    "low energy / fatigue": "Try one very small task (a glass of water, a 5-minute walk). Small wins can rebuild momentum.",
    "hopelessness": "Feelings of hopelessness are a symptom, not a fact about your future. A counsellor can help you work through them.",
    "worthlessness / guilt": "Write down one thing you did today, however small. Self-critical thoughts are often harsher than reality.",
    "social withdrawal / loneliness": "Send one short message to a friend or family member. You do not need to explain everything.",
    "loss of interest": "Schedule one gentle activity you used to enjoy, even for ten minutes, without expecting to enjoy it fully.",
    "appetite change": "Try small, regular meals or snacks, and mention appetite changes to a doctor.",
    "concentration difficulty": "Break tasks into 10-15 minute chunks with short breaks.",
    "persistent sadness": "Talking to a counsellor or doctor about low mood that lasts more than two weeks is a good step.",
    "academic stress": "Break coursework into 20-minute study blocks with short breaks. Remember that academic performance does not define your human worth.",
    "social pressure & comparison": "Remember that social media and peer conversations rarely show others' struggles. Focus on your personal learning pace.",
    "lack of motivation & burnout": "Use the 2-minute rule: commit to working on an avoided task for just 120 seconds, or give yourself permission to rest without guilt.",
    "anxiety & panic": "Try slow box breathing (4 in, 4 hold, 4 out, 4 hold) or name 5 things you can see to ground physical anxiety spikes.",
}
GENERAL = ["Talk to someone you trust about how you've been feeling.",
           "Consider booking an appointment with a doctor or counsellor.",
           "Spend some time outdoors in daylight and keep to a simple daily routine."]


def load_resources():
    with open(RESOURCES_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_response(level: str, themes) -> dict:
    tips = [TIPS[t] for t in themes if t in TIPS][:4]
    if level in ("MODERATE", "HIGH"):
        tips += GENERAL[: max(0, 4 - len(tips))]
    if level == "CRISIS":
        tips = ["Tell someone near you right now so you are not alone.",
                "If you can, move away from anything you could use to harm yourself."]
    if level == "UNSUPPORTED":
        tips = []
    resources = load_resources() if level in ("MODERATE", "HIGH", "CRISIS", "UNSUPPORTED") else []
    return {"message": MESSAGES[level], "suggestions": tips, "resources": resources, "disclaimer": DISCLAIMER}
