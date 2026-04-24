import json

import frappe


ROOT_WORKSPACE_CANDIDATES = ("Human Resources", "HR")

HR_TALENT_CARD = "توسعه مسیر شغلی"
HR_TALENT_LINKS = [
	("خانواده‌های شغلی", "Job Family"),
	("گریدهای شغلی", "Job Grade"),
	("مدل شایستگی", "Competency"),
	("ارزیابی‌های شایستگی", "Competency Assessment"),
	("نقشه‌های مسیر شغلی", "Career Path Map"),
	("گذارهای مسیر شغلی", "Career Path Transition"),
	("دوره‌های ۹ خانه", "Nine Box Cycle"),
	("ارزیابی‌های ۹ خانه", "Nine Box Assessment"),
	("برنامه‌های توسعه فردی", "Individual Development Plan"),
]
HR_TALENT_SHORTCUTS = [
	("خانواده‌های شغلی", "Job Family"),
	("گریدهای شغلی", "Job Grade"),
	("برنامه‌های توسعه فردی", "Individual Development Plan"),
]

PERFORMANCE_TALENT_CARD = "جانشین‌پروری و توسعه"
PERFORMANCE_TALENT_LINKS = [
	("ارزیابی‌های ۹ خانه", "Nine Box Assessment"),
	("برنامه‌های توسعه فردی", "Individual Development Plan"),
	("ارزیابی‌های شایستگی", "Competency Assessment"),
]
PERFORMANCE_TALENT_SHORTCUTS = [
	("ارزیابی‌های ۹ خانه", "Nine Box Assessment"),
	("برنامه‌های توسعه فردی", "Individual Development Plan"),
]

WEEKLY_SHIFT_CARD = "برنامه‌ریزی شیفت هفتگی"
WEEKLY_SHIFT_LINKS = [
	("تنظیمات برنامه‌ریز شیفت هفتگی", "Weekly Shift Planner Settings"),
	("برنامه شیفت هفتگی", "Weekly Shift Plan"),
	("نهایی‌سازی شیفت هفتگی", "Weekly Shift Finalization"),
]
WEEKLY_SHIFT_SHORTCUTS = [("برنامه شیفت هفتگی", "Weekly Shift Plan")]


def sync_hr_workspace_setup():
	root_workspace = get_hr_root_workspace()
	if root_workspace:
		ensure_workspace_extensions(
			root_workspace,
			HR_TALENT_CARD,
			HR_TALENT_LINKS,
			shortcuts=HR_TALENT_SHORTCUTS,
			after_cards=["Other Reports"],
		)

	ensure_workspace_extensions(
		"Performance",
		PERFORMANCE_TALENT_CARD,
		PERFORMANCE_TALENT_LINKS,
		shortcuts=PERFORMANCE_TALENT_SHORTCUTS,
		after_cards=["Reports"],
	)

	ensure_workspace_extensions(
		"Shift & Attendance",
		WEEKLY_SHIFT_CARD,
		WEEKLY_SHIFT_LINKS,
		shortcuts=WEEKLY_SHIFT_SHORTCUTS,
		after_cards=["Shifts"],
	)


def get_hr_root_workspace():
	for workspace in ROOT_WORKSPACE_CANDIDATES:
		if frappe.db.exists("Workspace", workspace):
			return workspace
	return None


def ensure_workspace_extensions(workspace_name, card_label, links, shortcuts=None, after_cards=None):
	if not frappe.db.exists("Workspace", workspace_name):
		return

	workspace = frappe.get_doc("Workspace", workspace_name)
	updated = False

	if ensure_workspace_card_links(workspace, card_label, links):
		updated = True
	if ensure_content_card(workspace, card_label, after_cards or []):
		updated = True
	if ensure_workspace_shortcuts(workspace, shortcuts or []):
		updated = True
	if ensure_content_shortcuts(workspace, [label for label, _ in (shortcuts or [])]):
		updated = True

	if updated:
		workspace.save(ignore_permissions=True)


def ensure_workspace_card_links(workspace, card_label, links):
	updated = False
	rows = workspace.get("links") or []

	if not any(row.type == "Card Break" and row.label == card_label for row in rows):
		workspace.append("links", {"type": "Card Break", "label": card_label, "link_count": 0})
		rows = workspace.get("links") or []
		updated = True

	for label, link_to in links:
		if not frappe.db.exists("DocType", link_to):
			continue

		existing = next(
			(
				row
				for row in rows
				if row.type == "Link" and row.link_type == "DocType" and row.link_to == link_to
			),
			None,
		)
		if existing:
			if existing.label != label:
				existing.label = label
				updated = True
			continue

		workspace.append(
			"links",
			{
				"type": "Link",
				"label": label,
				"link_type": "DocType",
				"link_to": link_to,
			},
		)
		rows = workspace.get("links") or []
		updated = True

	if sync_card_link_count(workspace, card_label):
		updated = True

	return updated


def ensure_content_card(workspace, card_label, after_cards):
	content = parse_workspace_content(workspace.content)
	if any(
		block.get("type") == "card" and (block.get("data") or {}).get("card_name") == card_label
		for block in content
	):
		return False

	insert_at = len(content)
	for index, block in enumerate(content):
		if block.get("type") != "card":
			continue
		card_name = (block.get("data") or {}).get("card_name")
		if card_name in after_cards:
			insert_at = index + 1

	content.insert(insert_at, {"type": "card", "data": {"card_name": card_label, "col": 4}})
	workspace.content = json.dumps(content, ensure_ascii=False)
	return True


def ensure_workspace_shortcuts(workspace, shortcuts):
	updated = False
	rows = workspace.get("shortcuts") or []

	for label, link_to in shortcuts:
		if not frappe.db.exists("DocType", link_to):
			continue

		existing = next(
			(row for row in rows if row.type == "DocType" and row.link_to == link_to),
			None,
		)
		if existing:
			if existing.label != label:
				existing.label = label
				updated = True
			continue

		workspace.append(
			"shortcuts",
			{
				"type": "DocType",
				"label": label,
				"link_to": link_to,
				"doc_view": "List",
				"color": "Grey",
			},
		)
		rows = workspace.get("shortcuts") or []
		updated = True

	return updated


def ensure_content_shortcuts(workspace, shortcut_labels):
	if not shortcut_labels:
		return False

	content = parse_workspace_content(workspace.content)
	updated = False
	spacer_index = next((idx for idx, block in enumerate(content) if block.get("type") == "spacer"), len(content))

	for label in shortcut_labels:
		exists = any(
			block.get("type") == "shortcut"
			and (block.get("data") or {}).get("shortcut_name") == label
			for block in content
		)
		if exists:
			continue

		content.insert(spacer_index, {"type": "shortcut", "data": {"shortcut_name": label, "col": 3}})
		spacer_index += 1
		updated = True

	if updated:
		workspace.content = json.dumps(content, ensure_ascii=False)

	return updated


def parse_workspace_content(raw_content):
	if not raw_content:
		return []
	if isinstance(raw_content, list):
		return raw_content
	try:
		parsed = json.loads(raw_content)
	except Exception:
		return []
	return parsed if isinstance(parsed, list) else []


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
