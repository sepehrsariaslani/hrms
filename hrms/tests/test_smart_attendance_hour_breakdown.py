import unittest

from hrms.regional.iran.utils import get_smart_attendance_hours_summary


class TestSmartAttendanceHourBreakdown(unittest.TestCase):
	def test_separates_presence_break_net_overtime_and_regular_work(self):
		summary = get_smart_attendance_hours_summary(
			[
				{
					"employee": "HR-EMP-1",
					"presence_hours": 10,
					"break_hours": 1,
					"working_hours": 9,
					"overtime": 2,
				},
			],
			"HR-EMP-1",
		)

		self.assertEqual(summary.presence_hours, 10)
		self.assertEqual(summary.break_hours, 1)
		self.assertEqual(summary.net_worked_hours, 9)
		self.assertEqual(summary.overtime_hours, 2)
		self.assertEqual(summary.regular_worked_hours, 7)

	def test_regular_work_never_becomes_negative(self):
		summary = get_smart_attendance_hours_summary(
			[{"employee": "HR-EMP-1", "presence_hours": 2, "break_hours": 0, "working_hours": 2, "overtime": 3}],
			"HR-EMP-1",
		)

		self.assertEqual(summary.regular_worked_hours, 0)
