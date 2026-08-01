# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document


class SalarySlipLeave(Document):
	def validate(self):
		# Keep leave_days in sync with the editable leave_hours, converting using
		# the standard working hours from HR Settings (each full leave day equals
		# standard_working_hours hours).
		self.leave_days = self.get_leave_days()

	def get_leave_days(self):
		standard_hours = frappe.db.get_single_value("HR Settings", "standard_working_hours") or 8
		standard_hours = flt(standard_hours)
		if not standard_hours:
			return 0
		return flt(self.leave_hours) / standard_hours


def flt(value, precision=None):
	return frappe.utils.flt(value, precision)
