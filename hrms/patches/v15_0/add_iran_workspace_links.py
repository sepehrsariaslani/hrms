import frappe


def execute():
	add_hr_smart_attendance_link()
	add_payroll_settings_link()


def add_hr_smart_attendance_link():
	if not frappe.db.exists("Workspace", "HR"):
		return

	workspace = frappe.get_doc("Workspace", "HR")
	if any(link.link_to == "Smart Attendance Report" for link in workspace.links or []):
		return

	workspace.append("links", {
			"type": "Link",
			"label": "گزارش حضور و غیاب هوشمند",
			"link_type": "Report",
			"link_to": "Smart Attendance Report",
			"is_query_report": 1,
			"dependencies": "Attendance",
	})
	increment_card_link_count(workspace.links, "Key Reports")
	reorder_link_after_target(workspace, "Smart Attendance Report", "Monthly Attendance Sheet")
	workspace.save(ignore_permissions=True)


def add_payroll_settings_link():
	if not frappe.db.exists("Workspace", "Payroll"):
		return

	workspace = frappe.get_doc("Workspace", "Payroll")
	if any(link.link_to == "Iran Payroll Settings" for link in workspace.links or []):
		return

	workspace.append("links", {
			"type": "Link",
			"label": "تنظیمات حقوق ایران",
			"link_type": "DocType",
			"link_to": "Iran Payroll Settings",
	})
	increment_card_link_count(workspace.links, "Settings")
	reorder_link_after_target(workspace, "Iran Payroll Settings", "Payroll Settings")
	workspace.save(ignore_permissions=True)


def reorder_link_after_target(workspace, link_to_move, target_link_to):
	rows = workspace.get("links") or []
	move_row = None
	target_idx = None

	for idx, row in enumerate(rows):
		if row.link_to == link_to_move:
			move_row = row
		if row.link_to == target_link_to:
			target_idx = idx

	if not move_row or target_idx is None:
		return

	rows.remove(move_row)
	rows.insert(target_idx + 1, move_row)


# Keep card counts in sync for workspace cards.
def increment_card_link_count(rows, card_label):
	for row in rows or []:
		if row.type == "Card Break" and row.label == card_label:
			row.link_count = (row.link_count or 0) + 1
			break
