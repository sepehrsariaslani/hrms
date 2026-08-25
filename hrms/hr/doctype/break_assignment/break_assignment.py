# Copyright (c) 2026, Iran Utilities and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form

from hrms.hr.utils import validate_active_employee


class BreakAssignment(Document):
	def validate(self):
		validate_active_employee(self.employee)
		if self.to_date:
			self.validate_from_to_dates("from_date", "to_date")
		self.validate_overlapping_assignments()

	def on_update_after_submit(self):
		if self.to_date:
			self.validate_from_to_dates("from_date", "to_date")
		self.validate_overlapping_assignments()

	def validate_overlapping_assignments(self):
		if self.status == "Inactive":
			return

		self_end = self.to_date or "2199-12-31"
		overlap = frappe.db.sql(
			"""
			SELECT name
			FROM `tabBreak Assignment`
			WHERE employee = %(employee)s
			  AND break_hours = %(break_hours)s
			  AND docstatus = 1
			  AND status = 'Active'
			  AND name != %(name)s
			  AND from_date <= %(self_end)s
			  AND (to_date IS NULL OR to_date >= %(self_start)s)
			LIMIT 1
			""",
			{
				"employee": self.employee,
				"break_hours": self.break_hours,
				"name": self.name or "",
				"self_start": self.from_date,
				"self_end": self_end,
			},
			as_dict=True,
		)

		if overlap:
			frappe.throw(
				_("Employee {0} already has an active assignment for {1}: {2}").format(
					frappe.bold(self.employee),
					frappe.bold(self.break_hours),
					get_link_to_form("Break Assignment", overlap[0].name),
				),
				title=_("Overlapping Break Assignment"),
			)
