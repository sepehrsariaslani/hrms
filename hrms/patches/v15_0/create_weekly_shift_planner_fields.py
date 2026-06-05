import frappe
from pymysql.err import OperationalError
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Employee": [
				{
					"default": "0",
					"fieldname": "is_shift_allocator",
					"fieldtype": "Check",
					"label": "Shift Allocator",
					"insert_after": "shift_request_approver",
				},
				{
					"default": "0",
					"fieldname": "needs_shift_registration",
					"fieldtype": "Check",
					"label": "Needs Shift Registration",
					"insert_after": "is_shift_allocator",
				},
				{
					"default": "0",
					"fieldname": "has_rotational_shift",
					"fieldtype": "Check",
					"label": "Has Rotational Shift",
					"insert_after": "needs_shift_registration",
				},
				{
					"default": "0",
					"fieldname": "variable_shift",
					"fieldtype": "Check",
					"label": "Variable Shift",
					"insert_after": "has_rotational_shift",
				},
				{
					"fieldname": "forbidden_shift_days",
					"fieldtype": "Small Text", # تغییر داده شد تا پچ بدون ارور اجرا شود
					"label": "Forbidden Shift Days",
					"options": "Saturday\nSunday\nMonday\nTuesday\nWednesday\nThursday\nFriday",
					"insert_after": "variable_shift",
				},
				{
					"fieldname": "employee_shift_duty_roles",
					"fieldtype": "Table",
					"label": "Employee Shift Duty Roles",
					"options": "Employee Shift Duty Role",
					"insert_after": "forbidden_shift_days",
				},
			],
			"Shift Assignment": [
				{
					"default": "0",
					"fieldname": "generated_from_weekly_plan",
					"fieldtype": "Check",
					"label": "Generated from Weekly Shift Plan",
					"insert_after": "shift_request",
					"read_only": 1,
				},
				{
					"fieldname": "weekly_shift_plan",
					"fieldtype": "Link",
					"label": "Weekly Shift Plan",
					"options": "Weekly Shift Plan",
					"insert_after": "generated_from_weekly_plan",
					"read_only": 1,
				},
				{
					"fieldname": "weekly_shift_plan_slot",
					"fieldtype": "Data",
					"label": "Weekly Shift Plan Slot",
					"insert_after": "weekly_shift_plan",
					"read_only": 1,
				},
				{
					"default": "0",
					"fieldname": "generated_from_finalization",
					"fieldtype": "Check",
					"label": "Generated from Weekly Shift Finalization",
					"insert_after": "weekly_shift_plan_slot",
					"read_only": 1,
				},
				{
					"fieldname": "weekly_shift_finalization",
					"fieldtype": "Link",
					"label": "Weekly Shift Finalization",
					"options": "Weekly Shift Finalization",
					"insert_after": "generated_from_finalization",
					"read_only": 1,
				},
				{
					"fieldname": "weekly_shift_finalization_slot",
					"fieldtype": "Data",
					"label": "Weekly Shift Finalization Slot",
					"insert_after": "weekly_shift_finalization",
					"read_only": 1,
				},
			],
		},
		ignore_validate=True,
	)

	create_default_shift_planner_settings()
	create_default_shift_duty_roles()



def create_default_shift_planner_settings():
	if not frappe.db.exists("DocType", "Weekly Shift Planner Settings"):
		return

	morning_shift = get_first_active_shift_type()

	evening_shift_filters = {}
	if frappe.db.has_column("Shift Type", "disabled"):
		evening_shift_filters["disabled"] = 0
	if morning_shift:
		evening_shift_filters["name"] = ["!=", morning_shift]

	evening_shift = get_first_active_shift_type(evening_shift_filters)

	if morning_shift:
		frappe.db.set_single_value("Weekly Shift Planner Settings", "morning_shift_type", morning_shift)
	if evening_shift:
		frappe.db.set_single_value("Weekly Shift Planner Settings", "evening_shift_type", evening_shift)

	frappe.db.set_single_value("Weekly Shift Planner Settings", "required_days_per_week", 6)
	frappe.db.set_single_value("Weekly Shift Planner Settings", "minimum_hours_per_week", 48)
	frappe.db.set_single_value("Weekly Shift Planner Settings", "auto_generate_assignments", 1)
	frappe.db.set_single_value("Weekly Shift Planner Settings", "week_start_day", "Saturday")



def create_default_shift_duty_roles():
	if not frappe.db.exists("DocType", "Shift Duty Role"):
		return

	default_roles = ["Cashier", "Ice Cream", "Bar", "Kitchen"]
	for role in default_roles:
		if frappe.db.exists("Shift Duty Role", {"role_name": role}):
			continue

		doc = frappe.new_doc("Shift Duty Role")
		doc.role_name = role
		doc.is_active = 1
		doc.insert(ignore_permissions=True)


def get_first_active_shift_type(extra_filters: dict | None = None) -> str | None:
	filters = dict(extra_filters or {})

	# Some older benches do not have the `disabled` column in `tabShift Type`.
	if frappe.db.has_column("Shift Type", "disabled") and "disabled" not in filters:
		filters["disabled"] = 0

	try:
		return frappe.db.get_value("Shift Type", filters, "name", order_by="start_time asc")
	except OperationalError as error:
		if "Unknown column 'disabled'" not in str(error):
			raise

		filters.pop("disabled", None)
		return frappe.db.get_value("Shift Type", filters, "name", order_by="start_time asc")
