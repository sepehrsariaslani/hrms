import frappe


def execute():
	if not frappe.db.exists("Workspace Sidebar", "HR Setup"):
		return

	hr_sidebar = frappe.get_doc("Workspace Sidebar", "HR Setup")
	changed = False

	employee_rows = [
		row for row in (hr_sidebar.items or []) if row.type == "Link" and row.link_type == "DocType" and row.link_to == "Employee"
	]
	if employee_rows:
		primary = employee_rows[0]
		if primary.label != "Employee":
			primary.label = "Employee"
			changed = True
		if primary.child != 0:
			primary.child = 0
			changed = True
		if primary.indent != 0:
			primary.indent = 0
			changed = True
		if (primary.icon or "") != "users":
			primary.icon = "users"
			changed = True
		for duplicate in employee_rows[1:]:
			hr_sidebar.items.remove(duplicate)
			changed = True
	else:
		hr_sidebar.append(
			"items",
			{
				"type": "Link",
				"label": "Employee",
				"link_type": "DocType",
				"link_to": "Employee",
				"icon": "users",
				"child": 0,
				"indent": 0,
				"collapsible": 1,
				"keep_closed": 0,
				"show_arrow": 0,
			},
		)
		changed = True

	if changed:
		hr_sidebar.save(ignore_permissions=True)
