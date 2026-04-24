import frappe
from frappe import _
from frappe.model.document import Document


class HRNewsletterReceipt(Document):
	def validate(self):
		self._set_defaults()
		self._validate_unique_row()

	def _set_defaults(self):
		if self.employee and not self.employee_name:
			self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
		if self.employee and not self.designation:
			self.designation = frappe.db.get_value("Employee", self.employee, "designation")

	def _validate_unique_row(self):
		if not (self.newsletter and self.employee):
			return

		existing = frappe.db.get_value(
			"HR Newsletter Receipt",
			{
				"newsletter": self.newsletter,
				"employee": self.employee,
				"name": ["!=", self.name],
			},
			"name",
		)
		if existing:
			frappe.throw(_("A receipt already exists for this employee and newsletter."))
