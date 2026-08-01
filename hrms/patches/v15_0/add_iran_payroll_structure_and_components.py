import frappe

from hrms.overrides.company import make_salary_components, run_regional_setup
from hrms.regional.iran.utils import IRAN_COMPONENT_NAMES, IRAN_DEDUCTION_COMPONENT_NAMES


IRAN_COUNTRY_ALIASES = {
	"iran",
	"iran, islamic republic of",
	"islamic republic of iran",
	"ایران",
}

DEFAULT_EARNINGS = [
	"Basic",
	IRAN_COMPONENT_NAMES["housing"],
	IRAN_COMPONENT_NAMES["grocery"],
	IRAN_COMPONENT_NAMES["marriage"],
	IRAN_COMPONENT_NAMES["child"],
	IRAN_COMPONENT_NAMES["seniority"],
	IRAN_COMPONENT_NAMES["technical"],
	IRAN_COMPONENT_NAMES["supervision"],
	IRAN_COMPONENT_NAMES["severance"],
	IRAN_COMPONENT_NAMES["eidi"],
]

DEFAULT_DEDUCTIONS = [
	IRAN_DEDUCTION_COMPONENT_NAMES["employee_insurance"],
	IRAN_DEDUCTION_COMPONENT_NAMES["income_tax"],
	IRAN_DEDUCTION_COMPONENT_NAMES["employer_insurance"],
]


def execute():
	companies = frappe.get_all("Company", fields=["name", "country", "default_currency"])

	for company in companies:
		country = (company.country or "").strip().lower()
		if country not in IRAN_COUNTRY_ALIASES:
			continue

		run_regional_setup(company.country)
		make_salary_components(company.country)
		ensure_default_iran_salary_structure(company.name, company.default_currency)


def ensure_default_iran_salary_structure(company: str, currency: str | None):
	structure_name = f"Iran Payroll Structure - {company}"
	if frappe.db.exists("Salary Structure", structure_name):
		return

	structure = frappe.new_doc("Salary Structure")
	structure.name = structure_name
	structure.company = company
	structure.currency = currency or frappe.db.get_value("Company", company, "default_currency")
	structure.is_active = "Yes"
	structure.payroll_frequency = "Monthly"

	for component in DEFAULT_EARNINGS:
		if frappe.db.exists("Salary Component", component):
			structure.append("earnings", {"salary_component": component})

	for component in DEFAULT_DEDUCTIONS:
		if frappe.db.exists("Salary Component", component):
			structure.append("deductions", {"salary_component": component})

	if not structure.get("earnings"):
		return

	structure.insert(ignore_permissions=True)
	if structure.docstatus == 0:
		structure.submit()
