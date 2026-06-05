import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import delete_custom_fields


def setup():
	make_custom_fields()
	ensure_iran_payroll_settings_doc()
	ensure_iran_seniority_table_doc()


def uninstall():
	delete_custom_fields(get_custom_fields())


def make_custom_fields(update=True):
	create_custom_fields(get_custom_fields(), update=update)


def ensure_iran_payroll_settings_doc():
	if not frappe.db.exists("DocType", "Iran Payroll Settings"):
		return

	if not frappe.db.exists("Iran Payroll Settings"):
		frappe.get_doc({"doctype": "Iran Payroll Settings", "active_law_year": 1405}).insert(ignore_permissions=True)


def ensure_iran_seniority_table_doc():
	if not frappe.db.exists("DocType", "Iran Seniority Table"):
		return

	fiscal_year = get_fiscal_year_by_date()
	if not fiscal_year:
		return

	if frappe.db.exists("Iran Seniority Table", {"fiscal_year": fiscal_year}):
		return

	frappe.get_doc(
		{
			"doctype": "Iran Seniority Table",
			"fiscal_year": fiscal_year,
			"enabled": 1,
		}
	).insert(ignore_permissions=True)


def get_fiscal_year_by_date(reference_date=None):
	reference_date = reference_date or frappe.utils.nowdate()
	fiscal_year = frappe.db.get_value(
		"Fiscal Year",
		{
			"year_start_date": ["<=", reference_date],
			"year_end_date": [">=", reference_date],
		},
		"name",
	)
	return fiscal_year or frappe.db.get_value("Fiscal Year", {}, "name")


def get_custom_fields():
	return {
		"Employee": [
			{
				"fieldname": "iran_payroll_section",
				"fieldtype": "Section Break",
				"label": "حقوق و دستمزد ایران",
				"insert_after": "attendance_device_id",
				"collapsible": 1,
			},
			{
				"fieldname": "daily_pay",
				"fieldtype": "Currency",
				"label": "حقوق پایه روزانه",
				"default": "0",
				"insert_after": "iran_payroll_section",
			},
			{
				"fieldname": "monthly_base_pay",
				"fieldtype": "Currency",
				"label": "حقوق پایه ماهانه",
				"default": "0",
				"read_only": 1,
				"insert_after": "daily_pay",
			},
			{
				"fieldname": "base_pay",
				"fieldtype": "Currency",
				"label": "حقوق پایه ساعتی",
				"default": "0",
				"read_only": 1,
				"insert_after": "monthly_base_pay",
			},
			{
				"fieldname": "karane",
				"fieldtype": "Currency",
				"label": "کارانه",
				"default": "0",
				"insert_after": "base_pay",
			},
			{
				"fieldname": "technical_allowance_monthly",
				"fieldtype": "Currency",
				"label": "حق فنی ماهیانه",
				"default": "0",
				"insert_after": "karane",
			},
			{
				"fieldname": "insurance_start_date",
				"fieldtype": "Date",
				"label": "تاریخ شروع بیمه",
				"insert_after": "technical_allowance_monthly",
			},
			{
				"fieldname": "insurance_service_years",
				"fieldtype": "Int",
				"label": "سابقه بیمه (سال)",
				"default": "0",
				"read_only": 1,
				"insert_after": "insurance_start_date",
			},
			{
				"fieldname": "employee_salary_type",
				"fieldtype": "Select",
				"label": "نوع حقوق",
				"options": "قراردادی\nثابت\nساعتی",
				"default": "قراردادی",
				"insert_after": "insurance_service_years",
			},
			{
				"fieldname": "fixed_monthly_salary",
				"fieldtype": "Currency",
				"label": "حقوق ثابت ماهیانه",
				"default": "0",
				"depends_on": "eval:doc.employee_salary_type=='ثابت'",
				"insert_after": "employee_salary_type",
			},
			{
				"fieldname": "employee_hourly_salary",
				"fieldtype": "Currency",
				"label": "حقوق ساعتی کارمند",
				"default": "0",
				"depends_on": "eval:doc.employee_salary_type=='ساعتی'",
				"insert_after": "fixed_monthly_salary",
			},
			{
				"fieldname": "employee_seniority_daily_base",
				"fieldtype": "Currency",
				"label": "پایه سنوات روزانه",
				"default": "0",
				"read_only": 1,
				"insert_after": "employee_hourly_salary",
			},
			{
				"fieldname": "employee_seniority_monthly_base",
				"fieldtype": "Currency",
				"label": "پایه سنوات ماهانه",
				"default": "0",
				"read_only": 1,
				"insert_after": "employee_seniority_daily_base",
			},
			{
				"fieldname": "overtime_rate",
				"fieldtype": "Currency",
				"label": "نرخ اضافه کاری ساعتی",
				"default": "0",
				"read_only": 1,
				"insert_after": "employee_seniority_monthly_base",
			},
			{
				"fieldname": "absence_deduction",
				"fieldtype": "Currency",
				"label": "کسر کار ساعتی",
				"default": "0",
				"read_only": 1,
				"insert_after": "overtime_rate",
			},
			{
				"fieldname": "supervision_allowance",
				"fieldtype": "Currency",
				"label": "حق سرپرستی ماهانه",
				"default": "0",
				"insert_after": "absence_deduction",
			},
			{
				"fieldname": "service_allowance_monthly",
				"fieldtype": "Currency",
				"label": "حق سرویس (ایاب و ذهاب) ماهانه",
				"default": "0",
				"insert_after": "supervision_allowance",
			},
			{
				"fieldname": "housing_allowance",
				"fieldtype": "Currency",
				"label": "حق مسکن",
				"default": "0",
				"read_only": 1,
				"insert_after": "service_allowance_monthly",
			},
			{
				"fieldname": "grocery_allowance",
				"fieldtype": "Currency",
				"label": "بن خواربار",
				"default": "0",
				"read_only": 1,
				"insert_after": "housing_allowance",
			},
			{
				"fieldname": "marriage_allowance",
				"fieldtype": "Currency",
				"label": "حق تاهل",
				"default": "0",
				"read_only": 1,
				"insert_after": "grocery_allowance",
			},
			{
				"fieldname": "child_allowance_per_child",
				"fieldtype": "Currency",
				"label": "حق اولاد هر فرزند",
				"default": "0",
				"read_only": 1,
				"depends_on": "eval:doc.children_count>0",
				"insert_after": "marriage_allowance",
			},
			{
				"fieldname": "child_allowance",
				"fieldtype": "Currency",
				"label": "حق اولاد",
				"default": "0",
				"read_only": 1,
				"depends_on": "eval:doc.children_count>0",
				"insert_after": "child_allowance_per_child",
			},
			{
				"fieldname": "min_hourly_wage",
				"fieldtype": "Currency",
				"label": "حداقل مزد ساعتی",
				"default": "0",
				"read_only": 1,
				"insert_after": "child_allowance",
			},
			{
				"fieldname": "total_receivable",
				"fieldtype": "Currency",
				"label": "جمع دریافتنی‌های کارمند",
				"default": "0",
				"read_only": 1,
				"insert_after": "min_hourly_wage",
			},
			{
				"fieldname": "employer_insurance_share",
				"fieldtype": "Currency",
				"label": "بیمه سهم کارفرما",
				"default": "0",
				"read_only": 1,
				"depends_on": "eval:doc.employee_salary_type=='قراردادی'",
				"insert_after": "total_receivable",
			},
			{
				"fieldname": "employee_insurance_share",
				"fieldtype": "Currency",
				"label": "بیمه سهم کارمند",
				"default": "0",
				"read_only": 1,
				"depends_on": "eval:doc.employee_salary_type=='قراردادی'",
				"insert_after": "employer_insurance_share",
			},
			{
				"fieldname": "unemployment_insurance_share",
				"fieldtype": "Currency",
				"label": "بیمه بیکاری",
				"default": "0",
				"read_only": 1,
				"depends_on": "eval:doc.employee_salary_type=='قراردادی'",
				"insert_after": "employee_insurance_share",
			},
			{
				"fieldname": "organization_monthly_cost",
				"fieldtype": "Currency",
				"label": "کل هزینه پیش‌بینی شده فرد برای سازمان",
				"default": "0",
				"read_only": 1,
				"depends_on": "eval:doc.employee_salary_type=='قراردادی'",
				"insert_after": "unemployment_insurance_share",
			},
			{
				"fieldname": "children_count",
				"fieldtype": "Int",
				"label": "تعداد فرزند",
				"default": "0",
				"insert_after": "organization_monthly_cost",
			},
		],
		"Salary Slip": [
			{
				"fieldname": "iran_attendance_summary_section",
				"fieldtype": "Section Break",
				"label": "خلاصه کارکرد هوشمند",
				"insert_after": "total_working_hours",
				"collapsible": 1,
			},
			{
				"fieldname": "required_working_hours_iran",
				"fieldtype": "Float",
				"label": "ساعات موظفی",
				"insert_after": "iran_attendance_summary_section",
				"read_only": 1,
				"default": "0",
			},
			{
				"fieldname": "worked_hours_iran",
				"fieldtype": "Float",
				"label": "ساعات کارکرد",
				"insert_after": "required_working_hours_iran",
				"read_only": 1,
				"default": "0",
			},
			{
				"fieldname": "overtime_hours_iran",
				"fieldtype": "Float",
				"label": "ساعات اضافه کاری",
				"insert_after": "worked_hours_iran",
				"read_only": 1,
				"default": "0",
			},
			{
				"fieldname": "shortage_hours_iran",
				"fieldtype": "Float",
				"label": "ساعات کسری کار",
				"insert_after": "overtime_hours_iran",
				"read_only": 1,
				"default": "0",
			},
		],
	}
