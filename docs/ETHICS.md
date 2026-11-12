# Ethics, safety and privacy

**Purpose.** MindWatch is a *screening aid*. It estimates whether text contains language patterns associated with
depression. It does **not** diagnose, and it can be wrong in both directions.

**Safeguards implemented**
- Explicit crisis language (rule-based, independent of the ML model) always shows help-line information.
- Text the model cannot read (non-Latin scripts) is labelled `UNSUPPORTED`, never "low risk".
- Chat assistant states it is automated, never diagnoses, escalates to help-lines on crisis language and after repeated high-risk messages.
- PHQ-9 item 9 > 0 always shows help-lines.
- Privacy by default: raw text is not stored (`MINDWATCH_STORE_TEXT=1` to override); accounts need no email; users can
  export and delete all data; passwords are hashed; CSRF protection, strict CSP and other security headers.
- Consent: only analyse your own text or text you have explicit consent to analyse. The app does not scrape social media.

**Known limitations**
- Trained/evaluated on synthetic data only by default; real-world accuracy is unknown.
- English only. Romanised or code-mixed Tamil/Hindi cannot be detected as unsupported and will be scored unreliably.
- Crisis rules are keyword based: they can miss indirect wording and over-trigger on some discussion/quotes.
- Bag-of-words models miss sarcasm and context; possible cultural/demographic bias is not audited.
- Not clinically validated. Do not use for decisions about a person's care, employment, insurance or education.
- Help-line data must be verified and localised before deployment (`data/resources.json`).

**Do not** use this system to monitor other people without their knowledge and consent.
