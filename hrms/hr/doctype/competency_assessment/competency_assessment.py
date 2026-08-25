# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class CompetencyAssessment(Document):
	def validate(self):
		self.set_context_from_employee()
		if not self.assessment_items:
			self.populate_required_competencies()
		self.calculate_gaps()
		self.calculate_summary()

	def set_context_from_employee(self):
		if not self.employee:
			return

		designation = frappe.db.get_value("Employee", self.employee, "designation")
		self.designation = designation or ""

		if designation and frappe.get_meta("Designation").has_field("job_family"):
			self.job_family = frappe.db.get_value("Designation", designation, "job_family") or ""

		if designation and frappe.get_meta("Designation").has_field("job_grade"):
			self.job_grade = frappe.db.get_value("Designation", designation, "job_grade") or ""

	def populate_required_competencies(self):
		requirements = self.get_requirement_map()
		for competency, data in requirements.items():
			self.append(
				"assessment_items",
				{
					"competency": competency,
					"required_level": data.get("required_level", 1),
					"weightage": data.get("weightage", 0),
				},
			)

	def get_requirement_map(self):
		requirements = {}
		self.add_rows_to_map(requirements, self.get_core_competencies())
		self.add_rows_to_map(requirements, self.get_family_competencies())
		self.add_rows_to_map(requirements, self.get_grade_competencies())
		self.add_rows_to_map(requirements, self.get_designation_competencies())
		return requirements

	def add_rows_to_map(self, requirement_map, rows):
		for row in rows:
			competency = row.get("competency")
			if not competency:
				continue

			existing = requirement_map.get(competency) or {}
			requirement_map[competency] = {
				"required_level": max(flt(existing.get("required_level")), flt(row.get("required_level") or 0)),
				"weightage": max(flt(existing.get("weightage")), flt(row.get("weightage") or 0)),
			}

	def get_core_competencies(self):
		meta = frappe.get_meta("HR Settings")
		if not meta.has_field("core_competencies"):
			return []

		hr_settings = frappe.get_single("HR Settings")
		return hr_settings.get("core_competencies") or []

	def get_family_competencies(self):
		if not self.job_family:
			return []

		meta = frappe.get_meta("Job Family")
		if not meta.has_field("technical_competencies"):
			return []

		job_family = frappe.get_doc("Job Family", self.job_family)
		return job_family.get("technical_competencies") or []

	def get_grade_competencies(self):
		if not self.job_grade:
			return []

		meta = frappe.get_meta("Job Grade")
		if not meta.has_field("leadership_competencies"):
			return []

		job_grade = frappe.get_doc("Job Grade", self.job_grade)
		return job_grade.get("leadership_competencies") or []

	def get_designation_competencies(self):
		if not self.designation:
			return []

		meta = frappe.get_meta("Designation")
		if not meta.has_field("required_competencies"):
			return []

		designation = frappe.get_doc("Designation", self.designation)
		return designation.get("required_competencies") or []

	def calculate_gaps(self):
		for row in self.assessment_items or []:
			row.gap = flt(row.required_level) - flt(row.current_level)

	def calculate_summary(self):
		if not self.assessment_items:
			self.average_required_level = 0
			self.average_current_level = 0
			self.average_gap = 0
			return

		count = len(self.assessment_items)
		total_required = sum(flt(row.required_level) for row in self.assessment_items)
		total_current = sum(flt(row.current_level) for row in self.assessment_items)
		total_gap = sum(flt(row.gap) for row in self.assessment_items)

		self.average_required_level = total_required / count
		self.average_current_level = total_current / count
		self.average_gap = total_gap / count

