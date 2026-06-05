# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class EmployeeDeskVisibility(Document):
	def validate(self):
		self._validate_scope()
		self._validate_active_uniqueness()
		self._set_title()

	def _validate_scope(self):
		if self.is_default:
			self.company = None

		if not self.company and not self.is_default:
			frappe.throw(_("Set a Company or mark this profile as Default."))

	def _validate_active_uniqueness(self):
		if not self.is_active:
			return

		if self.company:
			filters = {
				"name": ["!=", self.name],
				"is_active": 1,
				"company": self.company,
			}
			if frappe.db.exists("Employee Desk Visibility", filters):
				frappe.throw(_("Only one active profile is allowed per company."))
			return

		if self.is_default:
			filters = {
				"name": ["!=", self.name],
				"is_active": 1,
				"is_default": 1,
			}
			if frappe.db.exists("Employee Desk Visibility", filters):
				frappe.throw(_("Only one active default profile is allowed."))

	def _set_title(self):
		if self.company:
			self.title = _("Employee Desk Visibility - {0}").format(self.company)
		elif self.is_default:
			self.title = _("Employee Desk Visibility - Default")
		else:
			self.title = _("Employee Desk Visibility")
