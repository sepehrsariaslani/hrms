import frappe

from hrms.overrides.company import make_salary_components, run_regional_setup
from hrms.regional.iran.utils import DEDUCTION_COMPONENTS, EARNING_COMPONENTS


IRAN_COUNTRY_ALIASES = {
	"iran",
	"iran, islamic republic of",
	"islamic republic of iran",
	"ایران",
}

DEFAULT_EARNINGS = [
	"Basic",
	EARNING_COMPONENTS["housing"],
	EARNING_COMPONENTS["grocery"],
	EARNING_COMPONENTS["marriage"],
	EARNING_COMPONENTS["child"],
	EARNING_COMPONENTS["seniority"],
	EARNING_COMPONENTS["technical"],
	EARNING_COMPONENTS["supervision"],
	EARNING_COMPONENTS["severance"],
	EARNING_COMPONENTS["eidi"],
]

DEFAULT_DEDUCTIONS = [
	DEDUCTION_COMPONENTS["employee_insurance"],
	DEDUCTION_COMPONENTS["income_tax"],
	DEDUCTION_COMPONENTS["employer_insurance"],
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
