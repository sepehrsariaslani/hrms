# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class JobGrade(Document):
	def validate(self):
		self.validate_score_range()
		self.calculate_max_salary()

	def validate_score_range(self):
		if flt(self.max_score) and flt(self.min_score) and flt(self.max_score) < flt(self.min_score):
			frappe.throw(_("حداکثر امتیاز باید بزرگ‌تر یا مساوی حداقل امتیاز باشد."))

	def calculate_max_salary(self):
		if self.min_salary is None:
			self.max_salary = 0
			return

		spread = flt(self.spread_percent)
		if spread < 0:
			frappe.throw(_("اسپرد حقوقی نمی‌تواند منفی باشد."))

		self.max_salary = flt(self.min_salary) * (1 + spread / 100)

