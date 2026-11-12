# MindWatch 2.0 — Social Media Mental Wellbeing & Screening Platform

**MindWatch 2.0** is an intelligent, privacy-first, full-stack mental wellbeing platform designed for students and young adults. It analyses written text for emotional signals and language distress markers, provides multi-category validated and educational self-checks, features a context-aware supportive chat assistant with evidence-based coping exercises, tracks longitudinal emotional trajectories over time, and presents a modern SaaS dashboard.

> **Important Clinical & Ethical Disclaimer:** MindWatch 2.0 is a **screening and educational aid, NOT a diagnostic medical tool**. Language pattern analysis reflects momentary expression and cannot diagnose depression or anxiety. If you are experiencing persistent distress, please consult a qualified healthcare professional. In emergency or crisis situations, immediate human helplines (such as Tele-MANAS 14416 or 112 in India) are available 24/7.

---

## What's New in MindWatch 2.0

| Feature Area | Capabilities & Enhancements in 2.0 |
|---|---|
| **Intelligent Support Chat** | **High-priority upgrade**: Context-aware multi-turn conversational companion. Detects student concerns (academic pressure, loneliness, sleep struggles, panic, motivation). Features interactive coping workflows (Box Breathing, 5-4-3-2-1 Grounding, Cognitive Reframing, Sleep Stimulus Control, 2-Minute Rule). Backend LLM support (Google Gemini / OpenAI) with an intelligent, multi-turn local fallback engine and strict crisis escalation. |
| **Advanced Text Analysis** | Fine-grained emotional signal breakdown (Positive, Negative, Neutral language ratios, Cognitive Absolutism index, Self-Referential focus). Interpretable feature attribution explaining *why* terms influenced scores. Expanded student themes (Academic stress, Social comparison, Burnout, Sleep disruption, Panic). Comparison against user's prior post. |
| **Multi-Category Self-Checks** | Step-by-step interactive wizard (**one question per screen**) with progress tracking. Features validated **PHQ-9** (depression) & **GAD-7** (anxiety) screeners alongside dedicated non-diagnostic screeners for **Sleep & Lifestyle**, **Academic & Social Pressure**, and **Motivation & Daily Momentum**. |
| **Longitudinal Timeline Analytics** | Multi-period analytics (Daily, Weekly, Monthly) rendered with **interactive Chart.js graphs**. Date-range filtering, recurring theme frequency distributions, language signal frequencies, period comparison, and downloadable **CSV and JSON reports**. Supports analyzing saved database entries or uploaded archives (.txt, .csv, .json). |
| **Modern SaaS UI / UX** | Complete frontend redesign with a responsive sidebar layout, crisp typography, clean cards, light and dark theme adaptation, accessible forms, and bundled offline Chart.js v4. |
| **Personalized User Dashboard** | Dedicated student portal displaying recorded analyses count, latest self-check results, trajectory indicators, personalized daily coping action cards, recent activity logs, and quick actions. |
| **Database & Security Hardening** | Automatic non-destructive SQLite migrations preserving existing data, strict user isolation (`WHERE user_id = current_uid()`), password hashing via Werkzeug, CSRF tokens on all modifying routes, CSP headers, full JSON data export, and cascading account deletion. |

---

## Architecture

```
[Social Post / Journal Text]
       │
       ▼
[Language Guard (is_supported)] ────(Non-Latin)────► [UNSUPPORTED Tier + Helpline Directory]
       │
       ├────► [Crisis Safety Pre-Filter] ────────────► [CRISIS Tier + Immediate Helpline Modal]
       │
       ├────► [Lexicon & Affective Signal Engine] ──► [Positive / Negative / Neutral / Absolutism]
       │
       ├────► [Theme Classifier] ──────────────────► [Academic Stress / Sleep / Loneliness / etc.]
       │
       └────► [TF-IDF + Linear Classifier] ────────► [Language Distress Score (0.0 – 1.0)]
                                                                    │
                                                                    ▼
                                                    [Interpretable Term Attribution]
                                                    [Prior Submission Comparison]
                                                    [Personalized Coping Advice]
```

---

## Quick Start (Windows PowerShell)

### 1. Prerequisites
- Python 3.10+ (Python 3.11, 3.12, 3.13, 3.15 supported)
- Virtual environment (`.venv`)

### 2. Environment Setup
In PowerShell from the project directory:

```powershell
# Navigate to the project root
cd d:\Downloads\mindwatch-depression-detection-system\mindwatch

# If virtual environment is not yet created:
python -m venv ..\.venv

# Activate virtual environment
..\.venv\Scripts\Activate.ps1

# Install / verify dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Key configuration options:
- `SECRET_KEY`: Random string for signing sessions.
- `MINDWATCH_STORE_TEXT`: Set to `1` only if raw text persistence is explicitly consented (default is `0` for privacy).
- `GEMINI_API_KEY`: *(Optional)* Google Gemini API key for AI-assisted chat companion. If omitted, MindWatch automatically runs its built-in smart local fallback engine.
- `OPENAI_API_KEY`: *(Optional)* OpenAI API key alternative.

### 4. Run the Application
```powershell
# Run the Flask development server
python -m app.app
```
Open your browser and navigate to:
**`http://127.0.0.1:5000`**

---

## Automated Verification & Test Suite

MindWatch 2.0 includes 60 automated unit and integration tests covering all routes, security headers, machine learning inference, self-check scoring, and supportive chat logic.

To run the complete test suite:
```powershell
..\.venv\Scripts\python.exe -m unittest discover tests
```

Output:
```
Ran 60 tests in ~5s
OK
```

---

## Application Routes & Endpoints

| Route | Method | Purpose |
|---|---|---|
| `/` | `GET` | Landing page and quick social media post text analysis |
| `/analyze` | `POST` | Processes text and displays detailed visual result breakdown |
| `/api/analyze` | `POST` | REST API endpoint returning JSON analysis and assistance |
| `/self-check` | `GET` | Category selection hub for all 5 wellbeing screeners |
| `/self-check/<category_id>` | `GET, POST` | Interactive step-by-step assessment wizard (PHQ-9, GAD-7, Sleep, Academic, Motivation) |
| `/phq9` | `GET, POST` | Legacy PHQ-9 screener (100% backward-compatible) |
| `/chat` | `GET` | Intelligent support chat interface |
| `/api/chat` | `POST` | Chatbot API endpoint supporting multi-turn memory and exercise triggers |
| `/timeline` | `GET, POST` | Interactive Chart.js timeline with date filtering |
| `/timeline/load-saved` | `POST` | Loads authenticated user's saved records into the timeline |
| `/timeline/export` | `GET` | Exports timeline data as `.csv` or `.json` |
| `/dashboard` | `GET` | Personalized user dashboard (authenticated) or anonymous platform stats |
| `/history` | `GET` | Private history of text analyses and completed self-checks |
| `/settings` | `GET` | User preferences, password management, and data controls |
| `/settings/preferences` | `POST` | Updates theme and student context role |
| `/settings/password` | `POST` | Updates account password |
| `/account/export` | `GET` | Downloads user data package as JSON |
| `/account/delete` | `POST` | Permanently deletes account and cascades all linked records |
| `/resources` | `GET` | Searchable directory of emergency helplines and student support |
| `/about` | `GET` | Ethical design principles, scientific literature, and limitations |
| `/health` | `GET` | Service liveness endpoint (`{"status": "ok"}`) |

---

## Scientific Literature References

1. **PHQ-9**: Kroenke, K., Spitzer, R. L., & Williams, J. B. (2001). *The PHQ-9: validity of a brief depression severity measure.* Journal of General Internal Medicine, 16(9), 606-613.
2. **GAD-7**: Spitzer, R. L., Kroenke, K., Williams, J. B., & Löwe, B. (2006). *A brief measure for assessing generalized anxiety disorder: the GAD-7.* Archives of Internal Medicine, 166(10), 1092-1097.
3. **Pronoun & Self-Referential Focus**: Rude, S., Gortner, E. M., & Pennebaker, J. (2004). *Language use of currently and formerly depressed college students.* Cognition & Emotion, 18(6), 821-833.
4. **Absolutist Cognitive Words**: Al-Mosaiwi, M., & Johnstone, T. (2018). *In an absolute state: Elevated use of absolutist words is a marker specific to anxiety, depression, and suicidal ideation.* Clinical Psychological Science, 6(4), 529-542.

---

## Known Limitations

- **Language Scope**: Model inference operates on English (Latin-script) text. Non-Latin scripts (Tamil, Hindi, Devanagari, etc.) are safely flagged as `UNSUPPORTED` and direct users to multilingual crisis resources.
- **Social Media Context**: Short posts may lack interpersonal context, sarcasm, or situational nuance.
- **Screening vs Diagnosis**: MindWatch 2.0 strictly flags statistical language markers; it does not replace a clinical psychologist or medical doctor.
