# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class NineBoxAssessment(Document):
	def validate(self):
		self.set_employee_context()
		self.set_scores_from_links()
		self.set_nine_box_result()

	def set_employee_context(self):
		if not self.employee:
			return

		employee = frappe.get_doc("Employee", self.employee)
		self.employee_name = employee.employee_name
		self.company = employee.company
		self.department = employee.department
		self.designation = employee.designation

	def set_scores_from_links(self):
		if self.appraisal and not self.performance_score:
			score = flt(frappe.db.get_value("Appraisal", self.appraisal, "final_score"))
			self.performance_score = self.normalize_score(score)

		if self.competency_assessment and not self.potential_score:
			score = flt(frappe.db.get_value("Competency Assessment", self.competency_assessment, "average_current_level"))
			self.potential_score = self.normalize_score(score)

	def normalize_score(self, score):
		scale = self.get_scale_max()
		score = flt(score)
		if score <= 5 and scale > 10:
			return score * (scale / 5)
		return score

	def get_scale_max(self):
		if not self.cycle:
			return 100
		return flt(frappe.db.get_value("Nine Box Cycle", self.cycle, "score_scale_max")) or 100

	def set_nine_box_result(self):
		if not self.cycle:
			return

		cycle = frappe.get_doc("Nine Box Cycle", self.cycle)
		perf_band = self.get_band(
			flt(self.performance_score),
			flt(cycle.performance_low_max),
			flt(cycle.performance_medium_max),
		)
		pot_band = self.get_band(
			flt(self.potential_score),
			flt(cycle.potential_low_max),
			flt(cycle.potential_medium_max),
		)

		box_number, box_label, recommended_path = self.map_box(pot_band, perf_band)
		self.box_code = str(box_number)
		self.box_label = box_label
		self.recommended_path = recommended_path

	def get_band(self, value, low_max, medium_max):
		if value <= low_max:
			return "low"
		if value <= medium_max:
			return "medium"
		return "high"

	def map_box(self, potential_band, performance_band):
		mapping = {
			("high", "high"): (
				9,
				"ستاره‌ها (عملکرد بالا / پتانسیل بالا)",
				"عمودی (مسیر مدیریتی و جانشین‌پروری)",
			),
			("high", "medium"): (8, "پتانسیل بالا با عملکرد رو‌به‌رشد", "ترکیبی (آماده‌سازی ارتقا)"),
			("high", "low"): (7, "پتانسیل بالا با عملکرد پایین", "بهبود عملکرد + کوچینگ"),
			("medium", "high"): (
				6,
				"عملکرد بالا / پتانسیل متوسط",
				"افقی (توسعه تخصصی یا Lead)",
			),
			("medium", "medium"): (5, "هسته پایدار سازمان", "ترکیبی (افقی + تقویت شایستگی)"),
			("medium", "low"): (4, "عملکرد متوسط / پتانسیل پایین", "تثبیت نقش فعلی"),
			("low", "high"): (
				3,
				"عملکرد بالا / پتانسیل پایین",
				"افقی (متخصص قابل اتکا)",
			),
			("low", "medium"): (2, "عملکرد پایین / پتانسیل متوسط", "برنامه بهبود عملکرد"),
			("low", "low"): (1, "ریسک بالا (عملکرد و پتانسیل پایین)", "بازطراحی نقش یا برنامه اصلاحی"),
		}
		return mapping[(potential_band, performance_band)]

