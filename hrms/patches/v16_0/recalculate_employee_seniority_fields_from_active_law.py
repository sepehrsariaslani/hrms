import frappe


def execute():
	if not frappe.db.exists("DocType", "Employee"):
		return

	from hrms.regional.iran.utils import recalculate_iran_employee_seniority_fields

	recalculate_iran_employee_seniority_fields()
