import frappe


SETUP_SECTION_LABEL = "Setup"
REPORTS_SECTION_LABEL = "Reports"

PAYROLL_SETUP_LINKS = [
	("Salary Component", "Salary Component"),
	("Salary Structure", "Salary Structure"),
	("Employment Contract", "قرارداد استخدام"),
	("Overtime Type", "نوع اضافه کاری"),
	("Iran Payroll Settings", "تنظیمات حقوق و دستمزد ایران"),
	("Iran Seniority Table", "جدول پایه سنوات"),
	("Gratuity Rule", "جدول مزایای پایان خدمت"),
]


def execute():
	if not frappe.db.exists("Workspace Sidebar", "Payroll"):
		return

	sidebar = frappe.get_doc("Workspace Sidebar", "Payroll")
	items = list(sidebar.get("items") or [])
	if not items:
		return

	setup_index = next(
		(index for index, row in enumerate(items) if row.type == "Section Break" and row.label == SETUP_SECTION_LABEL),
		None,
	)
	if setup_index is None:
		return

	changed = False
	changed |= ensure_main_link(
		items,
		link_to="Employee",
		label="لیست کارمند",
		insert_after="Payroll",
		icon="users",
	)
	changed |= ensure_main_link(
		items,
		link_to="Overtime Slip",
		label="فیش اضافه کاری",
		insert_after="Salary Slip",
		icon="receipt-text",
	)
	for link_to, label in PAYROLL_SETUP_LINKS:
		changed |= ensure_setup_link(items, setup_index, link_to, label)

	if changed:
		sidebar.set("items", items)
		sidebar.save(ignore_permissions=True)


def ensure_main_link(items, link_to: str, label: str, insert_after: str | None = None, icon: str = "") -> bool:
	updated = False
	matches = [row for row in items if row.type == "Link" and row.link_to == link_to]

	if matches:
		primary = matches[0]
		if primary.label != label:
			primary.label = label
			updated = True
		if primary.link_type != "DocType":
			primary.link_type = "DocType"
			updated = True
		if primary.child != 0:
			primary.child = 0
			updated = True
		if primary.indent != 0:
			primary.indent = 0
			updated = True
		if (primary.icon or "") != icon:
			primary.icon = icon
			updated = True
		for duplicate in matches[1:]:
			items.remove(duplicate)
			updated = True
	else:
		primary = frappe._dict(
			{
				"type": "Link",
				"label": label,
				"link_type": "DocType",
				"link_to": link_to,
				"child": 0,
				"indent": 0,
				"icon": icon,
				"collapsible": 1,
				"keep_closed": 0,
				"show_arrow": 0,
			}
		)
		items.append(primary)
		updated = True

	if ensure_before_first_section(items, link_to):
		updated = True
	if insert_after and move_link_after(items, link_to, insert_after):
		updated = True

	return updated


def ensure_before_first_section(items, link_to: str) -> bool:
	row = next((item for item in items if item.type == "Link" and item.link_to == link_to), None)
	if not row:
		return False

	first_section_index = next((idx for idx, item in enumerate(items) if item.type == "Section Break"), len(items))
	row_index = items.index(row)
	if row_index < first_section_index:
		return False

	items.remove(row)
	first_section_index = next((idx for idx, item in enumerate(items) if item.type == "Section Break"), len(items))
	items.insert(first_section_index, row)
	return True


def move_link_after(items, link_to_move: str, target_link_to: str) -> bool:
	move_row = next((row for row in items if row.type == "Link" and row.link_to == link_to_move), None)
	target_row = next((row for row in items if row.type == "Link" and row.link_to == target_link_to), None)
	if not move_row or not target_row:
		return False

	current_idx = items.index(move_row)
	target_idx = items.index(target_row)
	desired_idx = target_idx + 1
	if current_idx == desired_idx:
		return False

	items.remove(move_row)
	if current_idx < desired_idx:
		desired_idx -= 1
	items.insert(desired_idx, move_row)
	return True


def ensure_setup_link(items, setup_index: int, link_to: str, label: str) -> bool:
	updated = False
	matches = [row for row in items if row.type == "Link" and row.link_to == link_to]

	if matches:
		primary = matches[0]
		if primary.label != label:
			primary.label = label
			updated = True
		if primary.link_type != "DocType":
			primary.link_type = "DocType"
			updated = True
		if primary.child != 1:
			primary.child = 1
			updated = True
		if primary.indent != 0:
			primary.indent = 0
			updated = True

		for duplicate in matches[1:]:
			items.remove(duplicate)
			updated = True
	else:
		primary = frappe._dict(
			{
				"type": "Link",
				"label": label,
				"link_type": "DocType",
				"link_to": link_to,
				"child": 1,
				"indent": 0,
				"icon": "",
				"collapsible": 1,
				"keep_closed": 0,
				"show_arrow": 0,
			}
		)
		items.append(primary)
		updated = True

	if move_link_to_setup_block(items, setup_index, link_to):
		updated = True

	return updated


def move_link_to_setup_block(items, setup_index: int, link_to: str) -> bool:
	link_row = next((row for row in items if row.type == "Link" and row.link_to == link_to), None)
	if not link_row:
		return False

	next_section_index = next(
		(index for index in range(setup_index + 1, len(items)) if items[index].type == "Section Break"),
		len(items),
	)
	setup_block_link_tos = {
		row.link_to
		for row in items[setup_index + 1 : next_section_index]
		if row.type == "Link" and row.link_type == "DocType"
	}
	desired_order = [link for link, _ in PAYROLL_SETUP_LINKS if link in setup_block_link_tos or link == link_to]
	desired_pos_in_block = desired_order.index(link_to)
	desired_idx = setup_index + 1 + desired_pos_in_block

	current_idx = items.index(link_row)
	if current_idx == desired_idx:
		return False

	items.remove(link_row)
	if current_idx < desired_idx:
		desired_idx -= 1
	items.insert(desired_idx, link_row)
	return True
