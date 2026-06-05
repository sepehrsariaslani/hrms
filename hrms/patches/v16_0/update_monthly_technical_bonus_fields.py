import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

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
	hide_daily_technical_bonus_field()
	backfill_technical_allowance_monthly()
	recalculate_iran_employee_seniority_fields()


def ensure_iran_custom_fields_exist():
	for country in frappe.get_all("Company", pluck="country", distinct=True):
		if (country or "").strip().lower() in IRAN_COUNTRY_ALIASES:
			run_regional_setup(country)
			return


def hide_daily_technical_bonus_field():
	make_property_setter(
		"Employee",
		"technical_bonus_daily",
		"hidden",
		1,
		"Check",
		validate_fields_for_doctype=False,
	)


def backfill_technical_allowance_monthly():
	if not frappe.db.has_column("Employee", "technical_allowance_monthly"):
		return

	frappe.db.sql(
		"""
		UPDATE `tabEmployee`
		SET technical_allowance_monthly = monthly_technical_bonus
		WHERE technical_allowance_monthly IS NULL
		  AND monthly_technical_bonus IS NOT NULL
		"""
	)
