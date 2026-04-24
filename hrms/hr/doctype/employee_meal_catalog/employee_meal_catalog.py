# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class EmployeeMealCatalog(Document):
	def validate(self):
		self._validate_duplicate()
		self._validate_item_is_employee_meal()

	def _validate_duplicate(self):
		if not (self.company and self.item):
			return

		existing = frappe.db.get_value(
			"Employee Meal Catalog",
			{
				"company": self.company,
				"item": self.item,
				"name": ["!=", self.name],
			},
			"name",
		)
		if existing:
			frappe.throw(_("This food item is already added for selected company."))

	def _validate_item_is_employee_meal(self):
		if not self.item:
			return

		if frappe.db.has_column("Item", "is_employee_meal_item"):
			flag = frappe.db.get_value("Item", self.item, "is_employee_meal_item")
			if not flag:
				frappe.throw(_("Selected item is not marked as employee meal item."))
