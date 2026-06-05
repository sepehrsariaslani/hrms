import frappe


def execute():
	if frappe.db.exists("Role", "Shift Allocator"):
		return

	role = frappe.new_doc("Role")
	role.role_name = "Shift Allocator"
	role.desk_access = 1
	role.insert(ignore_permissions=True)
