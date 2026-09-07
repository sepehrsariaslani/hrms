import unittest

from hrms.hr.report.smart_attendance_report.smart_attendance_report import (
	calculate_break_hours_for_pairs,
)


class TestPresenceHours(unittest.TestCase):
	def test_presence_uses_the_sum_of_all_completed_entry_exit_pairs(self):
		pairs = [
			{"in_seconds": 8 * 3600, "out_seconds": 12 * 3600, "duration_seconds": 4 * 3600},
			{"in_seconds": 13 * 3600, "out_seconds": 17 * 3600, "duration_seconds": 4 * 3600},
		]
		lunch_break = [
			{
				"calculation_type": "Time Window",
				"start": 12 * 3600,
				"end": 13 * 3600,
				"deduction_seconds": 3600,
			}
		]

		self.assertEqual(calculate_break_hours_for_pairs(pairs, lunch_break), 0)
		self.assertEqual(sum(pair["duration_seconds"] for pair in pairs) / 3600, 8)
