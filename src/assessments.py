"""Multi-category mental wellbeing self-check questionnaires for MindWatch 2.0.

Validated Instruments:
- PHQ-9 (Patient Health Questionnaire-9; Kroenke et al., 2001) - Validated depression screening.
- GAD-7 (Generalized Anxiety Disorder-7; Spitzer et al., 2006) - Validated anxiety screening.

Non-Diagnostic Student Wellbeing Screeners:
- Sleep & Lifestyle Habits Screener
- Academic & Social Pressure Screener
- Motivation & Daily Activities Screener

Screening aids only: not diagnostic medical tools. Item 9 on PHQ-9 triggers crisis resources.
"""
from typing import Dict, List, Any

# Standard 4-point Likert options for 2-week recall
STANDARD_OPTIONS = [
    (0, "Not at all"),
    (1, "Several days"),
    (2, "More than half the days"),
    (3, "Nearly every day")
]

CATEGORIES: Dict[str, Dict[str, Any]] = {
    "phq9": {
        "id": "phq9",
        "title": "Mood & Emotional Wellbeing (PHQ-9)",
        "short_title": "Mood (PHQ-9)",
        "badge": "Validated Instrument",
        "is_validated": True,
        "timeframe": "Over the last 2 weeks",
        "description": "Standard 9-item clinical screener measuring frequency of depressive symptoms.",
        "disclaimer": "The PHQ-9 is an evidence-based screening questionnaire, not a clinical diagnosis. Only a qualified clinician can diagnose depression.",
        "items": [
            "Little interest or pleasure in doing things",
            "Feeling down, depressed, or hopeless",
            "Trouble falling or staying asleep, or sleeping too much",
            "Feeling tired or having little energy",
            "Poor appetite or overeating",
            "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
            "Trouble concentrating on things, such as reading or watching television",
            "Moving or speaking so slowly that other people could have noticed — or the opposite, being so fidgety or restless that you have been moving around a lot more than usual",
            "Thoughts that you would be better off dead, or of hurting yourself in some way"
        ],
        "options": STANDARD_OPTIONS,
        "max_score": 27,
        "bands": [
            (4, "Minimal", "Few or no depressive symptoms reported. Continue your self-care practices and check in periodically."),
            (9, "Mild", "Mild depressive symptoms noted. Focusing on healthy routines, social connection, and stress management is recommended; consider speaking with someone if this persists."),
            (14, "Moderate", "Moderate depressive symptoms. We encourage scheduling an appointment with a campus counsellor, therapist, or physician to explore support options."),
            (19, "Moderately Severe", "Moderately severe symptoms. Speaking with a doctor or mental health professional soon is strongly recommended."),
            (27, "Severe", "Severe symptoms indicated. Please reach out to a healthcare professional, student counselling center, or helpline as soon as possible.")
        ],
        "recommendations": {
            "Minimal": [
                "Maintain your regular sleep, exercise, and social routines.",
                "Practice proactive stress relief such as mindfulness or creative hobbies.",
                "Retake this self-check in 2–4 weeks to monitor your wellbeing."
            ],
            "Mild": [
                "Establish a consistent daily schedule with dedicated winding-down time.",
                "Reach out to a trusted friend, family member, or classmate for casual connection.",
                "Break daily tasks into smaller 15-minute intervals to reduce feeling overwhelmed."
            ],
            "Moderate": [
                "Consider booking an introductory consultation with a university counsellor or doctor.",
                "Share how you've been feeling with someone you trust—you do not have to carry this alone.",
                "Focus on basic foundational care: regular balanced meals, daylight walks, and consistent sleep."
            ],
            "Moderately Severe": [
                "Please connect with a mental health professional or primary care doctor for support.",
                "If campus services are available, request an appointment with student health services.",
                "Review the helpline directory below for immediate confidential listening."
            ],
            "Severe": [
                "Please reach out to a mental health professional or emergency service today.",
                "Contact Tele-MANAS at 14416 or your local emergency line (112) for immediate support.",
                "Let a trusted person near you know how much pain you are experiencing right now."
            ]
        }
    },
    "gad7": {
        "id": "gad7",
        "title": "Stress & Anxiety (GAD-7)",
        "short_title": "Anxiety (GAD-7)",
        "badge": "Validated Instrument",
        "is_validated": True,
        "timeframe": "Over the last 2 weeks",
        "description": "Standard 7-item clinical screener measuring generalized anxiety and persistent worry.",
        "disclaimer": "The GAD-7 is an evidence-based anxiety screening tool, not a clinical diagnosis. Consult a qualified professional for clinical evaluation.",
        "items": [
            "Feeling nervous, anxious, or on edge",
            "Not being able to stop or control worrying",
            "Worrying too much about different things",
            "Trouble relaxing",
            "Being so restless that it is hard to sit still",
            "Becoming easily annoyed or irritable",
            "Feeling afraid, as if something awful might happen"
        ],
        "options": STANDARD_OPTIONS,
        "max_score": 21,
        "bands": [
            (4, "Minimal", "Minimal anxiety symptoms reported. Your anxiety levels appear within a typical, manageable range."),
            (9, "Mild", "Mild anxiety symptoms. Mild worry or restlessness can occur with college stress; mindfulness and physical activity can help keep it balanced."),
            (14, "Moderate", "Moderate anxiety symptoms. Persistent worry or tension may be impacting your concentration and comfort. Professional guidance can offer effective coping tools."),
            (21, "Severe", "Severe anxiety symptoms. High levels of nervousness or worry are present. Consulting a medical or mental health professional is strongly recommended.")
        ],
        "recommendations": {
            "Minimal": [
                "Continue using healthy relaxation habits such as deep breathing or exercise.",
                "Keep note of stressful triggers before exam periods.",
                "Practice healthy boundaries around study time and rest."
            ],
            "Mild": [
                "Try Box Breathing (4 seconds in, 4 hold, 4 out, 4 hold) when feeling tense.",
                "Limit caffeine consumption, especially during late afternoon or evening hours.",
                "Set aside 15 minutes of designated 'worry time' to write down racing thoughts, then set the notebook aside."
            ],
            "Moderate": [
                "Explore evidence-based relaxation techniques like 5-4-3-2-1 sensory grounding.",
                "Discuss stress and anxiety management with a counsellor or health professional.",
                "Structure your day with clear work/rest boundaries to avoid constant cognitive overdrive."
            ],
            "Severe": [
                "Schedule an appointment with a counsellor, psychologist, or physician for guidance.",
                "Reach out to a trusted loved one or counsellor to share what you are experiencing.",
                "Use our support chat's breathing exercise whenever physical panic symptoms arise."
            ]
        }
    },
    "sleep": {
        "id": "sleep",
        "title": "Sleep & Lifestyle Wellbeing Screener",
        "short_title": "Sleep & Lifestyle",
        "badge": "Wellbeing Screener",
        "is_validated": False,
        "timeframe": "Over the last 2 weeks",
        "description": "Non-diagnostic screener exploring sleep quality, bedtime habits, and daytime vitality.",
        "disclaimer": "This is an educational lifestyle wellbeing screener designed to help understand daily routine patterns. It is not a clinical assessment of sleep disorders.",
        "items": [
            "Difficulty falling asleep within 30 minutes, or waking up multiple times during the night",
            "Using phones, laptops, or bright screens in bed during the hour before trying to sleep",
            "Going to bed and waking up at erratic, highly inconsistent times",
            "Consuming caffeine, energy drinks, or heavy meals late in the evening",
            "Waking up feeling unrefreshed, fatigued, or needing naps to get through the day"
        ],
        "options": STANDARD_OPTIONS,
        "max_score": 15,
        "bands": [
            (4, "Healthy Habits", "Your sleep routine and lifestyle habits appear well-balanced and restorative."),
            (8, "Moderate Strain", "Some sleep disruption or lifestyle fatigue is present. Small habit adjustments can noticeably improve your energy."),
            (15, "Significant Disruption", "Marked sleep strain and irregular routines. Prioritizing sleep hygiene and consulting a health professional if issues persist is recommended.")
        ],
        "recommendations": {
            "Healthy Habits": [
                "Keep your consistent wake-up time even on weekends to anchor your circadian rhythm.",
                "Maintain daytime natural sunlight exposure within 30 minutes of waking.",
                "Keep your bedroom cool, dark, and quiet."
            ],
            "Moderate Strain": [
                "Adopt the 20-minute stimulus control rule: if unable to sleep after 20 minutes, get up and do a quiet dim activity until drowsy.",
                "Switch off screens or use blue-light filters 45–60 minutes before bedtime.",
                "Avoid caffeine after 2:00 PM to protect deep sleep architecture."
            ],
            "Significant Disruption": [
                "Establish a strict fixed morning alarm time to reset your biological clock.",
                "Create a predictable 30-minute wind-down ritual (e.g. warm shower, reading, light stretching).",
                "If chronic insomnia or unrefreshing sleep persists, discuss with a doctor to rule out medical causes."
            ]
        }
    },
    "academic": {
        "id": "academic",
        "title": "Academic & Social Pressure Screener",
        "short_title": "Academic Pressure",
        "badge": "Student Screener",
        "is_validated": False,
        "timeframe": "Over the last 2 weeks",
        "description": "Assesses student-specific workload overwhelm, performance expectations, and peer comparison.",
        "disclaimer": "This is a student-focused stress screener designed to reflect educational and social demands. It does not constitute a clinical psychological diagnosis.",
        "items": [
            "Feeling overwhelmed by coursework, impending assignment deadlines, or exam expectations",
            "Intense worry about disappointing family, mentors, or falling short of your own academic standards",
            "Comparing your progress to classmates and feeling like an impostor or that you are falling behind",
            "Sacrificing meals, sleep, or personal downtime to study or keep up with academic demands",
            "Feeling guilty or anxious whenever you take a break or try to relax"
        ],
        "options": STANDARD_OPTIONS,
        "max_score": 15,
        "bands": [
            (4, "Manageable Pressure", "You are managing academic and social expectations with reasonable balance."),
            (8, "Moderate Strain", "You are experiencing noticeable academic pressure. Setting realistic boundaries and pacing work will help prevent burnout."),
            (15, "High Overwhelm", "High academic and social strain detected. Academic stress is significantly impacting your wellbeing; seeking support and adjusting workload is advised.")
        ],
        "recommendations": {
            "Manageable Pressure": [
                "Continue using proactive calendar planning and scheduling study blocks.",
                "Celebrate completed milestones before rushing to the next assignment.",
                "Maintain hobbies outside your academic curriculum."
            ],
            "Moderate Strain": [
                "Use the Pomodoro Technique (25 min study / 5 min break) to combat fatigue.",
                "Speak with course instructors or teaching assistants during office hours early when struggling.",
                "Challenge impostor thoughts: remind yourself that social media and peers only broadcast highlights."
            ],
            "High Overwhelm": [
                "Consult your university's academic advising office or student wellbeing counselor.",
                "Explore options for deadline extensions or workload restructuring where necessary.",
                "Give yourself explicit permission to take guilt-free restorative rest—your health comes before any grade."
            ]
        }
    },
    "motivation": {
        "id": "motivation",
        "title": "Motivation & Daily Functioning Screener",
        "short_title": "Daily Motivation",
        "badge": "Wellbeing Screener",
        "is_validated": False,
        "timeframe": "Over the last 2 weeks",
        "description": "Evaluates task initiation, mental clarity, routine momentum, and behavioral engagement.",
        "disclaimer": "This screener measures daily motivation and cognitive vitality. It is an educational tool and not a clinical diagnosis.",
        "items": [
            "Difficulty starting everyday tasks, leaving responsibilities delayed until the last moment",
            "Feeling mentally foggy, sluggish, or struggling to maintain focus on single activities",
            "Feeling paralyzed by the sheer number of things you have to do",
            "Losing the sense of reward or satisfaction after completing tasks",
            "Spending extended hours stuck in bed, scrolling, or avoiding important tasks"
        ],
        "options": STANDARD_OPTIONS,
        "max_score": 15,
        "bands": [
            (4, "Steady Momentum", "Your motivation and daily routine are functioning well with healthy momentum."),
            (8, "Moderate Inertia", "Experiencing some motivational friction or task hesitation. Implementing low-friction micro-goals can help rebuild drive."),
            (15, "High Inertia & Burnout", "Significant executive fatigue or burnout patterns noted. Gentle self-compassion and breaking tasks into atomic steps is important.")
        ],
        "recommendations": {
            "Steady Momentum": [
                "Keep building on small daily wins and maintain positive morning routines.",
                "Vary your working environments (library, quiet café, desk) to stay engaged.",
                "Reflect on long-term values that inspire your daily efforts."
            ],
            "Moderate Inertia": [
                "Apply the '2-Minute Rule': commit to working on an avoided task for just 120 seconds.",
                "Write down only 3 essential tasks for tomorrow instead of an overwhelming 10-item list.",
                "Pair demanding tasks with enjoyable rewards (a favourite snack, a walk, a podcast)."
            ],
            "High Inertia & Burnout": [
                "Practice behavioral activation: pick one ridiculously tiny action (e.g. drinking water, clearing one desk corner).",
                "Recognize that burnout is a signal of depleted energy, not personal failure.",
                "Consider speaking with a counselor or academic advisor to reset expectations."
            ]
        }
    }
}


def get_category(category_id: str) -> Dict[str, Any]:
    """Retrieve full category specification by ID, defaulting to PHQ-9 if unknown."""
    return CATEGORIES.get(category_id, CATEGORIES["phq9"])


def score_assessment(category_id: str, answers: List[int], allow_skip: bool = False) -> Dict[str, Any]:
    """Score an assessment for the given category with validation and personalized guidance.

    For validated screeners (PHQ-9, GAD-7), all items must be answered.
    For non-diagnostic screeners, skipped items (None) default to 0 with a note if allow_skip is enabled.
    """
    cat = get_category(category_id)
    n_expected = len(cat["items"])

    cleaned_answers: List[int] = []
    skipped_count = 0

    for i, a in enumerate(answers):
        if a is None:
            if cat["is_validated"] or not allow_skip:
                raise ValueError(f"Question {i+1} requires an answer for this assessment.")
            cleaned_answers.append(0)
            skipped_count += 1
        else:
            try:
                val = int(a)
                if val < 0 or val > 3:
                    raise ValueError
                cleaned_answers.append(val)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid answer '{a}' for question {i+1}; must be 0–3.")

    if len(cleaned_answers) != n_expected:
        raise ValueError(f"Expected {n_expected} answers for {cat['title']}, got {len(cleaned_answers)}.")

    total = sum(cleaned_answers)
    band_name = "Minimal"
    band_guidance = ""

    for limit, name, guidance in cat["bands"]:
        if total <= limit:
            band_name = name
            band_guidance = guidance
            break
    else:
        # Fallback to the highest band
        band_name = cat["bands"][-1][1]
        band_guidance = cat["bands"][-1][2]

    recs = cat.get("recommendations", {}).get(band_name, [])

    # PHQ-9 specific safety flag: item 9 (thoughts of death or self-harm)
    item9_flag = bool(category_id == "phq9" and cleaned_answers[8] > 0)

    # General high distress trigger (score in top tier or item 9)
    high_distress = item9_flag or (total >= int(cat["max_score"] * 0.55))

    return {
        "category_id": cat["id"],
        "category_title": cat["title"],
        "short_title": cat["short_title"],
        "is_validated": cat["is_validated"],
        "total": total,
        "max_score": cat["max_score"],
        "band": band_name,
        "guidance": band_guidance,
        "recommendations": recs,
        "item9_flag": item9_flag,
        "high_distress": high_distress,
        "disclaimer": cat["disclaimer"],
        "answers": cleaned_answers,
        "skipped_count": skipped_count
    }
