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
	make_monthly_technical_fields_editable()
	hide_hourly_technical_field()
	recalculate_iran_employee_seniority_fields()


def ensure_iran_custom_fields_exist():
	for country in frappe.get_all("Company", pluck="country", distinct=True):
		if (country or "").strip().lower() in IRAN_COUNTRY_ALIASES:
			run_regional_setup(country)
			return


def make_monthly_technical_fields_editable():
	for fieldname in ("monthly_technical_bonus", "technical_allowance_monthly"):
		make_property_setter(
			"Employee",
			fieldname,
			"read_only",
			0,
			"Check",
			validate_fields_for_doctype=False,
		)


def hide_hourly_technical_field():
	make_property_setter(
		"Employee",
		"technical_bonus",
		"hidden",
		1,
		"Check",
		validate_fields_for_doctype=False,
	)
