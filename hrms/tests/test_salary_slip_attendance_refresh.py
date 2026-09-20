import unittest
from unittest.mock import patch

from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip


class TestSalarySlipAttendanceRefresh(unittest.TestCase):
	def test_attendance_summary_is_loaded_before_salary_structure_formulas(self):
		class DraftSlip:
			docstatus = 0
			employee = "HR-EMP-TEST"
			start_date = "2026-05-22"
			end_date = "2026-06-21"

			def __init__(self):
				self.summary_loaded = False

			def process_salary_structure(self):
				self.assert_true(self.summary_loaded)

			def add_leave_balances(self):
				pass

			def save(self, **kwargs):
				pass

			def assert_true(self, value):
				if not value:
					raise AssertionError("attendance summary must be populated before formulas")

		draft = DraftSlip()

		def load_summary(doc):
			doc.summary_loaded = True

		with patch("hrms.regional.iran.utils.apply_smart_attendance_summary", side_effect=load_summary):
			result = SalarySlip.refresh_from_smart_attendance(draft)

		self.assertTrue(result["success"])
