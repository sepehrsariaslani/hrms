import frappe

from hrms.overrides.company import make_salary_components


IRAN_COUNTRY_ALIASES = {
	"iran",
	"iran, islamic republic of",
	"islamic republic of iran",
	"ایران",
}


def execute():
	companies = frappe.get_all("Company", fields=["name", "country"])

	for company in companies:
		country = (company.country or "").strip().lower()
		if country not in IRAN_COUNTRY_ALIASES:
			continue

		make_salary_components(company.country)
