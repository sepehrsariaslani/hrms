from __future__ import annotations

from datetime import date

import frappe
from frappe.utils import cint, date_diff, flt, getdate

EARNING_COMPONENTS = {
	"housing": "Housing Allowance (Iran)",
	"grocery": "Grocery Allowance (Iran)",
	"marriage": "Marriage Allowance (Iran)",
	"child": "Child Allowance (Iran)",
	"seniority": "Seniority Allowance (Iran)",
	"technical": "Technical Allowance (Iran)",
	"supervision": "Supervision Allowance (Iran)",
	"severance": "Severance Reserve (Iran)",
	"eidi": "Eidi Reserve (Iran)",
}

DEDUCTION_COMPONENTS = {
	"employee_insurance": "Employee Social Insurance (Iran)",
	"employer_insurance": "Employer Social Insurance (Iran)",
	"income_tax": "Income Tax (Iran)",
}

INSURANCE_EXEMPT_EARNINGS = {
	EARNING_COMPONENTS["technical"],
	EARNING_COMPONENTS["severance"],
	EARNING_COMPONENTS["eidi"],
}

IRAN_COUNTRY_ALIASES = {"iran", "islamic republic of iran", "iran, islamic republic of", "ایران"}


def is_iran_company(company: str | None) -> bool:
	if not company:
		return False

	country = (frappe.db.get_value("Company", company, "country") or "").strip().lower()
	return country in IRAN_COUNTRY_ALIASES


def get_iran_payroll_settings() -> frappe._dict | None:
	if not frappe.db.exists("DocType", "Iran Payroll Settings"):
		return None

	if not frappe.db.exists("Iran Payroll Settings"):
		return None

	return frappe.get_cached_doc("Iran Payroll Settings")


def get_active_yearly_rule(settings, salary_date: date):
	active_law_year = cint(settings.active_law_year)
	rules = settings.get("yearly_rules") or []

	for row in rules:
		if active_law_year and cint(row.law_year) == active_law_year:
			return row

	for row in rules:
		if row.effective_from and row.effective_to:
			if getdate(row.effective_from) <= salary_date <= getdate(row.effective_to):
				return row

	return None


def get_tax_slabs_for_year(settings, law_year: int):
	rows = settings.get("tax_slabs") or []
	filtered = [row for row in rows if cint(row.law_year) == cint(law_year)]
	return sorted(filtered, key=lambda row: flt(row.from_amount))


def calculate_income_tax(taxable_income: float, slabs: list) -> float:
	if taxable_income <= 0:
		return 0

	for slab in slabs:
		start = flt(slab.from_amount)
		end = flt(slab.to_amount)
		rate = flt(slab.tax_rate)
		fixed_tax = flt(slab.fixed_tax)
		rebate = flt(slab.deduction_amount)

		in_band = taxable_income >= start and (not end or taxable_income <= end)
		if in_band:
			variable = (taxable_income - start) * (rate / 100)
			return max(0, fixed_tax + variable - rebate)

	return 0


def upsert_component_row(doc, table_field: str, component_name: str, amount: float):
	rows = doc.get(table_field) or []
	target = None
	for row in rows:
		if row.salary_component == component_name:
			target = row
			break

	if abs(flt(amount)) < 0.0001:
		if target:
			rows.remove(target)
		return

	if not target:
		target = doc.append(table_field, {})
		target.salary_component = component_name

	target.amount = flt(amount)


def get_salary_days(doc) -> float:
	# Keep payroll math stable even if payment days is empty at draft stage.
	salary_days = flt(doc.get("payment_days")) or 30
	return salary_days if salary_days > 0 else 30


def set_doc_field_if_exists(doc, fieldname: str, value):
	if doc.meta.get_field(fieldname):
		doc.set(fieldname, value)


def apply_smart_attendance_summary(doc):
	if not (doc.employee and doc.start_date and doc.end_date):
		return

	try:
		from hrms.hr.report.smart_attendance_report.smart_attendance_report import get_data

		rows = get_data(
			{
				"employee": doc.employee,
				"from_date": doc.start_date,
				"to_date": doc.end_date,
			}
		)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"Unable to compute Smart Attendance summary for Salary Slip {doc.get('name') or 'new'}",
		)
		return

	required_hours = 0
	worked_hours = 0
	overtime_hours = 0
	shortage_hours = 0

	for row in rows or []:
		if row.get("employee") != doc.employee:
			continue

		required_hours += flt(row.get("standard_hours"))
		worked_hours += flt(row.get("working_hours"))
		overtime_hours += flt(row.get("overtime"))
		shortage_hours += flt(row.get("time_off"))

	required_hours = flt(required_hours, 2)
	worked_hours = flt(worked_hours, 2)
	overtime_hours = flt(overtime_hours, 2)
	shortage_hours = flt(shortage_hours, 2)

	set_doc_field_if_exists(doc, "required_working_hours_iran", required_hours)
	set_doc_field_if_exists(doc, "worked_hours_iran", worked_hours)
	set_doc_field_if_exists(doc, "overtime_hours_iran", overtime_hours)
	set_doc_field_if_exists(doc, "shortage_hours_iran", shortage_hours)

	# Backward compatibility with existing custom print formats.
	set_doc_field_if_exists(doc, "employee_working_hours", worked_hours)
	set_doc_field_if_exists(doc, "overtime", overtime_hours)
	set_doc_field_if_exists(doc, "absence", shortage_hours)


@frappe.whitelist()
def apply_iran_payroll_rules(doc, method=None):
	if doc.doctype != "Salary Slip" or doc.docstatus != 0:
		return

	if not is_iran_company(doc.company):
		return

	settings = get_iran_payroll_settings()
	if not settings:
		return

	rule = get_active_yearly_rule(settings, getdate(doc.start_date or doc.posting_date))
	if not rule:
		return

	employee = frappe.db.get_value(
		"Employee",
		doc.employee,
		[
			"marital_status",
			"children_count",
			"date_of_joining",
			"daily_pay",
			"monthly_technical_bonus",
			"supervision_allowance",
		],
		as_dict=True,
	) or {}

	salary_date = getdate(doc.end_date or doc.posting_date)
	salary_days = get_salary_days(doc)
	children_count = cint(employee.get("children_count"))
	is_married = (employee.get("marital_status") or "").lower() == "married"

	joining_date = employee.get("date_of_joining")
	years_of_service = max(0, date_diff(salary_date, joining_date) // 365) if joining_date else 0

	housing = flt(rule.housing_allowance)
	grocery = flt(rule.grocery_allowance)
	marriage = flt(rule.marriage_allowance) if is_married else 0
	child = flt(rule.child_allowance_per_child) * children_count
	seniority = flt(rule.seniority_daily_base) * salary_days if years_of_service >= 1 else 0
	technical = flt(employee.get("monthly_technical_bonus"))
	supervision = flt(employee.get("supervision_allowance"))

	base_daily_wage = flt(employee.get("daily_pay")) or flt(rule.min_daily_wage)
	monthly_base_wage = base_daily_wage * salary_days
	severance = monthly_base_wage / 12 if years_of_service >= 1 else 0

	eidi_annual = monthly_base_wage * 2
	if flt(rule.min_monthly_wage):
		eidi_annual = min(eidi_annual, flt(rule.min_monthly_wage) * 3)
	eidi = eidi_annual / 12

	upsert_component_row(doc, "earnings", EARNING_COMPONENTS["housing"], housing)
	upsert_component_row(doc, "earnings", EARNING_COMPONENTS["grocery"], grocery)
	upsert_component_row(doc, "earnings", EARNING_COMPONENTS["marriage"], marriage)
	upsert_component_row(doc, "earnings", EARNING_COMPONENTS["child"], child)
	upsert_component_row(doc, "earnings", EARNING_COMPONENTS["seniority"], seniority)
	upsert_component_row(doc, "earnings", EARNING_COMPONENTS["technical"], technical)
	upsert_component_row(doc, "earnings", EARNING_COMPONENTS["supervision"], supervision)
	upsert_component_row(doc, "earnings", EARNING_COMPONENTS["severance"], severance)
	upsert_component_row(doc, "earnings", EARNING_COMPONENTS["eidi"], eidi)

	total_earnings = sum(flt(row.amount) for row in doc.get("earnings") or [])
	insurable_earnings = sum(
		flt(row.amount)
		for row in doc.get("earnings") or []
		if row.salary_component not in INSURANCE_EXEMPT_EARNINGS
	)
	employee_insurance = insurable_earnings * (flt(rule.insurance_employee_rate) / 100)
	employer_insurance = insurable_earnings * (flt(rule.insurance_employer_rate) / 100)

	taxable_income = total_earnings - employee_insurance - flt(rule.monthly_tax_exemption)
	tax_slabs = get_tax_slabs_for_year(settings, cint(rule.law_year))
	income_tax = calculate_income_tax(taxable_income, tax_slabs)

	upsert_component_row(
		doc,
		"deductions",
		DEDUCTION_COMPONENTS["employee_insurance"],
		employee_insurance,
	)
	upsert_component_row(
		doc,
		"deductions",
		DEDUCTION_COMPONENTS["employer_insurance"],
		employer_insurance,
	)
	upsert_component_row(doc, "deductions", DEDUCTION_COMPONENTS["income_tax"], income_tax)

	apply_smart_attendance_summary(doc)
	doc.calculate_net_pay()
	doc.compute_year_to_date()
	doc.compute_month_to_date()
	doc.compute_component_wise_year_to_date()
