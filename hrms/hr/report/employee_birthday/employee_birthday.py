# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.query_builder import Criterion
from frappe.query_builder.functions import Extract
from frappe.utils import getdate

from erpnext.accounts.utils import build_qb_match_conditions


def execute(filters=None):
	if not filters:
		filters = {}
	if not filters["company"]:
		frappe.throw(_("{0} is mandatory").format(_("Company")))
	columns = get_columns()
	data = get_employees(filters)

	return columns, data


def get_columns():
	return [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
		{"label": _("Date of Birth"), "fieldname": "date_of_birth", "fieldtype": "Date", "width": 100},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 120,
		},
		{
			"label": _("Designation"),
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 120,
		},
		{"label": _("Gender"), "fieldname": "gender", "fieldtype": "Data", "width": 60},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 120},
	]


def get_employees(filters):
	month = get_filtered_month(filters)
	use_jalali_month = True

	employee = frappe.qb.DocType("Employee")
	query = (
		frappe.qb.from_(employee)
		.select(
			employee.name.as_("employee"),
			employee.employee_name.as_("employee_name"),
			employee.date_of_birth.as_("date_of_birth"),
			employee.branch.as_("branch"),
			employee.department.as_("department"),
			employee.designation.as_("designation"),
			employee.gender.as_("gender"),
			employee.company.as_("company"),
		)
		.where(employee.company == filters.get("company"))
		.where(employee.status == "Active")
		.where(Criterion.all(build_qb_match_conditions("Employee")))
	)

	if not use_jalali_month:
		return query.where(Extract("month", employee.date_of_birth) == month).run(as_dict=True)

	employees = query.run(as_dict=True)
	return [row for row in employees if get_jalali_month(row.get("date_of_birth")) == month]


def get_jalali_month(gregorian_date):
	date_obj = getdate(gregorian_date)
	gy, gm, gd = date_obj.year, date_obj.month, date_obj.day

	g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
	j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]

	if (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0):
		g_days_in_month[1] = 29

	gy2 = gy - 1600
	gm2 = gm - 1
	gd2 = gd - 1

	g_day_no = 365 * gy2 + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
	for i in range(gm2):
		g_day_no += g_days_in_month[i]
	g_day_no += gd2

	j_day_no = g_day_no - 79
	j_np = j_day_no // 12053
	j_day_no %= 12053

	jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
	j_day_no %= 1461

	if j_day_no >= 366:
		jy += (j_day_no - 1) // 365
		j_day_no = (j_day_no - 1) % 365

	jm = 0
	for i in range(11):
		if j_day_no >= j_days_in_month[i]:
			j_day_no -= j_days_in_month[i]
			jm += 1
		else:
			break

	return jm + 1


def get_filtered_month(filters):
	month_value = (filters or {}).get("month")
	if month_value in (None, ""):
		frappe.throw(_("{0} is mandatory").format(_("Month")))

	month_text = str(month_value).strip()
	month_text = month_text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))

	if month_text.isdigit():
		month_no = int(month_text)
		if 1 <= month_no <= 12:
			return month_no

	month_map = {
		"jan": 1,
		"january": 1,
		"feb": 2,
		"february": 2,
		"mar": 3,
		"march": 3,
		"apr": 4,
		"april": 4,
		"may": 5,
		"jun": 6,
		"june": 6,
		"jul": 7,
		"july": 7,
		"aug": 8,
		"august": 8,
		"sep": 9,
		"sept": 9,
		"september": 9,
		"oct": 10,
		"october": 10,
		"nov": 11,
		"november": 11,
		"dec": 12,
		"december": 12,
		"فروردین": 1,
		"اردیبهشت": 2,
		"خرداد": 3,
		"تیر": 4,
		"مرداد": 5,
		"شهریور": 6,
		"مهر": 7,
		"آبان": 8,
		"آذر": 9,
		"دی": 10,
		"بهمن": 11,
		"اسفند": 12,
	}

	key = month_text.lower()
	if key in month_map:
		return month_map[key]
	if month_text in month_map:
		return month_map[month_text]

	frappe.throw(_("Invalid Month value: {0}").format(month_value))
