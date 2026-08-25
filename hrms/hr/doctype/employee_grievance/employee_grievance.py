# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, bold
from frappe.model.document import Document
from frappe.utils import getdate


class EmployeeGrievance(Document):
	def validate(self):
		self.set_default_employee_details()
		self.set_default_feedback_values()

	def on_submit(self):
		if self.status not in ["Invalid", "Resolved"]:
			frappe.throw(
				_("Only Employee Grievance with status {0} or {1} can be submitted").format(
					bold("Invalid"), bold("Resolved")
				)
			)

	def set_default_employee_details(self):
		if not self.date:
			self.date = getdate()

		if not self.raised_by:
			self.raised_by = frappe.db.get_value(
				"Employee",
				{"user_id": frappe.session.user, "status": "Active"},
				"name",
			)

		if not self.raised_by:
			frappe.throw(_("Please select the employee who raised this grievance."))

		employee_details = frappe.db.get_value(
			"Employee",
			self.raised_by,
			["employee_name", "designation", "reports_to"],
			as_dict=True,
		)
		if not employee_details:
			frappe.throw(_("Employee {0} was not found.").format(bold(self.raised_by)))

		self.employee_name = employee_details.employee_name
		self.designation = employee_details.designation
		self.reports_to = employee_details.reports_to

	def set_default_feedback_values(self):
		if frappe.db.has_column("Employee Grievance", "feedback_type") and not self.feedback_type:
			self.feedback_type = "انتقاد"

		if not self.grievance_type:
			default_grievance_type = "سایر موارد"
			if not frappe.db.exists("Grievance Type", default_grievance_type):
				default_grievance_type = frappe.db.get_value("Grievance Type", {}, "name", order_by="name asc")
			self.grievance_type = default_grievance_type

		if not self.grievance_against_party:
			self.grievance_against_party = "Employee"

		if not self.grievance_against:
			self.grievance_against = self.reports_to or self.raised_by
