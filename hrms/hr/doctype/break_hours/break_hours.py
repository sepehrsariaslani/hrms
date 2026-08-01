# Copyright (c) 2026, Iran Utilities and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_time


class BreakHours(Document):
	def validate(self):
		if not self.calculation_type:
			self.calculation_type = "Time Window"
		self.validate_break_window()
		self.validate_deduction_hours()
		self.validate_fixed_break_rules()

	def validate_break_window(self):
		if self.calculation_type == "Fixed by Worked Hours":
			return
		if not self.break_start or not self.break_end:
			frappe.throw(_("Break start and end time are required for time window breaks."))

		start_seconds = _time_to_seconds(self.break_start)
		end_seconds = _time_to_seconds(self.break_end)

		if start_seconds == end_seconds:
			frappe.throw(_("Break start and end time cannot be equal."))

	def validate_deduction_hours(self):
		if self.calculation_type == "Fixed by Worked Hours":
			return
		deduction_hours = flt(self.deduction_hours)
		if deduction_hours <= 0:
			frappe.throw(_("Deduction hours must be greater than zero."))

		window_hours = self.get_break_window_hours()
		if window_hours and deduction_hours > window_hours:
			frappe.throw(_("Deduction hours cannot be greater than break window hours ({0}).").format(window_hours))

	def get_break_window_hours(self) -> float:
		if self.calculation_type == "Fixed by Worked Hours":
			return 0
		if not self.break_start or not self.break_end:
			return 0

		start_seconds = _time_to_seconds(self.break_start)
		end_seconds = _time_to_seconds(self.break_end)
		if end_seconds <= start_seconds:
			end_seconds += 24 * 3600

		return flt((end_seconds - start_seconds) / 3600, 4)

	def validate_fixed_break_rules(self):
		if self.calculation_type != "Fixed by Worked Hours":
			return

		rules = list(self.get("fixed_break_rules") or [])
		if not rules:
			frappe.throw(_("At least one fixed break rule is required."))

		seen_thresholds = set()
		for rule in rules:
			minimum_work_hours = flt(rule.minimum_work_hours)
			deduction_hours = flt(rule.deduction_hours)
			if minimum_work_hours <= 0:
				frappe.throw(_("Minimum work hours must be greater than zero."))
			if deduction_hours <= 0:
				frappe.throw(_("Deduction hours must be greater than zero."))
			if deduction_hours > minimum_work_hours:
				frappe.throw(_("Deduction hours cannot be greater than minimum work hours."))
			if minimum_work_hours in seen_thresholds:
				frappe.throw(_("Minimum work hours must be unique for fixed break rules."))
			seen_thresholds.add(minimum_work_hours)


def _time_to_seconds(time_value) -> int:
	time_obj = get_time(time_value)
	return (time_obj.hour * 3600) + (time_obj.minute * 60) + time_obj.second
