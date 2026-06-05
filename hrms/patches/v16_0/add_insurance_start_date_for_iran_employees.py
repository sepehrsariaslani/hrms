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
	backfill_insurance_start_date_from_joining_date()
	recalculate_iran_employee_seniority_fields()


def ensure_iran_custom_fields_exist():
	for country in frappe.get_all("Company", pluck="country", distinct=True):
		if (country or "").strip().lower() in IRAN_COUNTRY_ALIASES:
			run_regional_setup(country)
			return


def backfill_insurance_start_date_from_joining_date():
	if not frappe.db.has_column("Employee", "insurance_start_date"):
		return

	frappe.db.sql(
		"""
		UPDATE `tabEmployee`
		SET insurance_start_date = date_of_joining
		WHERE insurance_start_date IS NULL
		  AND date_of_joining IS NOT NULL
		"""
	)
