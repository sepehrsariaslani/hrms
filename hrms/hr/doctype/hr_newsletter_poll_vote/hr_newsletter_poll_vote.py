import frappe
from frappe import _
from frappe.model.document import Document


class HRNewsletterPollVote(Document):
	def validate(self):
		self._set_defaults()
		self._validate_unique_vote()

	def _set_defaults(self):
		if self.employee and not self.employee_name:
			self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")

	def _validate_unique_vote(self):
		if not (self.poll and self.employee and self.option):
			return

		existing = frappe.db.get_value(
			"HR Newsletter Poll Vote",
			{
				"poll": self.poll,
				"employee": self.employee,
				"option": self.option,
				"name": ["!=", self.name],
			},
			"name",
		)
		if existing:
			frappe.throw(_("You already voted for this option."))

