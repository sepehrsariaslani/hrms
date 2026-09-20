import unittest

import frappe

from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip


class TestAdditionalSalaryComponentAggregation(unittest.TestCase):
	def test_refresh_removes_previous_additional_salary_rows_before_rebuilding(self):
		salary_slip = SalarySlip(
			{
				"doctype": "Salary Slip",
				"deductions": [
					{"salary_component": "کسری صندوق", "additional_salary": "HR-ADS-1"},
					{"salary_component": "بیمه سهم کارمند"},
				],
			}
		)

		salary_slip.clear_additional_salary_component_rows("deductions")

		self.assertEqual([row.salary_component for row in salary_slip.deductions], ["بیمه سهم کارمند"])

	def test_cashier_reconciliation_additional_salary_is_aggregated(self):
		additional_salary = frappe._dict(
			{
				"overwrite": 0,
				"is_recurring": 0,
				"ref_doctype": "Cashier Reconciliation",
			}
		)
		component = frappe._dict(
			{
				"variable_based_on_taxable_salary": 0,
				"accrual_component": 0,
				"is_flexible_benefit": 0,
			}
		)

		self.assertTrue(SalarySlip.should_aggregate_additional_salary(None, additional_salary, component))

	def test_financially_sensitive_reference_stays_separate(self):
		additional_salary = frappe._dict(
			{
				"overwrite": 0,
				"is_recurring": 0,
				"ref_doctype": "Payroll Correction",
			}
		)
		component = frappe._dict(
			{
				"variable_based_on_taxable_salary": 0,
				"accrual_component": 0,
				"is_flexible_benefit": 0,
			}
		)

		self.assertFalse(SalarySlip.should_aggregate_additional_salary(None, additional_salary, component))
