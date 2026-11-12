# Architecture

```
text -> language check -> cleaning -> TF-IDF (1-2 grams) + 6 linguistic features -> Logistic Regression -> P(depressive)
                     \-> crisis rules (negation / idiom aware) ------------------------------------------\
                                                                                                           v
                              risk grading (tuned thresholds) + symptom themes + explanation -> assistance (tips, help-lines)
                                                                                                           |
          Flask UI + REST API  <-- accounts (hashed pw), history, export/delete, PHQ-9, support chat, timeline (txt/csv/json)
                                                                                                           |
                                                                                             SQLite (no raw text by default)
```
| Module | File |
|---|---|
| Config, tuned thresholds | `config.py`, `models/thresholds.json` |
| Cleaning (keeps pronouns/negations) | `src/preprocess.py` |
| Linguistic features | `src/features.py` |
| Pipeline / candidate models | `src/model.py` |
| Training, CV, ablation, threshold tuning, figures | `src/train.py` |
| Synthetic data (train / iid_test / unseen_test) | `src/generate_sample_data.py` |
| Crisis rules + themes + grading | `src/risk.py`, `src/crisis_eval.py` |
| Language guard | `src/lang.py` |
| Inference + explanation | `src/predict.py` |
| Assistance, PHQ-9, chat | `src/assistant.py`, `src/phq9.py`, `src/chat.py` |
| Timeline + import | `src/timeline.py` |
| Web app / DB | `app/app.py`, `app/db.py`, `app/templates/` |
| Optional transformer baseline | `src/transformer_baseline.py` |

Threshold tuning uses out-of-fold predictions on the training data only: MODERATE = max F2 (recall-weighted),
HIGH = lowest threshold with precision >= 0.90 (clamped).
