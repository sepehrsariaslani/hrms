# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class IndividualDevelopmentPlan(Document):
	def validate(self):
		self.set_employee_context()
		self.set_target_context()
		if not self.competency_goals:
			self.populate_competency_goals_from_transition()
		self.calculate_competency_gaps()
		self.evaluate_transition_readiness()
		self.calculate_overall_progress()

	def set_employee_context(self):
		if not self.employee:
			return

		employee = frappe.get_doc("Employee", self.employee)
		self.employee_name = employee.employee_name
		self.company = employee.company
		self.department = employee.department
		self.current_designation = employee.designation

		if employee.designation and frappe.get_meta("Designation").has_field("job_family"):
			self.current_job_family = frappe.db.get_value("Designation", employee.designation, "job_family") or ""
		if employee.designation and frappe.get_meta("Designation").has_field("job_grade"):
			self.current_job_grade = frappe.db.get_value("Designation", employee.designation, "job_grade") or ""

	def set_target_context(self):
		if not self.target_transition:
			return

		transition = frappe.get_doc("Career Path Transition", self.target_transition)
		self.target_designation = transition.to_designation
		self.target_transition_type = transition.transition_type

	def populate_competency_goals_from_transition(self):
		if not self.target_transition:
			return

		transition = frappe.get_doc("Career Path Transition", self.target_transition)
		current_levels = self.get_latest_competency_levels()

		for row in transition.required_competencies or []:
			if not row.competency:
				continue
			current_level = flt(current_levels.get(row.competency))
			self.append(
				"competency_goals",
				{
					"competency": row.competency,
					"current_level": current_level,
					"target_level": flt(row.required_level) or current_level,
					"priority": "بالا" if row.is_mandatory else "متوسط",
				},
			)

	def get_latest_competency_levels(self):
		if not self.employee:
			return {}

		assessment_name = frappe.db.get_value(
			"Competency Assessment",
			{"employee": self.employee},
			"name",
			order_by="assessment_date desc, creation desc",
		)
		if not assessment_name:
			return {}

		rows = frappe.get_all(
			"Competency Assessment Item",
			filters={"parent": assessment_name, "parenttype": "Competency Assessment"},
			fields=["competency", "current_level"],
			limit=0,
		)
		return {row.competency: flt(row.current_level) for row in rows}

	def calculate_competency_gaps(self):
		for row in self.competency_goals or []:
			row.gap = flt(row.target_level) - flt(row.current_level)

	def evaluate_transition_readiness(self):
		if not self.target_transition or not self.employee:
			self.transition_readiness = ""
			return

		transition = frappe.get_doc("Career Path Transition", self.target_transition)
		result = transition.evaluate_employee(self.employee)
		self.transition_readiness = json.dumps(result, ensure_ascii=False)

	def calculate_overall_progress(self):
		action_progress = self.get_action_progress()
		milestone_progress = self.get_milestone_progress()

		parts = [action_progress, milestone_progress]
		self.overall_progress = sum(parts) / len(parts) if parts else 0

	def get_action_progress(self):
		actions = self.development_actions or []
		if not actions:
			return 0
		return sum(flt(row.completion_percent) for row in actions) / len(actions)

	def get_milestone_progress(self):
		milestones = self.milestones or []
		if not milestones:
			return 0
		completed = sum(1 for row in milestones if row.status == "تکمیل شده")
		return (completed / len(milestones)) * 100

