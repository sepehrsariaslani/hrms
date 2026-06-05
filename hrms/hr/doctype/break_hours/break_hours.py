# Copyright (c) 2026, Iran Utilities and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_time


class BreakHours(Document):
	def validate(self):
		self.validate_break_window()
		self.validate_deduction_hours()

	def validate_break_window(self):
		if not self.break_start or not self.break_end:
			return

		start_seconds = _time_to_seconds(self.break_start)
		end_seconds = _time_to_seconds(self.break_end)

		if start_seconds == end_seconds:
			frappe.throw(_("Break start and end time cannot be equal."))

	def validate_deduction_hours(self):
		deduction_hours = flt(self.deduction_hours)
		if deduction_hours <= 0:
			frappe.throw(_("Deduction hours must be greater than zero."))

		window_hours = self.get_break_window_hours()
		if window_hours and deduction_hours > window_hours:
			frappe.throw(_("Deduction hours cannot be greater than break window hours ({0}).").format(window_hours))

	def get_break_window_hours(self) -> float:
		if not self.break_start or not self.break_end:
			return 0

		start_seconds = _time_to_seconds(self.break_start)
		end_seconds = _time_to_seconds(self.break_end)
		if end_seconds <= start_seconds:
			end_seconds += 24 * 3600

		return flt((end_seconds - start_seconds) / 3600, 4)


def _time_to_seconds(time_value) -> int:
	time_obj = get_time(time_value)
	return (time_obj.hour * 3600) + (time_obj.minute * 60) + time_obj.second
