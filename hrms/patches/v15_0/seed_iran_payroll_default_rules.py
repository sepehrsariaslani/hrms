import frappe


def execute():
	if not frappe.db.exists("DocType", "Iran Payroll Settings"):
		return

	if not frappe.db.exists("Iran Payroll Settings"):
		return

	doc = frappe.get_doc("Iran Payroll Settings")
	law_year = doc.active_law_year or 1405
	updated = False

	if not doc.get("yearly_rules"):
		doc.append(
			"yearly_rules",
			{
				"law_year": law_year,
				"overtime_multiplier": doc.default_overtime_multiplier or 1.4,
				"insurance_employee_rate": 7,
				"insurance_employer_rate": 23,
				"unemployment_rate": 3,
			},
		)
		updated = True

	if doc.meta.get_field("tax_slabs") and not doc.get("tax_slabs"):
		doc.append("tax_slabs", {"law_year": law_year, "from_amount": 0, "to_amount": 0, "tax_rate": 0})
		updated = True

	if updated:
		doc.save(ignore_permissions=True)
