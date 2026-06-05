import frappe

from hrms.overrides.company import run_regional_setup
from hrms.regional.iran.utils import recalculate_iran_employee_seniority_fields


IRAN_COUNTRY_ALIASES = {
	"iran",
	"iran, islamic republic of",
	"islamic republic of iran",
	"ایران",
}


def execute():
	if not frappe.db.exists("DocType", "Employee"):
		return

	ensure_iran_custom_fields_exist()
	set_default_salary_type_for_existing_employees()
	recalculate_iran_employee_seniority_fields()


def ensure_iran_custom_fields_exist():
	for country in frappe.get_all("Company", pluck="country", distinct=True):
		if (country or "").strip().lower() in IRAN_COUNTRY_ALIASES:
			run_regional_setup(country)
			return


def set_default_salary_type_for_existing_employees():
	if not frappe.db.has_column("Employee", "employee_salary_type"):
		return

	frappe.db.sql(
		"""
		UPDATE `tabEmployee`
		SET employee_salary_type = 'قراردادی'
		WHERE employee_salary_type IS NULL
		"""
	)
