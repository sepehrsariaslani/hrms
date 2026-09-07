import unittest

from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip


class TestEmployerInsuranceShare(unittest.TestCase):
	def test_employee_insurance_deduction_overrides_stale_stored_employer_share(self):
		salary_slip = SalarySlip(
			{
				"doctype": "Salary Slip",
				"employer_insurance_share_iran": 1,
				"deductions": [{"abbr": "EI", "amount": 7000}],
			}
		)

		self.assertEqual(salary_slip.get_employer_insurance_share(), 23000)

	def test_stored_employer_share_is_used_when_employee_insurance_is_absent(self):
		salary_slip = SalarySlip(
			{"doctype": "Salary Slip", "employer_insurance_share_iran": 23000, "deductions": []}
		)

		self.assertEqual(salary_slip.get_employer_insurance_share(), 23000)

	def test_sync_updates_stored_employer_share_after_final_deductions(self):
		salary_slip = SalarySlip(
			{
				"doctype": "Salary Slip",
				"employer_insurance_share_iran": 1,
				"deductions": [{"abbr": "EI", "amount": 7000}],
			}
		)

		salary_slip.sync_employer_insurance_share()

		self.assertEqual(salary_slip.employer_insurance_share_iran, 23000)
