import frappe


SETTINGS_CARD_LABEL = "Settings"

PAYROLL_SETTINGS_LINKS = [
	("Employment Contract", "قرارداد استخدام", "Payroll Settings"),
	("Iran Payroll Settings", "تنظیمات حقوق و دستمزد ایران", "Payroll Settings"),
	("Iran Seniority Table", "جدول پایه سنوات", "Iran Payroll Settings"),
	("Gratuity Rule", "جدول مزایای پایان خدمت", "Iran Seniority Table"),
]


def execute():
	if not frappe.db.exists("Workspace", "Payroll"):
		return

	workspace = frappe.get_doc("Workspace", "Payroll")
	changed = False

	for link_to, label, insert_after in PAYROLL_SETTINGS_LINKS:
		changed |= ensure_workspace_link(
			workspace,
			link_to=link_to,
			label=label,
			insert_after=insert_after,
		)

	changed |= sync_card_link_count(workspace, SETTINGS_CARD_LABEL)

	if changed:
		workspace.save(ignore_permissions=True)


def ensure_workspace_link(workspace, link_to: str, label: str, insert_after: str | None = None) -> bool:
	rows = workspace.get("links") or []
	matches = [row for row in rows if row.link_to == link_to]
	updated = False

	if matches:
		primary = matches[0]
		if primary.label != label:
			primary.label = label
			updated = True
		if primary.link_type != "DocType":
			primary.link_type = "DocType"
			updated = True
		if primary.type != "Link":
			primary.type = "Link"
			updated = True
		if primary.hidden != 0:
			primary.hidden = 0
			updated = True

		for duplicate in matches[1:]:
			workspace.links.remove(duplicate)
			updated = True
	else:
		workspace.append(
			"links",
			{
				"type": "Link",
				"label": label,
				"hidden": 0,
				"link_type": "DocType",
				"link_to": link_to,
			},
		)
		updated = True

	if insert_after and reorder_link_after_target(workspace, link_to, insert_after):
		updated = True

	return updated


def reorder_link_after_target(workspace, link_to_move: str, target_link_to: str) -> bool:
	rows = workspace.get("links") or []
	move_row = None
	target_idx = None

	for idx, row in enumerate(rows):
		if row.link_to == link_to_move and row.type == "Link":
			move_row = row
		if row.link_to == target_link_to and row.type == "Link":
			target_idx = idx

	if not move_row or target_idx is None:
		return False

	current_idx = rows.index(move_row)
	desired_idx = target_idx + 1

	if current_idx == desired_idx:
		return False

	rows.remove(move_row)
	if current_idx < desired_idx:
		desired_idx -= 1
	rows.insert(desired_idx, move_row)
	return True


def sync_card_link_count(workspace, card_label: str) -> bool:
	rows = workspace.get("links") or []
	for index, row in enumerate(rows):
		if row.type != "Card Break" or row.label != card_label:
			continue

		count = 0
		for link_row in rows[index + 1 :]:
			if link_row.type == "Card Break":
				break
			if link_row.type == "Link":
				count += 1

		if (row.link_count or 0) != count:
			row.link_count = count
			return True
		return False

	return False
