import frappe

from hrms.overrides.company import run_regional_setup


IRAN_COUNTRY_ALIASES = {
	"iran",
	"iran, islamic republic of",
	"islamic republic of iran",
	"ایران",
}


def execute():
	refresh_iran_custom_fields()
	update_report_label()
	update_workspace_link_labels()


def refresh_iran_custom_fields():
	countries = frappe.get_all("Company", pluck="country", distinct=True)
	for country in countries:
		if (country or "").strip().lower() in IRAN_COUNTRY_ALIASES:
			run_regional_setup(country)


def update_report_label():
	if not frappe.db.exists("Report", "Smart Attendance Report"):
		return

	frappe.db.set_value("Report", "Smart Attendance Report", "report_name", "گزارش حضور و غیاب هوشمند")


def update_workspace_link_labels():
	for workspace_name, link_to, label in (
		("HR", "Smart Attendance Report", "گزارش حضور و غیاب هوشمند"),
		("Payroll", "Iran Payroll Settings", "تنظیمات حقوق ایران"),
		("Payroll", "Iran Seniority Table", "پایه سنوات"),
	):
		if not frappe.db.exists("Workspace", workspace_name):
			continue

		workspace = frappe.get_doc("Workspace", workspace_name)
		updated = False
		for row in workspace.get("links") or []:
			if row.link_to == link_to and row.label != label:
				row.label = label
				updated = True

		if updated:
			workspace.save(ignore_permissions=True)
