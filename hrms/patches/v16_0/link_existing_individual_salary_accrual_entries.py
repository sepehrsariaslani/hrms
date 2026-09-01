import frappe


def execute():
	"""Show existing individual accrual entries in Salary Slip Connections."""
	from hrms.regional.iran.setup import make_custom_fields

	make_custom_fields()
	for salary_slip in frappe.get_all(
		"Salary Slip",
		filters={"journal_entry": ["!=", ""]},
		fields=["name", "journal_entry"],
	):
		if frappe.db.exists("Journal Entry", salary_slip.journal_entry):
			frappe.db.set_value(
				"Journal Entry",
				salary_slip.journal_entry,
				"salary_slip_reference",
				salary_slip.name,
				update_modified=False,
			)
