import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import delete_custom_fields


def setup():
	make_custom_fields()
	ensure_iran_payroll_settings_doc()


def uninstall():
	delete_custom_fields(get_custom_fields())


def make_custom_fields(update=True):
	create_custom_fields(get_custom_fields(), update=update)


def ensure_iran_payroll_settings_doc():
	if not frappe.db.exists("DocType", "Iran Payroll Settings"):
		return

	if not frappe.db.exists("Iran Payroll Settings"):
		frappe.get_doc({"doctype": "Iran Payroll Settings", "active_law_year": 1405}).insert(ignore_permissions=True)


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
				"fieldname": "base_pay",
				"fieldtype": "Currency",
				"label": "حقوق پایه ساعتی",
				"default": "0",
				"insert_after": "iran_payroll_section",
			},
			{
				"fieldname": "technical_bonus",
				"fieldtype": "Currency",
				"label": "حق فنی ساعتی",
				"default": "0",
				"insert_after": "base_pay",
			},
			{
				"fieldname": "daily_pay",
				"fieldtype": "Currency",
				"label": "حقوق روزانه",
				"default": "0",
				"insert_after": "technical_bonus",
			},
			{
				"fieldname": "overtime_rate",
				"fieldtype": "Currency",
				"label": "نرخ اضافه کاری ساعتی",
				"default": "0",
				"insert_after": "daily_pay",
			},
			{
				"fieldname": "absence_deduction",
				"fieldtype": "Currency",
				"label": "کسر کار ساعتی",
				"default": "0",
				"insert_after": "overtime_rate",
			},
			{
				"fieldname": "monthly_technical_bonus",
				"fieldtype": "Currency",
				"label": "حق فنی ماهیانه",
				"default": "0",
				"insert_after": "absence_deduction",
			},
			{
				"fieldname": "supervision_allowance",
				"fieldtype": "Currency",
				"label": "حق سرپرستی",
				"default": "0",
				"insert_after": "monthly_technical_bonus",
			},
			{
				"fieldname": "children_count",
				"fieldtype": "Int",
				"label": "تعداد فرزند",
				"default": "0",
				"insert_after": "supervision_allowance",
			},
			{
				"fieldname": "attendance_break_settings",
				"fieldtype": "Section Break",
				"label": "تنظیمات کسر استراحت",
				"insert_after": "children_count",
				"collapsible": 1,
			},
			{
				"fieldname": "deduct_morning_break",
				"fieldtype": "Check",
				"label": "کسر صبحانه",
				"insert_after": "attendance_break_settings",
				"default": "1",
			},
			{
				"fieldname": "morning_break_start",
				"fieldtype": "Time",
				"label": "شروع صبحانه",
				"insert_after": "deduct_morning_break",
				"default": "09:40:00",
				"depends_on": "eval:doc.deduct_morning_break",
			},
			{
				"fieldname": "morning_break_end",
				"fieldtype": "Time",
				"label": "پایان صبحانه",
				"insert_after": "morning_break_start",
				"default": "10:00:00",
				"depends_on": "eval:doc.deduct_morning_break",
			},
			{
				"fieldname": "col_break_1",
				"fieldtype": "Column Break",
				"insert_after": "morning_break_end",
			},
			{
				"fieldname": "deduct_lunch_break",
				"fieldtype": "Check",
				"label": "کسر ناهار",
				"insert_after": "col_break_1",
				"default": "1",
			},
			{
				"fieldname": "lunch_break_start",
				"fieldtype": "Time",
				"label": "شروع ناهار",
				"insert_after": "deduct_lunch_break",
				"default": "13:00:00",
				"depends_on": "eval:doc.deduct_lunch_break",
			},
			{
				"fieldname": "lunch_break_end",
				"fieldtype": "Time",
				"label": "پایان ناهار",
				"insert_after": "lunch_break_start",
				"default": "14:00:00",
				"depends_on": "eval:doc.deduct_lunch_break",
			},
			{
				"fieldname": "sec_break_2",
				"fieldtype": "Section Break",
				"insert_after": "lunch_break_end",
			},
			{
				"fieldname": "deduct_afternoon_break",
				"fieldtype": "Check",
				"label": "کسر عصرانه",
				"insert_after": "sec_break_2",
				"default": "1",
			},
			{
				"fieldname": "afternoon_break_start",
				"fieldtype": "Time",
				"label": "شروع عصرانه",
				"insert_after": "deduct_afternoon_break",
				"default": "17:15:00",
				"depends_on": "eval:doc.deduct_afternoon_break",
			},
			{
				"fieldname": "afternoon_break_end",
				"fieldtype": "Time",
				"label": "پایان عصرانه",
				"insert_after": "afternoon_break_start",
				"default": "17:35:00",
				"depends_on": "eval:doc.deduct_afternoon_break",
			},
			{
				"fieldname": "col_break_2",
				"fieldtype": "Column Break",
				"insert_after": "afternoon_break_end",
			},
			{
				"fieldname": "deduct_evening_break",
				"fieldtype": "Check",
				"label": "کسر شام",
				"insert_after": "col_break_2",
				"default": "1",
			},
			{
				"fieldname": "evening_break_start",
				"fieldtype": "Time",
				"label": "شروع شام",
				"insert_after": "deduct_evening_break",
				"default": "20:40:00",
				"depends_on": "eval:doc.deduct_evening_break",
			},
			{
				"fieldname": "evening_break_end",
				"fieldtype": "Time",
				"label": "پایان شام",
				"insert_after": "evening_break_start",
				"default": "21:00:00",
				"depends_on": "eval:doc.deduct_evening_break",
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
