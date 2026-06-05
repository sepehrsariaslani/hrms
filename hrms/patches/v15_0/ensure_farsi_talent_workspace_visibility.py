import json

import frappe


HR_WORKSPACE = "Human Resources"
HR_WORKSPACE_FALLBACK = "HR"
PERFORMANCE_WORKSPACE = "Performance"

HR_CARD_LABEL = "توسعه مسیر شغلی"
PERFORMANCE_CARD_LABEL = "جانشین‌پروری و توسعه"

HR_LINKS = [
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

PERFORMANCE_LINKS = [
	("ارزیابی‌های ۹ خانه", "Nine Box Assessment"),
	("برنامه‌های توسعه فردی", "Individual Development Plan"),
	("ارزیابی‌های شایستگی", "Competency Assessment"),
]

HR_SHORTCUTS = [
	("خانواده‌های شغلی", "Job Family"),
	("گریدهای شغلی", "Job Grade"),
	("برنامه‌های توسعه فردی", "Individual Development Plan"),
]

PERFORMANCE_SHORTCUTS = [
	("ارزیابی‌های ۹ خانه", "Nine Box Assessment"),
	("برنامه‌های توسعه فردی", "Individual Development Plan"),
]

FA_DOCTYPE_TRANSLATIONS = {
	"Designation Direct Report": "گزارش‌های مستقیم شغل",
	"Designation Responsibility": "مسئولیت‌های شغل",
	"Designation Soft Skill": "مهارت نرم شغل",
	"Designation KPI": "شاخص عملکرد شغل",
	"Designation Working Condition": "شرایط کاری شغل",
	"Job Family": "خانواده شغلی",
	"Job Grade": "گرید شغلی",
	"Job Family Grade": "سطح خانواده شغلی",
	"Competency": "شایستگی",
	"Competency Behavioral Indicator": "مصداق رفتاری شایستگی",
	"Competency Requirement": "الزام شایستگی",
	"Competency Assessment": "ارزیابی شایستگی",
	"Competency Assessment Item": "آیتم ارزیابی شایستگی",
	"Career Path Map": "نقشه مسیر شغلی",
	"Career Path Station": "ایستگاه مسیر شغلی",
	"Career Path Transition": "گذار مسیر شغلی",
	"Career Path Transition Link": "لینک گذار مسیر شغلی",
	"Career Path Certification Requirement": "الزام گواهینامه مسیر شغلی",
	"Nine Box Cycle": "دوره ۹ خانه",
	"Nine Box Assessment": "ارزیابی ۹ خانه",
	"Individual Development Plan": "برنامه توسعه فردی",
	"IDP Competency Goal": "هدف شایستگی برنامه توسعه فردی",
	"IDP Development Action": "اقدام توسعه‌ای برنامه توسعه فردی",
	"IDP Milestone": "مایلستون برنامه توسعه فردی",
	"IDP Review": "بازبینی برنامه توسعه فردی",
}


def execute():
	upsert_doctype_translations()
	hr_workspace_name = get_hr_workspace_name()
	update_workspace(
		hr_workspace_name,
		HR_CARD_LABEL,
		HR_LINKS,
		shortcuts=HR_SHORTCUTS,
		after_cards=["Other Reports"],
	)
	update_workspace(
		PERFORMANCE_WORKSPACE,
		PERFORMANCE_CARD_LABEL,
		PERFORMANCE_LINKS,
		shortcuts=PERFORMANCE_SHORTCUTS,
		after_cards=["Reports"],
	)


def upsert_doctype_translations():
	for source_text, translated_text in FA_DOCTYPE_TRANSLATIONS.items():
		existing = frappe.get_all(
			"Translation",
			filters={"language": "fa", "source_text": source_text},
			fields=["name", "translated_text"],
			limit=1,
		)
		if existing:
			row = existing[0]
			if row.translated_text != translated_text:
				frappe.db.set_value(
					"Translation",
					row.name,
					"translated_text",
					translated_text,
					update_modified=False,
				)
			continue

		doc = frappe.new_doc("Translation")
		doc.language = "fa"
		doc.source_text = source_text
		doc.translated_text = translated_text
		doc.insert(ignore_permissions=True)


def get_hr_workspace_name():
	if frappe.db.exists("Workspace", HR_WORKSPACE):
		return HR_WORKSPACE
	return HR_WORKSPACE_FALLBACK


def update_workspace(workspace_name, card_label, links, shortcuts=None, after_cards=None):
	if not frappe.db.exists("Workspace", workspace_name):
		return

	workspace = frappe.get_doc("Workspace", workspace_name)
	updated = False

	if ensure_card_links(workspace, card_label, links):
		updated = True
	if ensure_content_card(workspace, card_label, after_cards=after_cards or []):
		updated = True
	if ensure_shortcuts(workspace, shortcuts or []):
		updated = True
	if ensure_content_shortcuts(workspace, [label for label, _ in (shortcuts or [])]):
		updated = True

	if updated:
		workspace.save(ignore_permissions=True)


def ensure_card_links(workspace, card_label, links):
	rows = workspace.get("links") or []
	updated = False

	if not any(row.type == "Card Break" and row.label == card_label for row in rows):
		workspace.append("links", {"type": "Card Break", "label": card_label, "link_count": 0})
		rows = workspace.get("links") or []
		updated = True

	for label, link_to in links:
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


def ensure_content_card(workspace, card_label, after_cards=None):
	after_cards = after_cards or []
	content = parse_workspace_content(workspace.content)

	if any(
		block.get("type") == "card" and (block.get("data") or {}).get("card_name") == card_label
		for block in content
	):
		return False

	insert_at = len(content)
	for idx, block in enumerate(content):
		if block.get("type") != "card":
			continue
		card_name = (block.get("data") or {}).get("card_name")
		if card_name in after_cards:
			insert_at = idx + 1

	content.insert(insert_at, {"type": "card", "data": {"card_name": card_label, "col": 4}})
	workspace.content = json.dumps(content, ensure_ascii=False)
	return True


def ensure_shortcuts(workspace, shortcuts):
	updated = False
	rows = workspace.get("shortcuts") or []
	for label, link_to in shortcuts:
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

		content.insert(
			spacer_index,
			{"type": "shortcut", "data": {"shortcut_name": label, "col": 3}},
		)
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
