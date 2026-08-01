import frappe

from hrms.overrides.company import make_salary_components, run_regional_setup


IRAN_COUNTRY_ALIASES = {
	"iran",
	"iran, islamic republic of",
	"islamic republic of iran",
	"ایران",
}


def execute():
	companies = frappe.get_all("Company", fields=["name", "country", "default_currency"])

	for company in companies:
		country = (company.country or "").strip().lower()
		if country not in IRAN_COUNTRY_ALIASES:
			continue

		run_regional_setup(company.country)
		make_salary_components(company.country)
