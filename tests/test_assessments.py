"""Tests for multi-category self-check assessments in MindWatch 2.0."""
import unittest
from src import assessments


class TestAssessments(unittest.TestCase):
    def test_phq9_scoring_and_bands(self):
        # All zeros -> Minimal
        r = assessments.score_assessment("phq9", [0] * 9)
        self.assertEqual(r["total"], 0)
        self.assertEqual(r["band"], "Minimal")
        self.assertFalse(r["item9_flag"])

        # Mild band (score 5-9)
        r_mild = assessments.score_assessment("phq9", [1] * 7 + [0] * 2)
        self.assertEqual(r_mild["total"], 7)
        self.assertEqual(r_mild["band"], "Mild")

        # Moderate band (score 10-14)
        r_mod = assessments.score_assessment("phq9", [2] * 6 + [0] * 3)
        self.assertEqual(r_mod["total"], 12)
        self.assertEqual(r_mod["band"], "Moderate")

        # Moderately Severe band (score 15-19)
        r_mod_sev = assessments.score_assessment("phq9", [2] * 8 + [0])
        self.assertEqual(r_mod_sev["total"], 16)
        self.assertEqual(r_mod_sev["band"], "Moderately Severe")

        # Severe band (score 20-27)
        r_sev = assessments.score_assessment("phq9", [3] * 9)
        self.assertEqual(r_sev["total"], 27)
        self.assertEqual(r_sev["band"], "Severe")
        self.assertTrue(r_sev["item9_flag"])

    def test_phq9_item9_flag(self):
        # Item 9 > 0 triggers safety flag even with total < 5
        r = assessments.score_assessment("phq9", [0] * 8 + [1])
        self.assertTrue(r["item9_flag"])
        self.assertTrue(r["high_distress"])

    def test_gad7_scoring_and_bands(self):
        # All zeros -> Minimal (0-4)
        r0 = assessments.score_assessment("gad7", [0] * 7)
        self.assertEqual(r0["total"], 0)
        self.assertEqual(r0["band"], "Minimal")

        # Mild (5-9)
        r_mild = assessments.score_assessment("gad7", [1] * 6 + [0])
        self.assertEqual(r_mild["total"], 6)
        self.assertEqual(r_mild["band"], "Mild")

        # Moderate (10-14)
        r_mod = assessments.score_assessment("gad7", [2] * 6 + [0])
        self.assertEqual(r_mod["total"], 12)
        self.assertEqual(r_mod["band"], "Moderate")

        # Severe (15-21)
        r_sev = assessments.score_assessment("gad7", [3] * 7)
        self.assertEqual(r_sev["total"], 21)
        self.assertEqual(r_sev["band"], "Severe")

    def test_sleep_screener(self):
        r = assessments.score_assessment("sleep", [0, 1, 1, 0, 1])
        self.assertEqual(r["total"], 3)
        self.assertEqual(r["band"], "Healthy Habits")
        self.assertFalse(r["is_validated"])

        r_strain = assessments.score_assessment("sleep", [3, 2, 3, 2, 3])
        self.assertEqual(r_strain["band"], "Significant Disruption")

    def test_academic_pressure_screener(self):
        r = assessments.score_assessment("academic", [2, 2, 2, 1, 0])
        self.assertEqual(r["total"], 7)
        self.assertEqual(r["band"], "Moderate Strain")
        self.assertIn("Pomodoro", " ".join(r["recommendations"]))

    def test_motivation_screener(self):
        r = assessments.score_assessment("motivation", [3, 3, 2, 3, 2])
        self.assertEqual(r["total"], 13)
        self.assertEqual(r["band"], "High Inertia & Burnout")

    def test_skip_handling(self):
        # Validated instruments MUST NOT allow skip
        with self.assertRaises(ValueError):
            assessments.score_assessment("phq9", [1, None, 1, 1, 1, 1, 1, 1, 0], allow_skip=True)

        with self.assertRaises(ValueError):
            assessments.score_assessment("gad7", [1, None, 1, 1, 1, 1, 0], allow_skip=True)

        # Custom screeners CAN allow skip (defaults skipped item to 0)
        r = assessments.score_assessment("academic", [2, None, 1, None, 0], allow_skip=True)
        self.assertEqual(r["answers"], [2, 0, 1, 0, 0])
        self.assertEqual(r["skipped_count"], 2)

    def test_validation_bounds(self):
        with self.assertRaises(ValueError):
            assessments.score_assessment("gad7", [1, 2, 3, 4, 0, 0, 0])  # 4 is out of bounds (0-3)

        with self.assertRaises(ValueError):
            assessments.score_assessment("gad7", [1, 2, 3])  # Too few answers


if __name__ == "__main__":
    unittest.main()
