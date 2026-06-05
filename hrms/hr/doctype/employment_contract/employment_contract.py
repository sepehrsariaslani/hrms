import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

from hrms.api.employment_contract import (
	get_contract_settings_defaults,
	get_employee_contract_defaults,
)
from hrms.utils.jalali_helper import gregorian_to_jalali


class EmploymentContract(Document):
	def validate(self):
		self.validate_dates()
		self.set_duration_months()
		self.set_contract_status()
		self.apply_settings_defaults()
		self.sync_employee_defaults()
		self.set_default_issue_date()
		self.set_jalali_dates()
		self.sync_work_locations_with_settings()
		self.ensure_salary_items()

	def validate_dates(self):
		if self.start_date and self.end_date and getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(_("تاریخ پایان قرارداد نمی‌تواند قبل از تاریخ شروع باشد."))

	def set_duration_months(self):
		if not (self.start_date and self.end_date):
			self.duration_months = 0
			return

		start = getdate(self.start_date)
		end = getdate(self.end_date)
		months = (end.year - start.year) * 12 + (end.month - start.month)
		if end.day < start.day:
			months -= 1
		if months == 0 and end >= start:
			months = 1
		self.duration_months = max(months, 0)

	def set_contract_status(self):
		if not (self.start_date and self.end_date):
			self.status = "Draft"
			return

		today_date = getdate(today())
		start = getdate(self.start_date)
		end = getdate(self.end_date)

		if today_date < start:
			self.status = "Draft"
		elif start <= today_date <= end:
			self.status = "Active"
		else:
			self.status = "Ended"

	def apply_settings_defaults(self):
		defaults = get_contract_settings_defaults()

		if not self.contract_type:
			self.contract_type = defaults.get("default_contract_type") or "قرارداد کار موقت"

		if not self.work_hours_per_week:
			self.work_hours_per_week = defaults.get("default_work_hours_per_week") or 44

		if not self.workplace_details:
			self.workplace_details = defaults.get("default_workplace_details")

		if not self.job_title:
			self.job_title = defaults.get("default_job_title")

		if not self.employer_bank_name:
			self.employer_bank_name = defaults.get("employer_bank_name")

		if not self.employer_bank_account:
			self.employer_bank_account = defaults.get("employer_bank_account")

		if not self.payment_bank_name:
			self.payment_bank_name = defaults.get("employee_payment_bank")

	def sync_employee_defaults(self):
		if not self.employee:
			return

		contract_start = self.start_date or today()
		data = get_employee_contract_defaults(self.employee, contract_start)

		# Always keep identity/contact fields in sync with Employee
		field_map = {
			"employee_name": "employee_name",
			"company": "company",
			"designation": "designation",
			"department": "department",
			"branch": "branch",
			"employee_phone": "employee_phone",
			"employee_address": "employee_address",
			"national_id": "national_id",
			"id_number": "id_number",
			"id_issue_place": "id_issue_place",
			"father_name": "father_name",
			"employee_bank_name": "employee_bank_name",
			"employee_bank_account": "employee_bank_account",
			"employee_iban": "employee_iban",
		}

		for target_field, source_key in field_map.items():
			if self.meta.has_field(target_field):
				self.set(target_field, data.get(source_key))

	def set_default_issue_date(self):
		if not self.issue_date:
			self.issue_date = today()

	def set_jalali_dates(self):
		self.issue_date_jalali = gregorian_to_jalali(self.issue_date) if self.issue_date else ""
		self.start_date_jalali = gregorian_to_jalali(self.start_date) if self.start_date else ""
		self.end_date_jalali = gregorian_to_jalali(self.end_date) if self.end_date else ""

	def sync_work_locations_with_settings(self):
		if self.work_locations:
			return

		defaults = get_contract_settings_defaults()
		workplaces = defaults.get("workplaces") or []
		for workplace in workplaces:
			branch = workplace.get("branch")
			if branch:
				self.append("work_locations", {"branch": branch})

	def ensure_salary_items(self):
		if not self.employee:
			return

		if self.salary_items and not self.has_value_changed("employee"):
			return

		employee_defaults = get_employee_contract_defaults(self.employee, self.start_date or today())
		payroll_components = employee_defaults.get("payroll_components") or []
		self.set("salary_items", [])
		for item in payroll_components:
			amount_31 = item.get("amount_31_days")
			amount_30 = item.get("amount_30_days")
			label = item.get("label")
			if not (label or "").strip():
				continue
			if (amount_31 or 0) <= 0 and (amount_30 or 0) <= 0:
				continue
			self.append(
				"salary_items",
				{
					"salary_component_label": label,
					"amount_31_days": amount_31,
					"amount_30_days": amount_30 if amount_30 is not None else amount_31,
					"remarks": item.get("remarks"),
				},
			)
