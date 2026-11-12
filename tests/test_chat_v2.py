"""Tests for upgraded intelligent support chat in MindWatch 2.0."""
import unittest
from src import chat


class TestChatV2(unittest.TestCase):
    def test_topic_identification(self):
        info_academic = chat.identify_student_concern("i'm so stressed about my finals and gpa")
        self.assertEqual(info_academic["primary"], "academic_stress")

        info_sleep = chat.identify_student_concern("i have insomnia and can't sleep at all")
        self.assertEqual(info_sleep["primary"], "sleep_issues")

        info_lonely = chat.identify_student_concern("i feel so isolated and alone with no friends")
        self.assertEqual(info_lonely["primary"], "loneliness")

        info_motivation = chat.identify_student_concern("i have zero motivation and procrastinating on everything")
        self.assertEqual(info_motivation["primary"], "motivation_burnout")

    def test_exercise_triggers(self):
        st = chat.start_state()

        # Box breathing
        out_b = chat.reply("can you help me with breathing", st)
        self.assertIn("box breathing", out_b["reply"].lower())

        # Grounding
        out_g = chat.reply("i need grounding", st)
        self.assertIn("5-4-3-2-1", out_g["reply"])

        # Sleep hygiene
        out_s = chat.reply("give me a sleep tip", st)
        self.assertIn("20-minute", out_s["reply"].lower())

        # Micro action rule
        out_m = chat.reply("procrastination rule", st)
        self.assertIn("2-minute", out_m["reply"].lower())

    def test_multi_turn_history(self):
        st = chat.start_state()
        chat.reply("i feel anxious about my upcoming exam", st)
        self.assertEqual(len(st["history"]), 2)  # 1 user + 1 assistant

        chat.reply("it's next tuesday and i haven't studied", st)
        self.assertEqual(len(st["history"]), 4)  # 2 user + 2 assistant
        self.assertEqual(st["turns"], 2)

    def test_local_fallback_no_clinical_claim(self):
        st = chat.start_state()
        out = chat.reply("i feel down and sad today", st)
        self.assertEqual(out["engine"], "local")
        self.assertNotIn("you have depression", out["reply"].lower())
        self.assertNotIn("i diagnose", out["reply"].lower())

    def test_crisis_override(self):
        st = chat.start_state()
        out = chat.reply("i want to end my life", st)
        self.assertEqual(out["level"], "CRISIS")
        self.assertEqual(out["engine"], "crisis_safety")
        self.assertTrue(len(out["resources"]) >= 2)


if __name__ == "__main__":
    unittest.main()
