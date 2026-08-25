import frappe


REPORT_NAME = "Insurance Seniority Report"
REPORT_LABEL = "سنوات در بیمه"
REPORTS_SECTION_LABEL = "Reports"


def execute():
	if frappe.db.exists("Workspace", "Payroll"):
		sync_payroll_workspace_links()

	if frappe.db.exists("Workspace Sidebar", "Payroll"):
		sync_payroll_workspace_sidebar()


def sync_payroll_workspace_links():
	workspace = frappe.get_doc("Workspace", "Payroll")
	changed = ensure_workspace_report_link(workspace)
	changed |= sync_card_link_count(workspace, REPORTS_SECTION_LABEL)
	if changed:
		workspace.save(ignore_permissions=True)


def ensure_workspace_report_link(workspace):
	rows = workspace.get("links") or []
	matches = [row for row in rows if row.link_type == "Report" and row.link_to == REPORT_NAME]
	updated = False

	if matches:
		primary = matches[0]
		if primary.label != REPORT_LABEL:
			primary.label = REPORT_LABEL
			updated = True
		if (primary.is_query_report or 0) != 0:
			primary.is_query_report = 0
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
				"label": REPORT_LABEL,
				"link_type": "Report",
				"link_to": REPORT_NAME,
				"is_query_report": 0,
				"hidden": 0,
			},
		)
		updated = True

	return updated


def sync_card_link_count(workspace, card_label):
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


def sync_payroll_workspace_sidebar():
	sidebar = frappe.get_doc("Workspace Sidebar", "Payroll")
	items = list(sidebar.get("items") or [])
	if not items:
		return

	changed = ensure_sidebar_report_link(items)
	if changed:
		sidebar.set("items", items)
		sidebar.save(ignore_permissions=True)


def ensure_sidebar_report_link(items):
	reports_section_index = next(
		(index for index, row in enumerate(items) if row.type == "Section Break" and row.label == REPORTS_SECTION_LABEL),
		None,
	)
	if reports_section_index is None:
		return False

	next_section_index = next(
		(index for index in range(reports_section_index + 1, len(items)) if items[index].type == "Section Break"),
		len(items),
	)

	report_candidates = [
		row for row in items if row.type == "Link" and row.link_type == "Report" and row.link_to == REPORT_NAME
	]
	updated = False

	if report_candidates:
		primary = report_candidates[0]
		if primary.label != REPORT_LABEL:
			primary.label = REPORT_LABEL
			updated = True
		if primary.child != 1:
			primary.child = 1
			updated = True
		if primary.indent != 0:
			primary.indent = 0
			updated = True
		for duplicate in report_candidates[1:]:
			items.remove(duplicate)
			updated = True
	else:
		primary = frappe._dict(
			{
				"type": "Link",
				"label": REPORT_LABEL,
				"link_type": "Report",
				"link_to": REPORT_NAME,
				"child": 1,
				"indent": 0,
				"icon": "",
				"collapsible": 1,
				"keep_closed": 0,
				"show_arrow": 0,
			}
		)
		items.insert(next_section_index, primary)
		updated = True

	current_index = items.index(primary)
	if not (reports_section_index < current_index < next_section_index):
		items.remove(primary)
		next_section_index = next(
			(index for index in range(reports_section_index + 1, len(items)) if items[index].type == "Section Break"),
			len(items),
		)
		items.insert(next_section_index, primary)
		updated = True

	return updated
