import frappe

from hrms.overrides.company import make_salary_components, run_regional_setup


IRAN_COUNTRY_ALIASES = {
	"iran",
	"iran, islamic republic of",
	"islamic republic of iran",
	"ایران",
}


def execute():
	countries = frappe.get_all("Company", pluck="country", distinct=True)
	for country in countries:
		if (country or "").strip().lower() in IRAN_COUNTRY_ALIASES:
			run_regional_setup(country)
			make_salary_components(country)

	ensure_smart_attendance_report_points_to_hrms()


def ensure_smart_attendance_report_points_to_hrms():
	if not frappe.db.exists("Report", "Smart Attendance Report"):
		return

	frappe.db.set_value(
		"Report",
		"Smart Attendance Report",
		{
			"module": "HR",
			"report_name": "گزارش حضور و غیاب هوشمند",
			"ref_doctype": "Employee Checkin",
			"is_standard": "Yes",
		},
	)
