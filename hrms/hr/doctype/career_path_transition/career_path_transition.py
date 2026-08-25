# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today


class CareerPathTransition(Document):
	def validate(self):
		self.validate_designations()
		self.set_designation_context()
		self.set_grade_levels()
		self.validate_transition_logic()
		self.set_transition_title()

	def validate_designations(self):
		if self.from_designation == self.to_designation:
			frappe.throw(_("شغل مبدا و مقصد نمی‌توانند یکسان باشند."))

	def set_grade_levels(self):
		self.from_grade_level = self.get_grade_level(self.from_grade)
		self.to_grade_level = self.get_grade_level(self.to_grade)

	def set_designation_context(self):
		if self.from_designation:
			self.from_job_family = frappe.db.get_value("Designation", self.from_designation, "job_family")
			self.from_grade = frappe.db.get_value("Designation", self.from_designation, "job_grade")

		if self.to_designation:
			self.to_job_family = frappe.db.get_value("Designation", self.to_designation, "job_family")
			self.to_grade = frappe.db.get_value("Designation", self.to_designation, "job_grade")

	def get_grade_level(self, grade):
		if not grade:
			return 0
		return flt(frappe.db.get_value("Job Grade", grade, "level_number"))

	def validate_transition_logic(self):
		transition_type = (self.transition_type or "").strip()
		from_family = self.from_job_family
		to_family = self.to_job_family
		from_level = flt(self.from_grade_level)
		to_level = flt(self.to_grade_level)

		if not self.from_grade or not self.to_grade:
			frappe.throw(_("برای تعریف مسیر شغلی، گرید مبدا و مقصد باید روی شغل‌ها مشخص باشد."))

		if transition_type in {"عمودی", "افقی"} and (not from_family or not to_family):
			frappe.throw(_("برای مسیرهای عمودی/افقی، خانواده شغلی مبدا و مقصد باید مشخص باشد."))

		if transition_type == "عمودی":
			if from_family and to_family and from_family != to_family:
				frappe.throw(_("در مسیر عمودی، خانواده شغلی مبدا و مقصد باید یکسان باشد."))
			if to_level <= from_level:
				frappe.throw(_("در مسیر عمودی، سطح گرید مقصد باید بزرگ‌تر از مبدا باشد."))

		elif transition_type == "افقی":
			if to_level != from_level:
				frappe.throw(_("در مسیر افقی، سطح گرید مبدا و مقصد باید یکسان باشد."))
			if from_family and to_family and from_family == to_family:
				frappe.throw(_("در مسیر افقی، خانواده شغلی مبدا و مقصد باید متفاوت باشد."))

		elif transition_type == "دوگانه (تخصصی/مدیریتی)":
			if to_level < from_level:
				frappe.throw(_("در مسیر دوگانه، سطح گرید مقصد نباید از مبدا کمتر باشد."))

	def set_transition_title(self):
		if self.from_designation and self.to_designation:
			self.transition_title = f"{self.from_designation} -> {self.to_designation}"

	@frappe.whitelist()
	def evaluate_employee(self, employee: str):
		"""Evaluate a transition tollgate for a given employee."""
		employee_doc = frappe.get_doc("Employee", employee)
		result = {
			"eligible": True,
			"checks": {},
			"details": {},
		}

		result["checks"]["designation_match"] = employee_doc.designation == self.from_designation
		if not result["checks"]["designation_match"]:
			result["eligible"] = False
			result["details"]["designation"] = _("سمت فعلی کارمند با مبدا مسیر یکسان نیست.")

		result["checks"]["tenure"] = self.check_tenure(employee_doc)
		if not result["checks"]["tenure"]:
			result["eligible"] = False

		result["checks"]["performance"] = self.check_performance(employee_doc.name)
		if not result["checks"]["performance"]:
			result["eligible"] = False

		competency_ok, competency_details = self.check_competencies(employee_doc.name)
		result["checks"]["competencies"] = competency_ok
		result["details"]["competencies"] = competency_details
		if not competency_ok:
			result["eligible"] = False

		cert_ok, cert_details = self.check_certifications(employee_doc.name)
		result["checks"]["certifications"] = cert_ok
		result["details"]["certifications"] = cert_details
		if not cert_ok:
			result["eligible"] = False

		return result

	def check_tenure(self, employee_doc):
		required_months = flt(self.min_tenure_months)
		if not required_months:
			return True

		if not employee_doc.date_of_joining:
			return False

		joining_date = getdate(employee_doc.date_of_joining)
		current_date = getdate(today())
		months = (current_date.year - joining_date.year) * 12 + (current_date.month - joining_date.month)
		return months >= required_months

	def check_performance(self, employee):
		required_score = flt(self.min_last_two_appraisal_avg)
		if not required_score:
			return True

		appraisals = frappe.get_all(
			"Appraisal",
			filters={"employee": employee},
			fields=["final_score"],
			order_by="end_date desc, creation desc",
			limit=2,
		)
		if not appraisals:
			return False

		average_score = sum(flt(row.final_score) for row in appraisals) / len(appraisals)
		return average_score >= required_score

	def check_competencies(self, employee):
		missing = []
		required_rows = self.required_competencies or []
		if not required_rows:
			return True, {"missing": []}

		assessment_name = frappe.db.get_value(
			"Competency Assessment",
			{"employee": employee},
			"name",
			order_by="assessment_date desc, creation desc",
		)
		if not assessment_name:
			return False, {"missing": [row.competency for row in required_rows if row.competency]}

		assessment_rows = frappe.get_all(
			"Competency Assessment Item",
			filters={"parent": assessment_name, "parenttype": "Competency Assessment"},
			fields=["competency", "current_level"],
			limit=0,
		)
		level_map = {row.competency: flt(row.current_level) for row in assessment_rows}

		for row in required_rows:
			if not row.competency:
				continue
			required_level = flt(row.required_level)
			if level_map.get(row.competency, 0) < required_level:
				missing.append(
					{
						"competency": row.competency,
						"required_level": required_level,
						"current_level": level_map.get(row.competency, 0),
					}
				)

		return len(missing) == 0, {"missing": missing, "assessment": assessment_name}

	def check_certifications(self, employee):
		missing = []
		required_rows = self.required_certifications or []
		if not required_rows:
			return True, {"missing": []}

		for row in required_rows:
			if not row.is_mandatory:
				continue

			if row.training_program:
				if not self.employee_has_training_program_certificate(employee, row.training_program):
					missing.append({"training_program": row.training_program})
			elif row.certificate_name:
				# Free-text certifications cannot be auto-verified from current HRMS data.
				missing.append({"certificate_name": row.certificate_name, "verification": "manual"})

		return len(missing) == 0, {"missing": missing}

	def employee_has_training_program_certificate(self, employee, training_program):
		rows = frappe.db.sql(
			"""
			select tre.name
			from `tabTraining Result` tr
			inner join `tabTraining Result Employee` tre on tre.parent = tr.name
			inner join `tabTraining Event` te on te.name = tr.training_event
			where tr.docstatus = 1
				and tre.parenttype = 'Training Result'
				and tre.employee = %s
				and te.training_program = %s
				and ifnull(te.has_certificate, 0) = 1
				and te.event_status = 'Completed'
			limit 1
			""",
			(employee, training_program),
			as_dict=True,
		)
		return bool(rows)
