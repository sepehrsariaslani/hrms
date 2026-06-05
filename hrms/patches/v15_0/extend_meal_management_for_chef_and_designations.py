import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_roles()
	create_employee_and_item_custom_fields()
	backfill_employee_designation_rows()
	backfill_employee_meal_item_flags()
	assign_meal_roles_to_company_coordinators()


def create_roles():
	for role_name in ("Meal Coordinator", "Chef"):
		if frappe.db.exists("Role", role_name):
			continue
		role = frappe.new_doc("Role")
		role.role_name = role_name
		role.desk_access = 1
		role.insert(ignore_permissions=True)


def create_employee_and_item_custom_fields():
	create_custom_fields(
		{
			"Employee": [
				{
					"fieldname": "employee_designations",
					"fieldtype": "Table",
					"label": "Employee Designations",
					"options": "Employee Designation Assignment",
					"insert_after": "designation",
				}
			],
			"Item": [
				{
					"fieldname": "is_employee_meal_item",
					"fieldtype": "Check",
					"label": "Employee Meal Item",
					"default": "0",
					"insert_after": "disabled",
				}
			],
		},
		ignore_validate=True,
		update=True,
	)


def backfill_employee_designation_rows():
	if not frappe.db.exists("DocType", "Employee Designation Assignment"):
		return
	if not frappe.db.has_column("Employee", "employee_designations"):
		return

	employees = frappe.get_all(
		"Employee",
		filters={"docstatus": ("<", 2)},
		fields=["name", "designation"],
		limit=0,
	)

	for employee in employees:
		if not employee.designation:
			continue

		rows = frappe.get_all(
			"Employee Designation Assignment",
			filters={
				"parent": employee.name,
				"parenttype": "Employee",
				"parentfield": "employee_designations",
			},
			fields=["name", "designation", "is_primary", "idx"],
			order_by="idx asc",
			limit=0,
		)

		if not rows:
			row = frappe.get_doc(
				{
					"doctype": "Employee Designation Assignment",
					"parent": employee.name,
					"parenttype": "Employee",
					"parentfield": "employee_designations",
					"designation": employee.designation,
					"is_primary": 1,
					"idx": 1,
				}
			)
			row.insert(ignore_permissions=True)
			continue

		designations = {row.designation for row in rows if row.designation}
		if employee.designation not in designations:
			row = frappe.get_doc(
				{
					"doctype": "Employee Designation Assignment",
					"parent": employee.name,
					"parenttype": "Employee",
					"parentfield": "employee_designations",
					"designation": employee.designation,
					"is_primary": 0,
					"idx": len(rows) + 1,
				}
			)
			row.insert(ignore_permissions=True)
			rows.append({"name": row.name, "is_primary": 0})

		primary_rows = [row for row in rows if row.get("is_primary")]
		if not primary_rows and rows:
			frappe.db.set_value(
				"Employee Designation Assignment",
				rows[0].get("name"),
				"is_primary",
				1,
				update_modified=False,
			)
		elif len(primary_rows) > 1:
			keep = primary_rows[0].get("name")
			for row in primary_rows[1:]:
				frappe.db.set_value(
					"Employee Designation Assignment",
					row.get("name"),
					"is_primary",
					0,
					update_modified=False,
				)


def backfill_employee_meal_item_flags():
	if not frappe.db.has_column("Item", "is_employee_meal_item"):
		return

	if frappe.db.exists("DocType", "Employee Meal Catalog"):
		frappe.db.sql(
			"""
			update `tabItem` item
			inner join `tabEmployee Meal Catalog` cat on cat.item = item.name
			set item.is_employee_meal_item = 1
			where ifnull(item.is_employee_meal_item, 0) = 0
			"""
		)


def assign_meal_roles_to_company_coordinators():
	if not frappe.db.has_column("Company", "meal_coordinator"):
		return

	users = frappe.get_all("Company", pluck="meal_coordinator")
	for user_id in users:
		if not user_id or user_id in {"Administrator", "Guest"}:
			continue
		try:
			user = frappe.get_doc("User", user_id)
			user.flags.ignore_permissions = True
			user.add_roles("Meal Coordinator", "Chef")
		except Exception:
			continue
