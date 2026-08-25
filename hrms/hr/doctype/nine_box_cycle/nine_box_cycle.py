# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class NineBoxCycle(Document):
	def validate(self):
		self.validate_thresholds()

	def validate_thresholds(self):
		scale = flt(self.score_scale_max) or 100
		perf_low = flt(self.performance_low_max)
		perf_mid = flt(self.performance_medium_max)
		pot_low = flt(self.potential_low_max)
		pot_mid = flt(self.potential_medium_max)

		if not (0 <= perf_low <= perf_mid <= scale):
			frappe.throw(_("آستانه‌های عملکرد باید بین 0 تا مقیاس امتیاز و به‌ترتیب صعودی باشند."))
		if not (0 <= pot_low <= pot_mid <= scale):
			frappe.throw(_("آستانه‌های پتانسیل باید بین 0 تا مقیاس امتیاز و به‌ترتیب صعودی باشند."))

