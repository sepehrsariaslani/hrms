from __future__ import annotations

from datetime import date

import frappe
from frappe.utils import cint, flt, getdate

from hrms.utils.jalali_helper import jalali_to_gregorian

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
STANDARD_MONTH_DAYS = 30
STANDARD_DAILY_WORK_HOURS = 7.33
CONTRACTUAL_SALARY_TYPE = "قراردادی"
FIXED_SALARY_TYPE = "ثابت"
HOURLY_SALARY_TYPE = "ساعتی"
EMPLOYER_INSURANCE_RATE = 0.23
EMPLOYEE_INSURANCE_RATE = 0.07
UNEMPLOYMENT_INSURANCE_RATE = 0.03
LOCALIZED_NUMBER_TRANSLATION = str.maketrans(
	{
		"۰": "0",
		"۱": "1",
		"۲": "2",
		"۳": "3",
		"۴": "4",
		"۵": "5",
		"۶": "6",
		"۷": "7",
		"۸": "8",
		"۹": "9",
		"٠": "0",
		"١": "1",
		"٢": "2",
		"٣": "3",
		"٤": "4",
		"٥": "5",
		"٦": "6",
		"٧": "7",
		"٨": "8",
		"٩": "9",
		"٫": ".",
		"٬": ",",
		"،": ",",
	}
)


def is_iran_company(company: str | None) -> bool:
	if not company:
		return False

	country = (frappe.db.get_value("Company", company, "country") or "").strip().lower()
	if not country:
		return False

	normalized_country = " ".join(country.replace("،", ",").split())
	return any(alias in normalized_country for alias in IRAN_COUNTRY_ALIASES)


def get_iran_payroll_settings() -> frappe._dict | None:
	if not frappe.db.exists("DocType", "Iran Payroll Settings"):
		return None

	if not frappe.db.exists("Iran Payroll Settings"):
		return None

	return frappe.get_cached_doc("Iran Payroll Settings")


def get_active_yearly_rule(settings, salary_date: date):
	rules = settings.get("yearly_rules") or []

	for row in rules:
		if cint(row.get("is_default")):
			return row

	active_law_year = cint(settings.active_law_year)

	for row in rules:
		if active_law_year and cint(row.law_year) == active_law_year:
			return row

	for row in rules:
		if row.effective_from and row.effective_to:
			if getdate(row.effective_from) <= salary_date <= getdate(row.effective_to):
				return row

	return None


def get_years_of_service(service_start_date, reference_date: date | None = None) -> int:
	if not service_start_date:
		return 0

	reference_date = getdate(reference_date) if reference_date else getdate()
	service_start_date = getdate(service_start_date)

	if reference_date < service_start_date:
		return 0

	completed_years = reference_date.year - service_start_date.year
	if (reference_date.month, reference_date.day) < (service_start_date.month, service_start_date.day):
		completed_years -= 1

	return max(0, completed_years)


def get_employee_seniority_reference_date(doc_or_dict) -> date | None:
	if not doc_or_dict:
		return None

	return doc_or_dict.get("insurance_start_date")


def get_employee_salary_type(doc_or_dict) -> str:
	if not doc_or_dict:
		return CONTRACTUAL_SALARY_TYPE

	return doc_or_dict.get("employee_salary_type") or CONTRACTUAL_SALARY_TYPE


def get_designation_salary_rule(settings, designation: str | None, company: str | None):
	if not designation or not company:
		return None

	for row in settings.get("designation_rules") or []:
		if row.get("designation") == designation and row.get("company") == company:
			return row

	return None


def get_fiscal_year_by_date(reference_date: date | None = None):
	reference_date = getdate(reference_date) if reference_date else getdate()
	fiscal_year = frappe.db.get_value(
		"Fiscal Year",
		{
			"year_start_date": ["<=", reference_date],
			"year_end_date": [">=", reference_date],
		},
		"name",
	)
	return fiscal_year or frappe.db.get_value("Fiscal Year", {}, "name")


def get_active_seniority_table(salary_date: date | None = None):
	if not frappe.db.exists("DocType", "Iran Seniority Table"):
		return None

	filters = {"enabled": 1}
	fiscal_year = get_fiscal_year_by_date(salary_date)
	if fiscal_year:
		filters["fiscal_year"] = fiscal_year

	table_name = frappe.db.get_value("Iran Seniority Table", filters, "name")
	if not table_name:
		table_name = frappe.db.get_value("Iran Seniority Table", {"enabled": 1}, "name")

	return frappe.get_cached_doc("Iran Seniority Table", table_name) if table_name else None


def get_seniority_daily_base(
	joining_date,
	salary_date: date | None = None,
	settings: frappe._dict | None = None,
	rule=None,
):
	years_of_service = get_years_of_service(joining_date, salary_date)
	if years_of_service <= 0:
		return 0

	table_doc = get_active_seniority_table(salary_date)
	if table_doc and cint(table_doc.get("enabled")):
		for row in sorted(table_doc.get("rules") or [], key=lambda d: cint(d.min_years), reverse=True):
			min_years = cint(row.min_years)
			if years_of_service >= min_years:
				return flt(row.daily_amount)

	if not rule and settings:
		rule = get_active_yearly_rule(settings, getdate(salary_date) if salary_date else getdate())

	return flt(rule.seniority_daily_base) if rule else 0


def sync_iran_employee_compensation_fields(doc, method=None):
	if not doc or doc.doctype != "Employee":
		return

	if not is_iran_company(doc.company):
		return

	normalize_insurance_start_date(doc)

	settings = get_iran_payroll_settings()
	salary_date = getdate()
	rule = get_active_yearly_rule(settings, salary_date) if settings else None
	designation_rule = get_designation_salary_rule(settings, doc.designation, doc.company) if settings else None
	set_doc_field_if_exists(doc, "insurance_start_date", get_employee_seniority_reference_date(doc))
	set_doc_field_if_exists(doc, "employee_salary_type", get_employee_salary_type(doc))

	salary_type = get_employee_salary_type(doc)
	daily_base = flt(doc.get("daily_pay"))
	monthly_technical_bonus = get_numeric_employee_field_value(doc, "karane")
	technical_allowance_monthly = get_numeric_employee_field_value(doc, "technical_allowance_monthly")
	monthly_technical_total = monthly_technical_bonus + technical_allowance_monthly
	technical_daily = monthly_technical_total / STANDARD_MONTH_DAYS if monthly_technical_total else 0
	supervision_monthly = flt(doc.get("supervision_allowance"))
	service_allowance_monthly = flt(doc.get("service_allowance_monthly"))
	overtime_multiplier = flt(rule.overtime_multiplier) if rule and flt(rule.overtime_multiplier) else 1.4

	if salary_type == FIXED_SALARY_TYPE:
		monthly_base = flt(doc.get("fixed_monthly_salary"))
		if not monthly_base:
			monthly_base = daily_base * STANDARD_MONTH_DAYS
		daily_base = monthly_base / STANDARD_MONTH_DAYS if monthly_base else 0
	elif salary_type == HOURLY_SALARY_TYPE:
		hourly_base = flt(doc.get("employee_hourly_salary"))
		daily_base = hourly_base * STANDARD_DAILY_WORK_HOURS
		monthly_base = daily_base * STANDARD_MONTH_DAYS
	else:
		if designation_rule:
			daily_base = flt(designation_rule.base_daily_pay)
		monthly_base = daily_base * STANDARD_MONTH_DAYS

	if salary_type != HOURLY_SALARY_TYPE:
		hourly_base = daily_base / STANDARD_DAILY_WORK_HOURS if daily_base else 0

	if salary_type == CONTRACTUAL_SALARY_TYPE and designation_rule:
		daily_base = flt(designation_rule.base_daily_pay)
		monthly_base = daily_base * STANDARD_MONTH_DAYS
		hourly_base = daily_base / STANDARD_DAILY_WORK_HOURS if daily_base else 0

	hourly_technical = technical_daily / STANDARD_DAILY_WORK_HOURS if technical_daily else 0
	overtime_hourly = (hourly_base + hourly_technical) * overtime_multiplier
	absence_deduction = (daily_base + technical_daily + (supervision_monthly / STANDARD_MONTH_DAYS)) / STANDARD_DAILY_WORK_HOURS

	seniority_daily = get_seniority_daily_base(
		get_employee_seniority_reference_date(doc),
		salary_date=salary_date,
		settings=settings,
		rule=rule,
	)
	insurance_service_years = get_years_of_service(
		get_employee_seniority_reference_date(doc),
		getdate(),
	)
	seniority_monthly = seniority_daily * STANDARD_MONTH_DAYS
	housing_allowance = flt(rule.housing_allowance) if rule else 0
	grocery_allowance = flt(rule.grocery_allowance) if rule else 0
	marriage_allowance = flt(rule.marriage_allowance) if rule and (doc.get("marital_status") or "").lower() == "married" else 0
	child_allowance_per_child = flt(rule.child_allowance_per_child) if rule else 0
	children_count = cint(doc.get("children_count"))
	child_allowance = child_allowance_per_child * children_count
	min_hourly_wage = flt(rule.min_hourly_wage) if rule else 0
	total_receivable = (
		monthly_base
		+ monthly_technical_total
		+ seniority_monthly
		+ supervision_monthly
		+ service_allowance_monthly
		+ housing_allowance
		+ grocery_allowance
		+ marriage_allowance
		+ child_allowance
	)
	insurance_base = monthly_base + seniority_monthly + grocery_allowance + housing_allowance + marriage_allowance

	if salary_type == CONTRACTUAL_SALARY_TYPE:
		employer_insurance_share = insurance_base * EMPLOYER_INSURANCE_RATE
		employee_insurance_share = insurance_base * EMPLOYEE_INSURANCE_RATE
		unemployment_insurance_share = insurance_base * UNEMPLOYMENT_INSURANCE_RATE
		organization_monthly_cost = total_receivable - employee_insurance_share + employer_insurance_share
	else:
		employer_insurance_share = 0
		employee_insurance_share = 0
		unemployment_insurance_share = 0
		organization_monthly_cost = 0

	set_doc_field_if_exists(doc, "daily_pay", daily_base)
	set_doc_field_if_exists(doc, "monthly_base_pay", monthly_base)
	set_doc_field_if_exists(doc, "base_pay", hourly_base)
	set_doc_field_if_exists(doc, "karane", monthly_technical_bonus)
	set_doc_field_if_exists(doc, "technical_allowance_monthly", technical_allowance_monthly)
	set_doc_field_if_exists(doc, "supervision_allowance", supervision_monthly)
	set_doc_field_if_exists(doc, "overtime_rate", overtime_hourly)
	set_doc_field_if_exists(doc, "absence_deduction", absence_deduction)
	set_doc_field_if_exists(doc, "employee_seniority_daily_base", seniority_daily)
	set_doc_field_if_exists(doc, "employee_seniority_monthly_base", seniority_monthly)
	set_doc_field_if_exists(doc, "insurance_service_years", insurance_service_years)
	set_doc_field_if_exists(doc, "service_allowance_monthly", service_allowance_monthly)
	set_doc_field_if_exists(doc, "housing_allowance", housing_allowance)
	set_doc_field_if_exists(doc, "grocery_allowance", grocery_allowance)
	set_doc_field_if_exists(doc, "marriage_allowance", marriage_allowance)
	set_doc_field_if_exists(doc, "child_allowance_per_child", child_allowance_per_child)
	set_doc_field_if_exists(doc, "child_allowance", child_allowance)
	set_doc_field_if_exists(doc, "min_hourly_wage", min_hourly_wage)
	set_doc_field_if_exists(doc, "total_receivable", total_receivable)
	set_doc_field_if_exists(doc, "employer_insurance_share", employer_insurance_share)
	set_doc_field_if_exists(doc, "employee_insurance_share", employee_insurance_share)
	set_doc_field_if_exists(doc, "unemployment_insurance_share", unemployment_insurance_share)
	set_doc_field_if_exists(doc, "organization_monthly_cost", organization_monthly_cost)


@frappe.whitelist()
def recalculate_iran_employee_seniority_fields(company: str | None = None):
	"""Recalculate seniority-based employee fields using active Iran payroll law."""
	filters = {}
	if company:
		filters["company"] = company

	employees = frappe.get_all("Employee", filters=filters, pluck="name", limit_page_length=0)
	updated = 0

	for employee in employees:
		doc = frappe.get_doc("Employee", employee)
		if not is_iran_company(doc.company):
			continue

		set_doc_field_if_exists(doc, "insurance_start_date", get_employee_seniority_reference_date(doc))
		sync_iran_employee_compensation_fields(doc)
		values = get_iran_employee_compensation_values(doc)
		values = filter_existing_employee_compensation_columns(values)
		frappe.db.set_value("Employee", employee, values, update_modified=False)
		updated += 1

	frappe.clear_cache(doctype="Employee")
	return {"updated": updated}


@frappe.whitelist()
def recalculate_iran_employee_compensation_from_client(
	employee: str,
	insurance_start_date: str | None = None,
	insurance_start_date_persian: str | None = None,
):
	if not employee:
		frappe.throw("Employee is required")

	doc = frappe.get_doc("Employee", employee)
	if not is_iran_company(doc.company):
		return {}

	if insurance_start_date_persian and not insurance_start_date:
		insurance_start_date = jalali_to_gregorian(insurance_start_date_persian)

	if insurance_start_date:
		insurance_start_date_text = str(insurance_start_date).strip()
		if "/" in insurance_start_date_text:
			year_text = insurance_start_date_text.split("/")[0].strip()
			if year_text.isdigit() and int(year_text) >= 1300:
				insurance_start_date = jalali_to_gregorian(insurance_start_date_text)
		doc.set("insurance_start_date", insurance_start_date)

	sync_iran_employee_compensation_fields(doc)

	return {
		"insurance_start_date": doc.get("insurance_start_date"),
		"insurance_service_years": cint(doc.get("insurance_service_years")),
		"employee_seniority_daily_base": flt(doc.get("employee_seniority_daily_base")),
		"employee_seniority_monthly_base": flt(doc.get("employee_seniority_monthly_base")),
		"employee_salary_type": doc.get("employee_salary_type"),
		"daily_pay": flt(doc.get("daily_pay")),
		"monthly_base_pay": flt(doc.get("monthly_base_pay")),
		"base_pay": flt(doc.get("base_pay")),
		"overtime_rate": flt(doc.get("overtime_rate")),
		"absence_deduction": flt(doc.get("absence_deduction")),
		"housing_allowance": flt(doc.get("housing_allowance")),
		"grocery_allowance": flt(doc.get("grocery_allowance")),
		"marriage_allowance": flt(doc.get("marriage_allowance")),
		"child_allowance_per_child": flt(doc.get("child_allowance_per_child")),
		"child_allowance": flt(doc.get("child_allowance")),
		"total_receivable": flt(doc.get("total_receivable")),
	}


def sync_employees_after_iran_payroll_settings_update(doc, method=None):
	if isinstance(doc, dict):
		doc = frappe.get_doc(doc)

	if not doc or doc.doctype != "Iran Payroll Settings":
		return

	designation_rules = doc.get("designation_rules") or []
	updated = 0
	seen = set()

	for row in designation_rules:
		company = row.get("company")
		designation = row.get("designation")
		if not company or not designation:
			continue

		key = (company, designation)
		if key in seen:
			continue
		seen.add(key)

		employees = frappe.get_all(
			"Employee",
			filters={"company": company, "designation": designation},
			pluck="name",
			limit_page_length=0,
		)
		for employee in employees:
			emp_doc = frappe.get_doc("Employee", employee)
			set_doc_field_if_exists(emp_doc, "insurance_start_date", get_employee_seniority_reference_date(emp_doc))
			sync_iran_employee_compensation_fields(emp_doc)
			values = get_iran_employee_compensation_values(emp_doc)
			values = filter_existing_employee_compensation_columns(values)
			frappe.db.set_value(
				"Employee",
				employee,
				values,
				update_modified=False,
			)
			updated += 1

	frappe.clear_cache(doctype="Employee")
	return {"updated": updated}


def sync_iran_employee_compensation_fields_on_update(doc, method=None):
	if not doc or doc.doctype != "Employee":
		return

	if not is_iran_company(doc.company):
		return

	sync_iran_employee_compensation_fields(doc)
	values = get_iran_employee_compensation_values(doc)
	values = filter_existing_employee_compensation_columns(values)
	frappe.db.set_value("Employee", doc.name, values, update_modified=False)


def get_iran_employee_compensation_values(doc) -> dict:
	return {
		"insurance_start_date": doc.get("insurance_start_date"),
		"insurance_service_years": cint(doc.get("insurance_service_years")),
		"employee_salary_type": doc.get("employee_salary_type"),
		"fixed_monthly_salary": flt(doc.get("fixed_monthly_salary")),
		"employee_hourly_salary": flt(doc.get("employee_hourly_salary")),
		"daily_pay": flt(doc.get("daily_pay")),
		"monthly_base_pay": flt(doc.get("monthly_base_pay")),
		"base_pay": flt(doc.get("base_pay")),
		"karane": flt(doc.get("karane")),
		"technical_allowance_monthly": flt(doc.get("technical_allowance_monthly")),
		"overtime_rate": flt(doc.get("overtime_rate")),
		"absence_deduction": flt(doc.get("absence_deduction")),
		"employee_seniority_daily_base": flt(doc.get("employee_seniority_daily_base")),
		"employee_seniority_monthly_base": flt(doc.get("employee_seniority_monthly_base")),
		"service_allowance_monthly": flt(doc.get("service_allowance_monthly")),
		"housing_allowance": flt(doc.get("housing_allowance")),
		"grocery_allowance": flt(doc.get("grocery_allowance")),
		"marriage_allowance": flt(doc.get("marriage_allowance")),
		"child_allowance_per_child": flt(doc.get("child_allowance_per_child")),
		"child_allowance": flt(doc.get("child_allowance")),
		"min_hourly_wage": flt(doc.get("min_hourly_wage")),
		"total_receivable": flt(doc.get("total_receivable")),
		"employer_insurance_share": flt(doc.get("employer_insurance_share")),
		"employee_insurance_share": flt(doc.get("employee_insurance_share")),
		"unemployment_insurance_share": flt(doc.get("unemployment_insurance_share")),
		"organization_monthly_cost": flt(doc.get("organization_monthly_cost")),
	}


def filter_existing_employee_compensation_columns(values: dict) -> dict:
	if not values:
		return {}

	return {key: value for key, value in values.items() if frappe.db.has_column("Employee", key)}


def normalize_insurance_start_date(doc):
	if not doc:
		return

	current_insurance_start = doc.get("insurance_start_date")
	if current_insurance_start:
		try:
			doc.set("insurance_start_date", getdate(current_insurance_start))
		except Exception:
			pass
		return

	persian_field_value = (
		doc.get("insurance_start_date_persian")
		or doc.get("custom_insurance_start_date_persian")
		or doc.get("insurance_start_persian")
	)
	if not persian_field_value:
		return

	converted = jalali_to_gregorian(persian_field_value)
	if not converted:
		return

	try:
		doc.set("insurance_start_date", getdate(converted))
	except Exception:
		pass


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


def get_numeric_employee_field_value(doc, fieldname: str) -> float:
	value = normalize_localized_numeric_input(doc.get(fieldname))
	if value in (None, "") and doc.get("name") and not doc.is_new() and frappe.db.has_column("Employee", fieldname):
		value = normalize_localized_numeric_input(frappe.db.get_value("Employee", doc.name, fieldname))
	return flt(value)


def normalize_localized_numeric_input(value):
	if not isinstance(value, str):
		return value

	return (
		value.translate(LOCALIZED_NUMBER_TRANSLATION)
		.replace("\u200e", "")
		.replace("\u200f", "")
		.replace("\u200c", "")
		.strip()
	)


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
			"insurance_start_date",
			"date_of_joining",
			"daily_pay",
			"karane",
			"technical_allowance_monthly",
			"supervision_allowance",
			"employee_seniority_daily_base",
		],
		as_dict=True,
	) or {}

	salary_date = getdate(doc.end_date or doc.posting_date)
	salary_days = get_salary_days(doc)
	children_count = cint(employee.get("children_count"))
	is_married = (employee.get("marital_status") or "").lower() == "married"

	seniority_reference_date = get_employee_seniority_reference_date(employee)
	years_of_service = get_years_of_service(seniority_reference_date, salary_date)

	housing = flt(rule.housing_allowance)
	grocery = flt(rule.grocery_allowance)
	marriage = flt(rule.marriage_allowance) if is_married else 0
	child = flt(rule.child_allowance_per_child) * children_count
	seniority_daily = flt(employee.get("employee_seniority_daily_base")) or get_seniority_daily_base(
		seniority_reference_date,
		salary_date=salary_date,
		settings=settings,
		rule=rule,
	)
	seniority = seniority_daily * salary_days if years_of_service >= 1 else 0
	technical = flt(employee.get("karane")) + flt(employee.get("technical_allowance_monthly"))
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
	# Income tax is managed خارج از تنظیمات حقوق ایران.
	upsert_component_row(doc, "deductions", DEDUCTION_COMPONENTS["income_tax"], 0)

	apply_smart_attendance_summary(doc)
	doc.calculate_net_pay()
	doc.compute_year_to_date()
	doc.compute_month_to_date()
	doc.compute_component_wise_year_to_date()
