import unittest

from hrms.hr.doctype.attendance_break_override.attendance_break_override import (
	get_effective_break_minutes,
)


class TestAttendanceBreakOverride(unittest.TestCase):
	def test_manual_final_minutes_replace_policy_minutes(self):
		self.assertEqual(get_effective_break_minutes(60, None), 60)
		self.assertEqual(get_effective_break_minutes(60, 0), 0)
		self.assertEqual(get_effective_break_minutes(60, 30), 30)
		self.assertEqual(get_effective_break_minutes(60, 120), 120)

	def test_effective_break_is_never_negative(self):
		self.assertEqual(get_effective_break_minutes(60, -1), 0)
