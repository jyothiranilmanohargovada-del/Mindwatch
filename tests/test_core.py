import json
import unittest
from pathlib import Path

import pandas as pd

from src import chat, phq9
from src.crisis_eval import evaluate_crisis
from src.lang import is_supported
from src.predict import analyze_post
from src.preprocess import clean_text
from src.risk import crisis_assessment, detect_themes, grade, has_crisis_language
from src.timeline import analyze_timeline, parse_csv, parse_json, parse_lines, parse_upload

ROOT = Path(__file__).resolve().parent.parent


class TestPreprocess(unittest.TestCase):
    def test_clean(self):
        out = clean_text("I'm soooo sad!!! http://x.com @bob #life")
        self.assertNotIn("http", out); self.assertNotIn("@", out); self.assertIn("i am", out)

    def test_keeps_pronouns_and_negations(self):
        self.assertIn("never", clean_text("I never feel anything"))


class TestCrisis(unittest.TestCase):
    def test_positive(self):
        for t in ["I want to die", "thinking about suicide", "I keep thinking about hurting myself",
                  "i don't want to wake up", "i just want the pain to stop"]:
            self.assertTrue(has_crisis_language(t), t)

    def test_negated_and_idioms(self):
        for t in ["this exam is killing me lol", "I would never kill myself", "we watched Suicide Squad",
                  "cutting myself some slack", "suicide prevention week is next week", "that joke killed me lmao"]:
            self.assertFalse(has_crisis_language(t), t)

    def test_suppression_reason(self):
        self.assertEqual(crisis_assessment("i would never kill myself")["suppressed"], "negated")

    def test_labelled_set(self):
        r = evaluate_crisis()
        self.assertGreaterEqual(r["recall"], 0.95); self.assertGreaterEqual(r["precision"], 0.95)


class TestRiskAndThemes(unittest.TestCase):
    def test_grade_order(self):
        self.assertEqual(grade(0.01, False), "LOW"); self.assertEqual(grade(0.99, False), "HIGH")
        self.assertEqual(grade(0.01, True), "CRISIS")

    def test_themes(self):
        self.assertIn("sleep problems", detect_themes("i can't sleep at night"))
        self.assertEqual(detect_themes("had a great day"), [])


class TestLanguage(unittest.TestCase):
    def test_script(self):
        self.assertTrue(is_supported("i feel empty")); self.assertFalse(is_supported("நான் மிகவும் சோகமாக இருக்கிறேன்"))

    def test_unsupported_not_low(self):
        r = analyze_post("நான் மிகவும் சோகமாக இருக்கிறேன்")
        self.assertEqual(r["level"], "UNSUPPORTED"); self.assertIsNone(r["probability"])


class TestModel(unittest.TestCase):
    def test_ordering(self):
        sad = analyze_post("i feel empty and hopeless, nothing makes me happy and i hate myself")
        happy = analyze_post("had an amazing day at the beach with my friends, so much fun")
        self.assertGreater(sad["probability"], 0.65); self.assertLess(happy["probability"], 0.35)

    def test_hard_negative_not_crisis(self):
        self.assertNotEqual(analyze_post("i'm dead tired after the exam lol")["level"], "CRISIS")

    def test_crisis_override(self):
        self.assertEqual(analyze_post("i want to end my life")["level"], "CRISIS")

    def test_metrics_files(self):
        m = json.loads((ROOT / "reports" / "metrics.json").read_text())
        for t in m["tests"]:
            self.assertGreater(m["models"][m["deployed_model"]][t]["f1"], 0.8)
        th = json.loads((ROOT / "models" / "thresholds.json").read_text())
        self.assertLess(th["moderate"], th["high"])

    def test_dataset_splits_disjoint(self):
        d = pd.read_csv(ROOT / "data" / "posts_dataset.csv")
        tr = set(d[d.split == "train"].text)
        for s in ["iid_test", "unseen_test"]:
            self.assertFalse(tr & set(d[d.split == s].text))


class TestPHQ9(unittest.TestCase):
    def test_bands(self):
        self.assertEqual(phq9.score([0] * 9)["band"], "Minimal")
        self.assertEqual(phq9.score([1] * 9)["band"], "Mild")
        self.assertEqual(phq9.score([2] * 9)["total"], 18)
        self.assertEqual(phq9.score([3] * 9)["band"], "Severe")

    def test_item9(self):
        self.assertTrue(phq9.score([0] * 8 + [1])["item9_flag"]); self.assertFalse(phq9.score([1] * 8 + [0])["item9_flag"])

    def test_validation(self):
        for bad in ([1] * 8, [1] * 8 + [4], [1] * 8 + ["a"]):
            with self.assertRaises(ValueError):
                phq9.score(bad)


class TestChat(unittest.TestCase):
    def test_crisis_escalates(self):
        out = chat.reply("i want to kill myself", chat.start_state())
        self.assertEqual(out["level"], "CRISIS"); self.assertTrue(out["resources"])

    def test_breathing(self):
        self.assertIn("breath", chat.reply("i feel anxious, can you help me breathe", chat.start_state())["reply"].lower())

    def test_never_diagnoses(self):
        st = chat.start_state()
        for m in ["i feel empty", "i can't sleep and feel hopeless", "i feel worthless"]:
            self.assertNotIn("you have depression", chat.reply(m, st)["reply"].lower())

    def test_escalation_to_professional(self):
        st = chat.start_state()
        chat.reply("i feel empty and hopeless and worthless", st)
        out = chat.reply("everything is pointless and i hate myself", st)
        self.assertTrue(out["resources"])


class TestTimeline(unittest.TestCase):
    def setUp(self):
        self.raw = (ROOT / "data" / "sample_timeline.txt").read_text()

    def test_trend(self):
        self.assertEqual(analyze_timeline(parse_lines(self.raw))["trend"], "worsening")

    def test_csv_json_equal_lines(self):
        base = parse_lines(self.raw)
        csv_raw = "date,text\n" + "\n".join(f'{d},"{t}"' for d, t in base)
        json_raw = json.dumps([{"date": str(d), "text": t} for d, t in base])
        self.assertEqual(parse_csv(csv_raw), base); self.assertEqual(parse_json(json_raw), base)
        self.assertEqual(parse_upload("x.json", json_raw), base)

    def test_skips_non_english(self):
        out = analyze_timeline(parse_lines(self.raw) + parse_lines("2026-10-05 | நான் சோகமாக இருக்கிறேன்"))
        self.assertEqual(out["skipped"], 1)


if __name__ == "__main__":
    unittest.main()
