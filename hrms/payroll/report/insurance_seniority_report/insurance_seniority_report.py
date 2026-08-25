import frappe
from frappe import _
from frappe.utils import add_to_date, flt, getdate

from hrms.regional.iran.utils import (
	STANDARD_MONTH_DAYS,
	get_active_yearly_rule,
	get_active_seniority_table,
	get_employee_seniority_reference_date,
	get_iran_payroll_settings,
	get_years_of_service,
	is_iran_company,
)
from hrms.utils.jalali_helper import jalali_to_gregorian


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("شناسه کارمند"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 130,
		},
		{
			"label": _("نام کارمند"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 190,
		},
		{
			"label": _("تاریخ شروع بیمه"),
			"fieldname": "insurance_start_date",
			"fieldtype": "Date",
			"width": 130,
		},
		{
			"label": _("سنوات روزانه در ماه مرجع"),
			"fieldname": "daily_seniority_reference",
			"fieldtype": "Currency",
			"width": 170,
		},
		{
			"label": _("سنوات ماهانه در ماه مرجع"),
			"fieldname": "monthly_seniority_reference",
			"fieldtype": "Currency",
			"width": 180,
		},
		{
			"label": _("تاریخ افزایش سنوات"),
			"fieldname": "next_seniority_change_date",
			"fieldtype": "Date",
			"width": 150,
		},
		{
			"label": _("سنوات روزانه بعد از افزایش"),
			"fieldname": "daily_seniority_after_change",
			"fieldtype": "Currency",
			"width": 185,
		},
		{
			"label": _("سنوات ماهیانه پس از افزایش"),
			"fieldname": "monthly_seniority_after_change",
			"fieldtype": "Currency",
			"width": 195,
		},
	]


def get_data(filters):
	reference_date = parse_reference_date(filters)

	employee_filters = {"status": "Active"}
	if filters.get("company"):
		employee_filters["company"] = filters.get("company")

	employees = frappe.get_all(
		"Employee",
		filters=employee_filters,
		fields=["name", "employee", "employee_name", "company", "insurance_start_date"],
		order_by="employee_name asc",
	)

	data = []
	for emp in employees:
		if not is_iran_company(emp.get("company")):
			continue

		insurance_start_date = get_employee_seniority_reference_date(emp)
		if not insurance_start_date:
			continue

		insurance_start_date = getdate(insurance_start_date)
		daily_ref = get_seniority_daily_by_year(insurance_start_date, reference_date)
		monthly_ref = daily_ref * STANDARD_MONTH_DAYS

		next_change_date = get_next_seniority_change_date(insurance_start_date, reference_date)
		daily_after = 0
		monthly_after = 0
		if next_change_date:
			daily_after = get_seniority_daily_by_year(insurance_start_date, next_change_date)
			monthly_after = daily_after * STANDARD_MONTH_DAYS

		data.append(
			{
				"employee": emp.get("employee") or emp.get("name"),
				"employee_name": emp.get("employee_name"),
				"insurance_start_date": insurance_start_date,
				"daily_seniority_reference": daily_ref,
				"monthly_seniority_reference": monthly_ref,
				"next_seniority_change_date": next_change_date,
				"daily_seniority_after_change": daily_after,
				"monthly_seniority_after_change": monthly_after,
			}
		)

	return data


def parse_reference_date(filters):
	reference_date = filters.get("reference_date")
	if not reference_date:
		frappe.throw(_("فیلتر «تاریخ مرجع» الزامی است."))
	reference_date_text = str(reference_date).strip()
	if "/" in reference_date_text:
		year_text = reference_date_text.split("/")[0].strip()
		if year_text.isdigit() and int(year_text) >= 1300:
			reference_date_text = jalali_to_gregorian(reference_date_text)
	return getdate(reference_date_text)


def get_next_seniority_change_date(insurance_start_date, reference_date):
	current_years = get_years_of_service(insurance_start_date, reference_date)
	next_anniversary = add_to_date(insurance_start_date, years=current_years + 1, as_datetime=False)
	next_anniversary = getdate(next_anniversary)
	if next_anniversary <= reference_date:
		next_anniversary = add_to_date(next_anniversary, years=1, as_datetime=False)
		next_anniversary = getdate(next_anniversary)
	return next_anniversary


def get_seniority_daily_by_year(insurance_start_date, salary_date):
	years_of_service = get_years_of_service(insurance_start_date, salary_date)
	if years_of_service <= 0:
		return 0

	seniority_table = get_active_seniority_table(salary_date)
	if seniority_table and frappe.utils.cint(seniority_table.get("enabled")):
		rules = sorted(
			seniority_table.get("rules") or [],
			key=lambda row: frappe.utils.cint(row.min_years),
			reverse=True,
		)
		for row in rules:
			min_years = frappe.utils.cint(row.min_years)
			if years_of_service >= min_years:
				return flt(row.daily_amount)

	settings = get_iran_payroll_settings()
	rule = get_active_yearly_rule(settings, salary_date) if settings else None
	return flt(rule.seniority_daily_base) if rule else 0
