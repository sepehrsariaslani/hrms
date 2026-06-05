import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


CUSTOM_FIELD_INSERT_AFTER_UPDATES = {
	# Keep attendance content in Attendance & Leaves tab.
	"attendance_device_info_section": "holiday_list",
	"custom_attendance_device_mappings": "attendance_device_info_section",
	"approvers_section": "custom_attendance_device_mappings",
	"expense_approver": "approvers_section",
	"leave_approver": "expense_approver",
	"column_break_45": "leave_approver",
	"shift_request_approver": "column_break_45",
	"is_shift_allocator": "shift_request_approver",
	"needs_shift_registration": "is_shift_allocator",
	"has_rotational_shift": "needs_shift_registration",
	"variable_shift": "has_rotational_shift",
	"forbidden_shift_days": "variable_shift",
	"employee_shift_duty_roles": "forbidden_shift_days",
	# Keep payroll-related fields in Salary tab.
	"salary_cb": "salary_mode",
	"payroll_cost_center": "salary_cb",
	"iran_payroll_section": "payroll_cost_center",
	"daily_pay": "iran_payroll_section",
	"monthly_base_pay": "daily_pay",
	"base_pay": "monthly_base_pay",
	"technical_bonus_daily": "base_pay",
	"monthly_technical_bonus": "technical_bonus_daily",
	"technical_bonus": "monthly_technical_bonus",
	"employee_seniority_daily_base": "technical_bonus",
	"employee_seniority_monthly_base": "employee_seniority_daily_base",
	"overtime_rate": "employee_seniority_monthly_base",
	"absence_deduction": "overtime_rate",
	"supervision_allowance": "absence_deduction",
	"housing_allowance": "supervision_allowance",
	"grocery_allowance": "housing_allowance",
	"marriage_allowance": "grocery_allowance",
	"child_allowance_per_child": "marriage_allowance",
	"child_allowance": "child_allowance_per_child",
	"min_hourly_wage": "child_allowance",
	"total_receivable": "min_hourly_wage",
}


def _set_custom_field_insert_after(fieldname, insert_after):
	if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": fieldname}):
		return
	frappe.db.set_value(
		"Custom Field",
		{"dt": "Employee", "fieldname": fieldname},
		"insert_after",
		insert_after,
		update_modified=False,
	)


def execute():
	if not frappe.db.exists("DocType", "Employee"):
		return

	for fieldname, insert_after in CUSTOM_FIELD_INSERT_AFTER_UPDATES.items():
		_set_custom_field_insert_after(fieldname, insert_after)

	# Keep these base fields in their expected place in Overview tab.
	make_property_setter(
		"Employee",
		"date_of_joining",
		"insert_after",
		"column_break1",
		"Data",
		validate_fields_for_doctype=False,
	)
	make_property_setter(
		"Employee",
		"status",
		"insert_after",
		"date_of_joining",
		"Data",
		validate_fields_for_doctype=False,
	)

	# Make important codes visible in the form again.
	make_property_setter(
		"Employee",
		"employee_number",
		"hidden",
		0,
		"Check",
		validate_fields_for_doctype=False,
	)
	make_property_setter(
		"Employee",
		"attendance_device_id",
		"hidden",
		0,
		"Check",
		validate_fields_for_doctype=False,
	)
	make_property_setter(
		"Employee",
		"attendance_device_id",
		"read_only",
		0,
		"Check",
		validate_fields_for_doctype=False,
	)

	frappe.clear_cache(doctype="Employee")
