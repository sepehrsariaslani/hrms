# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WeeklyShiftPlannerSettings(Document):
	def validate(self):
		if self.required_days_per_week <= 0:
			frappe.throw(frappe._("Required Days Per Week must be greater than 0"))
		if self.minimum_hours_per_week <= 0:
			frappe.throw(frappe._("Minimum Hours Per Week must be greater than 0"))
