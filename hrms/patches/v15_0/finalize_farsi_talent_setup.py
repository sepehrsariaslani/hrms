import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from hrms.patches.v15_0.add_idp_and_nine_box_employee_fields import get_employee_fields
from hrms.patches.v15_0.localize_designation_labels_and_add_job_architecture import (
	get_designation_custom_fields,
)


NEW_TALENT_DOCTYPES = [
	"designation_direct_report",
	"designation_responsibility",
	"designation_soft_skill",
	"designation_kpi",
	"designation_working_condition",
	"job_family",
	"job_grade",
	"job_family_grade",
	"competency",
	"competency_behavioral_indicator",
	"competency_requirement",
	"competency_assessment",
	"competency_assessment_item",
	"career_path_map",
	"career_path_station",
	"career_path_transition",
	"career_path_transition_link",
	"career_path_certification_requirement",
	"nine_box_cycle",
	"nine_box_assessment",
	"individual_development_plan",
	"idp_competency_goal",
	"idp_development_action",
	"idp_milestone",
	"idp_review",
]

HR_WORKSPACE_CARD = "توسعه مسیر شغلی"
HR_WORKSPACE_LINKS = [
	{"label": "خانواده‌های شغلی", "link_to": "Job Family"},
	{"label": "گریدهای شغلی", "link_to": "Job Grade"},
	{"label": "مدل شایستگی", "link_to": "Competency"},
	{"label": "ارزیابی‌های شایستگی", "link_to": "Competency Assessment"},
	{"label": "نقشه‌های مسیر شغلی", "link_to": "Career Path Map"},
	{"label": "گذارهای مسیر شغلی", "link_to": "Career Path Transition"},
	{"label": "دوره‌های ۹ خانه", "link_to": "Nine Box Cycle"},
	{"label": "ارزیابی‌های ۹ خانه", "link_to": "Nine Box Assessment"},
	{"label": "برنامه‌های توسعه فردی", "link_to": "Individual Development Plan"},
]

PERFORMANCE_WORKSPACE_CARD = "جانشین‌پروری و توسعه"
PERFORMANCE_WORKSPACE_LINKS = [
	{"label": "ارزیابی‌های ۹ خانه", "link_to": "Nine Box Assessment"},
	{"label": "برنامه‌های توسعه فردی", "link_to": "Individual Development Plan"},
	{"label": "ارزیابی‌های شایستگی", "link_to": "Competency Assessment"},
]


def execute():
	reload_talent_doctypes()
	reapply_farsi_custom_fields()
	update_standard_designation_labels()
	update_workspace_links()


def reload_talent_doctypes():
	for doctype_path in NEW_TALENT_DOCTYPES:
		frappe.reload_doc("hr", "doctype", doctype_path, force=True, reset_permissions=True)


def reapply_farsi_custom_fields():
	create_custom_fields(
		{
			"Designation": get_designation_custom_fields(),
			"Employee": get_employee_fields(),
		},
		ignore_validate=True,
		update=True,
	)


def update_standard_designation_labels():
	for fieldname, label in {
		"designation_name": "عنوان شغل",
		"description": "شرح کلی شغل",
		"color": "رنگ",
	}.items():
		set_field_property("Designation", fieldname, "label", label, "Data")

	set_field_property(
		"Designation",
		"grading_model",
		"options",
		"\nمرسر\nهی گروپ\nسفارشی",
		"Text",
	)


def set_field_property(doctype, fieldname, property_name, value, property_type):
	if not frappe.get_meta(doctype).has_field(fieldname):
		return

	make_property_setter(
		doctype,
		fieldname,
		property_name,
		value,
		property_type,
		validate_fields_for_doctype=False,
	)


def update_workspace_links():
	add_links_to_workspace("HR", HR_WORKSPACE_CARD, HR_WORKSPACE_LINKS)
	add_links_to_workspace("Performance", PERFORMANCE_WORKSPACE_CARD, PERFORMANCE_WORKSPACE_LINKS)


def add_links_to_workspace(workspace_name, card_label, links):
	if not frappe.db.exists("Workspace", workspace_name):
		return

	workspace = frappe.get_doc("Workspace", workspace_name)
	rows = workspace.get("links") or []
	updated = False

	if not any(row.type == "Card Break" and row.label == card_label for row in rows):
		workspace.append(
			"links",
			{
				"type": "Card Break",
				"label": card_label,
				"link_count": 0,
			},
		)
		updated = True

	for link in links:
		existing = next(
			(
				row
				for row in (workspace.get("links") or [])
				if row.type == "Link" and row.link_type == "DocType" and row.link_to == link["link_to"]
			),
			None,
		)
		if existing:
			if existing.label != link["label"]:
				existing.label = link["label"]
				updated = True
			continue

		workspace.append(
			"links",
			{
				"type": "Link",
				"label": link["label"],
				"link_type": "DocType",
				"link_to": link["link_to"],
			},
		)
		updated = True

	if sync_card_link_count(workspace, card_label):
		updated = True

	if updated:
		workspace.save(ignore_permissions=True)


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
