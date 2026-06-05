# Copyright (c) 2026, Iran Utilities
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, flt

from hrms.regional.iran.utils import (
	STANDARD_MONTH_DAYS,
	get_employee_seniority_reference_date,
	get_seniority_daily_base,
	get_years_of_service,
	get_iran_payroll_settings,
	get_active_yearly_rule,
)


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
			"width": 180,
		},
		{
			"label": _("تاریخ شروع بیمه"),
			"fieldname": "insurance_start_date",
			"fieldtype": "Date",
			"width": 130,
		},
		{
			"label": _("سال‌های سابقه بیمه"),
			"fieldname": "insurance_service_years",
			"fieldtype": "Int",
			"width": 150,
		},
		{
			"label": _("تاریخ ورود به سازمان"),
			"fieldname": "organization_join_date",
			"fieldtype": "Date",
			"width": 140,
		},
		{
			"label": _("پایه سنوات روزانه"),
			"fieldname": "employee_seniority_daily_base",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": _("پایه سنوات ماهانه"),
			"fieldname": "employee_seniority_monthly_base",
			"fieldtype": "Currency",
			"width": 160,
		},
		{
			"label": _("سابقه در سازمان تا امروز"),
			"fieldname": "organization_service_text",
			"fieldtype": "Data",
			"width": 190,
		},
	]


def get_data(filters):
	today = getdate()
	settings = get_iran_payroll_settings()
	rule = get_active_yearly_rule(settings, today) if settings else None

	employee_filters = {}
	if filters.get("company"):
		employee_filters["company"] = filters.get("company")
	if filters.get("employee_status"):
		employee_filters["status"] = filters.get("employee_status")

	employees = frappe.get_all(
		"Employee",
		filters=employee_filters,
		fields=[
			"name",
			"employee",
			"employee_name",
			"company",
			"status",
			"insurance_start_date",
			"joining_date",
			"date_of_joining",
			"employee_seniority_daily_base",
		],
		order_by="employee_name asc",
	)

	data = []
	for emp in employees:
		service_start_date = get_employee_seniority_reference_date(emp)
		insurance_years = get_years_of_service(service_start_date, today)
		organization_join_date = emp.get("joining_date") or emp.get("date_of_joining")
		organization_service_text = format_organization_service_text(organization_join_date, today)
		stored_daily_base = flt(emp.get("employee_seniority_daily_base"))
		computed_daily_base = get_seniority_daily_base(
			service_start_date,
			salary_date=today,
			settings=settings,
			rule=rule,
		)
		daily_base = stored_daily_base or computed_daily_base
		monthly_base = daily_base * STANDARD_MONTH_DAYS

		data.append(
			{
				"employee": emp.get("employee") or emp.get("name"),
				"employee_name": emp.get("employee_name"),
				"insurance_start_date": service_start_date,
				"insurance_service_years": insurance_years,
				"organization_join_date": organization_join_date,
				"employee_seniority_daily_base": daily_base,
				"employee_seniority_monthly_base": monthly_base,
				"organization_service_text": organization_service_text,
			}
		)

	return data


def format_organization_service_text(joining_date, reference_date):
	join_date = getdate(joining_date) if joining_date else None
	reference_date = getdate(reference_date) if reference_date else getdate()

	if not join_date:
		return ""

	if join_date > reference_date:
		return _("۰ سال و ۰ ماه")

	years = reference_date.year - join_date.year
	months = reference_date.month - join_date.month
	if reference_date.day < join_date.day:
		months -= 1
	if months < 0:
		years -= 1
		months += 12

	if years < 0:
		years = 0
	if months < 0:
		months = 0

	return _("{0} سال و {1} ماه").format(years, months)
