# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

VALID_STATUSES = {"Not Required", "Reserved", "Delivered"}


class MealReservation(Document):
	def validate(self):
		self._set_defaults()
		self._validate_unique_row()
		self._validate_status()

	def _set_defaults(self):
		if self.employee and not self.company:
			self.company = frappe.db.get_value("Employee", self.employee, "company")

		if self.employee and not self.employee_name:
			self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")

		if self.meal_item and not self.meal_title:
			self.meal_title = frappe.db.get_value("Item", self.meal_item, "item_name")

		if self.reservation_status != "Delivered":
			self.delivered_on = None
			self.delivered_by = None

		self.last_updated_by_user = frappe.session.user

	def _validate_unique_row(self):
		if not (self.meal_plan and self.employee and self.reservation_date):
			return

		existing = frappe.db.get_value(
			"Meal Reservation",
			{
				"meal_plan": self.meal_plan,
				"employee": self.employee,
				"reservation_date": self.reservation_date,
				"name": ["!=", self.name],
			},
			"name",
		)
		if existing:
			frappe.throw(_("Reservation already exists for this employee and date."))

	def _validate_status(self):
		if self.reservation_status not in VALID_STATUSES:
			frappe.throw(_("Invalid reservation status: {0}").format(self.reservation_status))
