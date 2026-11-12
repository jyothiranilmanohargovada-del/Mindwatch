"""Intelligent context-aware supportive chat engine for MindWatch 2.0.

Features:
- Multi-turn conversation state & context memory.
- Fine-grained student concern identification (academic, loneliness, sleep, anxiety, motivation, relationships).
- Evidence-based coping exercises (Box breathing, 5-4-3-2-1 grounding, cognitive reframing, sleep stimulus control, 2-minute rule).
- Optional backend LLM integration (Google Gemini / OpenAI compatible) via environment variables.
- Robust, intelligent, multi-turn local fallback engine when API keys are not present or network is unavailable.
- Strict Crisis Safety Mechanism prioritizing immediate human assistance, emergency helplines, and de-escalation.
- Never diagnoses depression or anxiety, and never replaces professional mental health care.
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from src.assistant import DISCLAIMER, load_resources
from src.predict import analyze_post

# Coping exercises
BOX_BREATHING = (
    "Let's do slow box breathing together:\n\n"
    "1. **Breathe in** slowly through your nose for 4 counts...\n"
    "2. **Hold** gently for 4 counts...\n"
    "3. **Exhale** smoothly through your mouth for 4 counts...\n"
    "4. **Hold** empty for 4 counts.\n\n"
    "Repeat this cycle 4 times. Focus only on the sensation of air filling and leaving your lungs."
)

GROUNDING_54321 = (
    "Let's ground your senses with the 5-4-3-2-1 technique to ease overwhelm:\n\n"
    "• Name **5 things you can see** around you right now.\n"
    "• Notice **4 things you can physically feel** (e.g. your feet on the floor, your chair, the fabric of your sleeve).\n"
    "• Listen for **3 things you can hear** (a fan, birds outside, a distant hum).\n"
    "• Identify **2 things you can smell** (or two scents you enjoy).\n"
    "• Notice **1 thing you can taste** (or take a sip of cool water).\n\n"
    "Take your time. What is one thing you notice around you right now?"
)

SLEEP_HYGIENE = (
    "Here is an evidence-based sleep reset plan:\n\n"
    "• **The 20-Minute Stimulus Control Rule:** If you are lying in bed awake for more than 20 minutes, get out of bed. Sit in a dim room and read something quiet until you feel drowsy. Keep bed strictly associated with sleep.\n"
    "• **Digital Sunset:** Disconnect from phone and laptop screens 45 minutes before sleep to allow your natural melatonin to rise.\n"
    "• **Worry Journal:** Write down tomorrow's tasks on paper before getting into bed so your mind doesn't have to keep rehearsing them."
)

ACADEMIC_REFRAMING = (
    "When academic pressure peaks, our minds often jump to worst-case scenarios ('If I fail this exam, my life is ruined').\n\n"
    "Let's test that thought:\n"
    "1. Is that thought an absolute fact, or an anxiety prediction?\n"
    "2. Have you handled difficult academic deadlines before?\n"
    "3. What is the single next manageable 20-minute action you can take right now?\n\n"
    "You are a human being pursuing an education, not just a grade generator."
)

TWO_MINUTE_RULE = (
    "When motivation is paralyzed, do not try to do the whole task. Use the **2-Minute Micro-Action Rule**:\n\n"
    "Commit to working on the avoided task for just 120 seconds. If you want to stop after 2 minutes, you have full permission to stop.\n\n"
    "Overcoming the initial friction of starting is 90% of the battle. What is one tiny 2-minute step you could try?"
)

OPENING = (
    "Hi, I'm MindWatch Support Assistant — an automated listener and coping guide, not a therapist or human clinician. "
    "I'm here to listen, offer evidence-based calming exercises, and connect you with support resources. What is on your mind today?"
)

CRISIS_REPLY = (
    "I am deeply concerned about what you just shared, and I want you to know that your safety and life truly matter. "
    "You do not have to carry this immense pain alone. Please connect with someone who can support you in person right now, "
    "or reach out to one of the confidential 24/7 crisis helplines listed below immediately. "
    "If you are in immediate danger of acting on these thoughts, please call 112 (or your local emergency services) or go to the nearest emergency room."
)


def start_state() -> Dict[str, Any]:
    """Initialize a rich conversation session state."""
    return {
        "turns": 0,
        "high": 0,
        "history": [],
        "topics": [],
        "last_exercise": None,
        "crisis_mode": False
    }


def detect_chat_intent(text: str) -> Optional[str]:
    """Detect specific user commands or explicit coping exercise requests."""
    t = text.lower()
    if re.search(r"\b(breath|breathing|breathe|can'?t breathe)\b", t) or (re.search(r"\b(calm down|panic)\b", t) and re.search(r"\b(help|how|exercise|guide)\b", t)):
        return "breath"

    if re.search(r"\b(ground|grounding|5-?4-?3-?2-?1|sensory|overwhelm\w*)\b", t):
        return "ground"
    if re.search(r"\b(sleep|insomnia|can'?t sleep|bedtime|tired|nightmare)\b", t) and re.search(r"\b(tip|help|how|advice|exercise|routine)\b", t):
        return "sleep"
    if re.search(r"\b(exam|study|studying|fail\w*|gpa|grades?|reframe|academic)\b", t) and re.search(r"\b(stress|help|panic|overwhelm|tip|advice)\b", t):
        return "academic_reframe"
    if re.search(r"\b(procrastinat\w*|motivation|can'?t start|stuck|lazy|inertia)\b", t) and re.search(r"\b(help|how|tip|advice|rule)\b", t):
        return "micro_action"
    if re.search(r"\b(thank|thanks|appreciate it|grateful)\b", t):
        return "thanks"
    if re.search(r"\b(bye|goodbye|cya|take care)\b", t):
        return "bye"
    if re.fullmatch(r"\s*(help|what can you do\??|options|menu)\s*", t):
        return "help"
    return None


def identify_student_concern(text: str) -> Dict[str, Any]:
    """Identify the main emotional topic and concern from the user's message."""
    t = text.lower()
    concerns = []

    if re.search(r"\b(exam|exams|finals|midterm|midterms|studying|gpa|grades|failing|assignment|assignments|thesis|dissertation|homework|deadline|coursework)\b", t):
        concerns.append("academic_stress")
    if re.search(r"\b(alone|lonely|isolated|isolation|no friends|nobody talks to me|ignored|left out|disconnected|nobody cares)\b", t):
        concerns.append("loneliness")
    if re.search(r"\b(sleep|insomnia|can'?t sleep|awake all night|exhausted|wake up tired|nightmares)\b", t):
        concerns.append("sleep_issues")
    if re.search(r"\b(panic|heart racing|chest tight|freaking out|spiraling|anxiety|dread|scared|terrified)\b", t):
        concerns.append("anxiety_panic")
    if re.search(r"\b(no motivation|can'?t get out of bed|procrastinat\w+|burnout|burned out|zero energy|paralyzed|stuck)\b", t):
        concerns.append("motivation_burnout")
    if re.search(r"\b(parents?|mom|dad|family|friend|friends|partner|breakup|arguing|relationship|disappoint)\b", t):
        concerns.append("relationships")
    if re.search(r"\b(hopeless|pointless|no future|giving up|what's the point|nothing matters)\b", t):
        concerns.append("hopelessness")

    primary = concerns[0] if concerns else "general_wellbeing"
    return {"primary": primary, "all": concerns}


def call_llm_api(message: str, state: dict) -> Optional[str]:
    """Attempt to generate response via LLM API if GEMINI_API_KEY or OPENAI_API_KEY is configured."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if not gemini_key and not openai_key:
        return None

    system_instruction = (
        "You are MindWatch Assistant, an empathetic, student-oriented mental wellbeing listener and coping guide. "
        "You are NOT a doctor, psychologist, or therapist. You NEVER diagnose depression, anxiety, or medical conditions. "
        "Acknowledge the user's feelings with warmth, active listening, and validation. "
        "Offer practical, evidence-based coping strategies (mindfulness, box breathing, 5-4-3-2-1 grounding, 2-minute rule for procrastination, sleep hygiene). "
        "Ask one gentle, open-ended follow-up question. Keep responses supportive, concise (2-3 short paragraphs), non-judgmental, and free of clinical jargon. "
        "Never say 'You have depression' or dismiss their struggle."
    )

    # Gemini REST API implementation using standard library urllib
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            contents = []
            for h in (state.get("history") or [])[-6:]:
                role = "user" if h["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": h["content"]}]})
            contents.append({"role": "user", "parts": [{"text": message}]})

            payload = {
                "system_instruction": {"parts": [{"text": system_instruction}]},
                "contents": contents,
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 400}
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=6.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
        except Exception:
            # Fall back safely on any API or network issue
            pass

    # OpenAI-compatible REST API fallback
    if openai_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            messages = [{"role": "system", "content": system_instruction}]
            for h in (state.get("history") or [])[-6:]:
                messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": message})

            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "max_tokens": 400,
                "temperature": 0.7
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=6.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                return text.strip()
        except Exception:
            pass

    return None


def generate_local_response(message: str, concern_info: dict, state: dict, level: str) -> str:
    """Intelligent, multi-turn, context-aware local conversational fallback."""
    concern = concern_info["primary"]
    turns = state.get("turns", 1)

    # Dynamic empathetic reflections tailored to topic
    REFLECTIONS = {
        "academic_stress": (
            "Academic pressure can feel intensely suffocating, especially when coursework, exams, and expectations pile up all at once. "
            "Please remember that your intelligence and worth are not defined solely by grades or productivity."
        ),
        "loneliness": (
            "Feeling lonely or disconnected is deeply painful, and it is something so many students experience in silence. "
            "Even when it feels like no one understands, you are reaching out right now, and that matters."
        ),
        "sleep_issues": (
            "Tossing and turning with a racing mind leaves both your body and emotions completely depleted. "
            "When sleep is disrupted, even everyday tasks can feel ten times heavier."
        ),
        "anxiety_panic": (
            "That sense of anxiety and racing thoughts is exhausting. Your nervous system is in high alert, "
            "and it is completely natural that your body feels tense and overwhelmed right now."
        ),
        "motivation_burnout": (
            "When burnout sets in, even opening a textbook or getting out of bed requires enormous effort. "
            "This isn't laziness—it is often a signal that your mental and emotional reserves are running on empty."
        ),
        "relationships": (
            "Navigating friction, misunderstandings, or high expectations with people in your life can carry an immense emotional weight. "
            "It makes complete sense that this is troubling your mind."
        ),
        "hopelessness": (
            "I hear how dark and difficult things feel right now. Heavy feelings can convince us that things won't change, "
            "but please remember that emotional weight is a temporary storm, not your permanent future."
        ),
        "general_wellbeing": (
            "Thank you for sharing what you are going through. Putting heavy emotions into words takes real courage."
        )
    }

    # Actionable guidance tailored to topic
    ACTIONS = {
        "academic_stress": (
            "A helpful approach right now is to shrink your focus: rather than looking at the entire semester, "
            "pick just one small 15-minute chunk of work. Would you like to try our academic reframing exercise?"
        ),
        "loneliness": (
            "Low-pressure connection can sometimes soften the isolation: sending a simple meme or a short 'thinking of you' message "
            "to someone you haven't spoken to in a while, without needing to explain everything."
        ),
        "sleep_issues": (
            "If you are currently in bed unable to sleep, try getting up for 15 minutes into a dim room until you feel drowsy. "
            "We also have a quick sleep hygiene guide if you'd like to explore it."
        ),
        "anxiety_panic": (
            "Right now, let's bring your physical body back to safety. We can do a quick 4-round Box Breathing exercise "
            "or a 5-4-3-2-1 sensory grounding exercise together."
        ),
        "motivation_burnout": (
            "Rather than pushing yourself to be productive today, consider giving yourself permission to do the bare minimum for an hour. "
            "The 2-Minute Micro-Action Rule can also help when you feel ready."
        ),
        "relationships": (
            "Setting gentle emotional boundaries and giving yourself time to process your thoughts before reacting can help ease the strain."
        ),
        "hopelessness": (
            "When thoughts feel this heavy, talking to a real human counsellor or trusted confidant makes a real difference. "
            "You do not have to figure out everything today."
        ),
        "general_wellbeing": (
            "Taking things one breath and one moment at a time is enough for today."
        )
    }

    # Meaningful open-ended follow-ups (rotating to avoid repetition)
    FOLLOW_UPS_MAP = {
        "academic_stress": [
            "What is the single most urgent deadline or task that feels heaviest on your shoulders right now?",
            "Have you been able to take any proper breaks today without studying?",
            "Is there a classmate, professor, or campus advisor you feel comfortable approaching?"
        ],
        "loneliness": [
            "How long have you felt this sense of distance or loneliness?",
            "Is there someone you used to feel close to that you miss connecting with?",
            "What is one quiet activity that usually brings you a bit of comfort?"
        ],
        "sleep_issues": [
            "Has your mind been racing about specific worries when you lie down?",
            "Roughly how many hours of sleep have you been able to get lately?",
            "Would you like to try a calming grounding exercise before you try sleeping again?"
        ],
        "anxiety_panic": [
            "Where in your body are you feeling the physical tension most strongly right now?",
            "Would you like me to guide you through a 2-minute box breathing cycle right now?",
            "What was happening right before this spike in anxiety started?"
        ],
        "motivation_burnout": [
            "What is one tiny thing you could take off your plate today to give yourself some breathing room?",
            "When did you last have a day where you could genuinely rest without feeling guilty?",
            "Would you like to try the 2-Minute Rule on just one small task?"
        ],
        "relationships": [
            "What has been the hardest part of dealing with this situation?",
            "Do you feel like your perspective is being heard by them?",
            "Is there someone outside of this situation who can offer you neutral support?"
        ],
        "hopelessness": [
            "What is one thing that has helped you get through difficult stretches in the past?",
            "Is there a friend, family member, or counselor you could message right now?",
            "Can you tell me a little more about what has brought you to this point?"
        ],
        "general_wellbeing": [
            "How long have you been carrying these feelings?",
            "What has been the most challenging part of your week so far?",
            "What is one small thing that would feel gentle or comforting to do for yourself today?"
        ]
    }

    reflection = REFLECTIONS.get(concern, REFLECTIONS["general_wellbeing"])
    action = ACTIONS.get(concern, ACTIONS["general_wellbeing"])
    questions = FOLLOW_UPS_MAP.get(concern, FOLLOW_UPS_MAP["general_wellbeing"])
    question = questions[(turns - 1) % len(questions)]

    # For turn 1, include opening note
    prefix = ""
    if turns == 1:
        prefix = "Thank you for reaching out. "

    return f"{prefix}{reflection}\n\n{action}\n\n{question}"


def reply(message: str, state: dict) -> dict:
    """Process incoming user message and return context-aware supportive reply."""
    msg = (message or "").strip()
    state["turns"] = state.get("turns", 0) + 1

    if not msg:
        return {
            "reply": "I'm right here whenever you want to write or share something.",
            "level": None,
            "resources": [],
            "engine": "local",
            "topic": None
        }

    # 1. CRISIS SAFETY PRE-SCREENING (Immediate paramount priority)
    res = analyze_post(msg)
    if res["crisis"]:
        state["high"] = state.get("high", 0) + 3
        state["crisis_mode"] = True
        return {
            "reply": CRISIS_REPLY,
            "level": "CRISIS",
            "resources": load_resources(),
            "engine": "crisis_safety",
            "topic": "crisis"
        }

    # 2. Check for explicit intent or exercise trigger
    intent = detect_chat_intent(msg)
    canned_exercises = {
        "breath": BOX_BREATHING,
        "ground": GROUNDING_54321,
        "sleep": SLEEP_HYGIENE,
        "academic_reframe": ACADEMIC_REFRAMING,
        "micro_action": TWO_MINUTE_RULE,
        "thanks": "You are very welcome. Take things one moment at a time. I'm here if you want to keep talking.",
        "bye": "Take gentle care of yourself. Remember that reaching out to people you trust is a strength, not a weakness.",
        "help": (
            "I'm here to support you in whatever way feels most comfortable:\n"
            "• Type **'breathing'** for a guided Box Breathing cycle.\n"
            "• Type **'grounding'** for the 5-4-3-2-1 sensory reset.\n"
            "• Type **'sleep'** for evidence-based sleep hygiene tips.\n"
            "• Type **'exam'** or **'academic'** for cognitive reframing.\n"
            "• Or simply talk about what you are feeling—academic stress, loneliness, fatigue, or relationships."
        )
    }

    if intent:
        state["last_exercise"] = intent
        reply_content = canned_exercises[intent]
        state.setdefault("history", []).append({"role": "user", "content": msg})
        state["history"].append({"role": "assistant", "content": reply_content})
        return {
            "reply": reply_content,
            "level": res["level"],
            "resources": [],
            "engine": "exercise_guide",
            "topic": intent
        }


    level = res["level"]
    if level in ("HIGH", "MODERATE"):
        state["high"] = state.get("high", 0) + (1 if level == "HIGH" else 0)

    if level == "UNSUPPORTED":
        return {
            "reply": "I can only read English (Latin-script) text, but I want to make sure you have access to help. The helplines below can assist in multiple languages.",
            "level": level,
            "resources": load_resources(),
            "engine": "local",
            "topic": "unsupported"
        }

    concern_info = identify_student_concern(msg)
    state.setdefault("topics", []).append(concern_info["primary"])

    # 3. Try LLM API (Gemini or OpenAI)
    ai_reply = call_llm_api(msg, state)
    engine_used = "ai" if ai_reply else "local"

    if ai_reply:
        reply_text = ai_reply
    else:
        # 4. Smart Local Fallback Engine
        reply_text = generate_local_response(msg, concern_info, state, level)

    # 5. High cumulative distress escalation (if user expressed repeated pain across turns)
    resources = []
    if state.get("high", 0) >= 2:
        escalation_note = (
            "\n\n*Because you've shared a lot of heavy pain during our conversation, I'd really encourage "
            "speaking with a university counsellor, doctor, or trusted person. The confidential contacts below are a safe place to start.*"
        )
        reply_text += escalation_note
        resources = load_resources()

    # Maintain conversation history
    state.setdefault("history", []).append({"role": "user", "content": msg})
    state["history"].append({"role": "assistant", "content": reply_text})

    return {
        "reply": reply_text,
        "level": level,
        "resources": resources,
        "engine": engine_used,
        "topic": concern_info["primary"]
    }
