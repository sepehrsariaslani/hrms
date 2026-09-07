import ast
import unittest
from pathlib import Path


SALARY_SLIP_PATH = (
	Path(__file__).resolve().parents[1] / "payroll" / "doctype" / "salary_slip" / "salary_slip.py"
)


class TestSalarySlipClassStructure(unittest.TestCase):
	def test_date_validation_remains_a_salary_slip_method(self):
		tree = ast.parse(SALARY_SLIP_PATH.read_text(encoding="utf-8"))
		salary_slip = next(
			node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "SalarySlip"
		)

		self.assertTrue(
			any(isinstance(node, ast.FunctionDef) and node.name == "validate_dates" for node in salary_slip.body)
		)
