import unittest

import frappe


class TestHourlyPenaltyConfiguration(unittest.TestCase):
	def test_every_active_structure_has_one_hourly_penalty_deduction(self):
		component = frappe.db.get_value(
			"Salary Component",
			"جریمه ساعتی",
			["type", "salary_component_abbr", "amount_based_on_formula", "formula"],
			as_dict=True,
		)
		self.assertIsNotNone(component)
		self.assertEqual(component.type, "Deduction")
		self.assertEqual(component.salary_component_abbr, "HRDH")
		self.assertFalse(component.amount_based_on_formula)
		self.assertFalse(component.formula)

		for name in frappe.get_all(
			"Salary Structure",
			filters={"company": "عظیمیه", "is_active": "Yes", "docstatus": ["!=", 2]},
			pluck="name",
		):
			structure = frappe.get_doc("Salary Structure", name)
			self.assertEqual(
				sum(row.salary_component == "جریمه ساعتی" for row in structure.deductions),
				1,
				name,
			)
