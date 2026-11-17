# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

VALID_STATUSES = {"Not Required", "Reserved", "Delivered"}


def _run_reservation_write_barrier(query, values):
	try:
		frappe.db.sql(query, values)
	except Exception as error:
		if getattr(error, "pgcode", None) == "40001":
			frappe.throw(_("A meal reservation changed while this request was being saved. Please try again."))
		raise


class MealReservation(Document):
	def validate(self):
		self._set_defaults()
		self._validate_unique_row()
		self._validate_status()
		self._validate_portion_capacity()

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

		from hrms.hr.doctype.meal_weekly_plan.meal_rules import (
			ACTIVE_RESERVATION_STATUSES,
			can_activate_reservation,
		)
		from hrms.hr.doctype.meal_weekly_plan.reservation_locking import employee_day_write_barrier

		if self.reservation_status in ACTIVE_RESERVATION_STATUSES and self.company:
			# A no-op UPDATE creates a conflicting row version on PostgreSQL. A
			# concurrent Repeatable Read transaction with an older snapshot then
			# fails with serialization failure instead of validating stale counts.
			query, values = employee_day_write_barrier(self.employee)
			_run_reservation_write_barrier(query, values)

			active_statuses = tuple(ACTIVE_RESERVATION_STATUSES)
			status_placeholders = ", ".join(["%s"] * len(active_statuses))
			active_rows = frappe.db.sql(
				f"""select reservation_status from `tabMeal Reservation`
					where company=%s and employee=%s and reservation_date=%s
					and reservation_status in ({status_placeholders}) and name != %s
					order by name limit 1 for update""",
				(self.company, self.employee, self.reservation_date, *active_statuses, self.name or ""),
				as_dict=True,
			)
			if not can_activate_reservation(
				[row.get("reservation_status") for row in active_rows], self.reservation_status
			):
				frappe.throw(_("Only one lunch may be reserved per employee, company, and day."))

	def _validate_portion_capacity(self):
		from hrms.hr.doctype.meal_weekly_plan.meal_rules import (
			ACTIVE_RESERVATION_STATUSES,
			has_portion_capacity,
			retains_existing_portion_claim,
		)
		from hrms.hr.doctype.meal_weekly_plan.reservation_locking import plan_day_write_barrier

		if not (self.meal_plan and self.reservation_date and self.reservation_status in ACTIVE_RESERVATION_STATUSES):
			return

		previous = None
		if self.name and frappe.db.exists("Meal Reservation", self.name):
			previous = frappe.db.get_value(
				"Meal Reservation",
				self.name,
				["reservation_status", "meal_plan", "reservation_date"],
				as_dict=True,
			)
		already_reserved = retains_existing_portion_claim(
			previous_status=previous.get("reservation_status") if previous else None,
			previous_plan=previous.get("meal_plan") if previous else None,
			previous_date=previous.get("reservation_date") if previous else None,
			plan=self.meal_plan,
			meal_date=self.reservation_date,
		)

		query, values = plan_day_write_barrier(self.meal_plan, self.reservation_date)
		_run_reservation_write_barrier(query, values)
		plan_item = frappe.db.get_value(
			"Meal Weekly Plan Item",
			{"parent": self.meal_plan, "meal_date": self.reservation_date},
			["max_portions"],
			as_dict=True,
		)
		if not plan_item:
			return

		active_statuses = tuple(ACTIVE_RESERVATION_STATUSES)
		status_placeholders = ", ".join(["%s"] * len(active_statuses))
		reserved_rows = frappe.db.sql(
			f"""select name from `tabMeal Reservation`
				where meal_plan=%s and reservation_date=%s
				and reservation_status in ({status_placeholders}) and name != %s
				order by name for update""",
			(self.meal_plan, self.reservation_date, *active_statuses, self.name or ""),
		)
		reserved_count = len(reserved_rows)
		if not has_portion_capacity(reserved_count, plan_item.get("max_portions"), already_reserved=already_reserved):
			frappe.throw(_("The meal plan has reached its maximum portions for this day."))

	def _validate_status(self):
		if self.reservation_status not in VALID_STATUSES:
			frappe.throw(_("Invalid reservation status: {0}").format(self.reservation_status))
