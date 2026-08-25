import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

DEFAULT_CUTOFF = "10:00:00"


def execute():
	create_meal_coordinator_role()
	create_company_meal_fields()
	set_company_defaults()


def create_meal_coordinator_role():
	if frappe.db.exists("Role", "Meal Coordinator"):
		return

	role = frappe.new_doc("Role")
	role.role_name = "Meal Coordinator"
	role.desk_access = 1
	role.insert(ignore_permissions=True)


def create_company_meal_fields():
	create_custom_fields(
		{
			"Company": [
				{
					"fieldname": "meal_enabled",
					"fieldtype": "Check",
					"label": "Meal Module Enabled",
					"default": "1",
					"insert_after": "default_currency",
				},
				{
					"fieldname": "meal_coordinator",
					"fieldtype": "Link",
					"label": "Meal Coordinator",
					"options": "User",
					"insert_after": "meal_enabled",
				},
				{
					"fieldname": "meal_default_cutoff_time",
					"fieldtype": "Time",
					"label": "Meal Default Cutoff Time",
					"default": DEFAULT_CUTOFF,
					"insert_after": "meal_coordinator",
				},
			]
		},
		ignore_validate=True,
		update=True,
	)


def set_company_defaults():
	if frappe.db.has_column("Company", "meal_enabled"):
		frappe.db.sql(
			"""
			update `tabCompany`
			set meal_enabled = 1
			where meal_enabled is null
			"""
		)

	if frappe.db.has_column("Company", "meal_default_cutoff_time"):
		frappe.db.sql(
			"""
			update `tabCompany`
			set meal_default_cutoff_time = %s
			where ifnull(meal_default_cutoff_time, '') = ''
			""",
			(DEFAULT_CUTOFF,),
		)
