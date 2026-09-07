import ast
import unittest
from pathlib import Path


SALARY_SLIP_PATH = (
	Path(__file__).resolve().parents[1] / "payroll" / "doctype" / "salary_slip" / "salary_slip.py"
)


class TestZeroAmountHourlyAdditionalSalarySummary(unittest.TestCase):
	def test_zero_amount_hourly_earning_is_counted_in_summary(self):
		tree = ast.parse(SALARY_SLIP_PATH.read_text(encoding="utf-8"))
		klass = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "SalarySlip")
		method = next(
			node
			for node in klass.body
			if isinstance(node, ast.FunctionDef) and node.name == "add_additional_salary_components"
		)
		accumulate_line = next(
			node.lineno
			for node in ast.walk(method)
			if isinstance(node, ast.Call)
			and isinstance(node.func, ast.Attribute)
			and node.func.attr == "accumulate_additional_salary_hours"
		)
		zero_value_skip_line = next(
			node.lineno
			for node in ast.walk(method)
			if isinstance(node, ast.If)
			and "remove_if_zero_valued" in ast.unparse(node.test)
		)

		self.assertLess(accumulate_line, zero_value_skip_line)

	def test_earnings_recalculation_resets_hourly_summary(self):
		from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

		salary_slip = SalarySlip(
			{
				"doctype": "Salary Slip",
				"additional_earning_hours": 45,
				"additional_deduction_hours": 0,
				"additional_overtime_hours": 0,
				"additional_ordinary_hours": 0,
			}
		)
		salary_slip._additional_salary_hours_summary_initialized = True

		salary_slip.initialize_additional_salary_hours_summary("earnings")

		self.assertEqual(salary_slip.additional_earning_hours, 0)
