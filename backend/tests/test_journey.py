import sys
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "api"))
sys.path.insert(0, str(ROOT / "backend" / "ai_core"))
sys.path.insert(0, str(ROOT / "backend" / "database"))

from demo import appointment_is_expired  # noqa: E402
from process_kb import JourneyState, PROCESS_STEPS  # noqa: E402


class JourneyRulesTests(unittest.TestCase):
    def test_appointment_slot_expiry(self):
        now = datetime(2026, 10, 17, 12, 0)
        self.assertTrue(appointment_is_expired("2026-10-16", "晚上", now))
        self.assertTrue(appointment_is_expired("2026-10-17", "上午", now))
        self.assertFalse(appointment_is_expired("2026-10-17", "下午", now))
        self.assertFalse(appointment_is_expired("2026-10-18", "上午", now))

    def test_finish_marks_last_step_and_state(self):
        state = JourneyState("erke", [])
        state.current = len(PROCESS_STEPS) - 1
        state.finish()
        self.assertTrue(state.is_finished())
        self.assertIn(PROCESS_STEPS[-1]["key"], state.done_keys)

    def test_evening_label_variants_are_not_expired_before_nine(self):
        now = datetime(2026, 10, 17, 20, 59)
        self.assertFalse(appointment_is_expired("2026-10-17", "晚上时段", now))
        self.assertTrue(appointment_is_expired("2026-10-17", "晚间", datetime(2026, 10, 17, 21, 0)))

    def test_unknown_slot_does_not_expire_at_midnight(self):
        now = datetime(2026, 10, 17, 15, 0)
        self.assertFalse(appointment_is_expired("2026-10-17", "晚间预约", now))


if __name__ == "__main__":
    unittest.main()
