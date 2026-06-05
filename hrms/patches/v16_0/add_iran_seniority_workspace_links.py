import frappe


def execute():
	if not frappe.db.exists("Workspace", "Payroll"):
		return

	workspace = frappe.get_doc("Workspace", "Payroll")
	changed = False

	changed |= ensure_workspace_link(
		workspace,
		link_to="Iran Payroll Settings",
		label="تنظیمات حقوق ایران",
		insert_after="Payroll Settings",
	)
	changed |= ensure_workspace_link(
		workspace,
		link_to="Iran Seniority Table",
		label="پایه سنوات",
		insert_after="Iran Payroll Settings",
	)

	if changed:
		workspace.save(ignore_permissions=True)


def ensure_workspace_link(workspace, link_to: str, label: str, insert_after: str | None = None) -> bool:
	rows = workspace.get("links") or []

	for row in rows:
		if row.link_to == link_to:
			updated = False
			if row.label != label:
				row.label = label
				updated = True
			return updated

	workspace.append(
		"links",
		{
			"type": "Link",
			"label": label,
			"link_type": "DocType",
			"link_to": link_to,
		},
	)
	increment_card_link_count(workspace.links, "Settings")
	if insert_after:
		reorder_link_after_target(workspace, link_to, insert_after)
	return True


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


def increment_card_link_count(rows, card_label):
	for row in rows or []:
		if row.type == "Card Break" and row.label == card_label:
			row.link_count = (row.link_count or 0) + 1
			break
