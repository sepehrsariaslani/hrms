import frappe


def execute():
	"""Expose salary-slip accrual entries from their Payroll Entry."""
	from hrms.regional.iran.setup import make_custom_fields

	make_custom_fields()
	if not frappe.get_meta("Journal Entry").has_field("payroll_entry_reference"):
		return

	for salary_slip in frappe.get_all(
		"Salary Slip",
		filters={"docstatus": 1, "payroll_entry": ["!=", ""], "journal_entry": ["!=", ""]},
		fields=["name", "payroll_entry", "journal_entry"],
	):
		if not frappe.db.get_value("Journal Entry", salary_slip.journal_entry, "payroll_entry_reference"):
			frappe.db.set_value(
				"Journal Entry",
				salary_slip.journal_entry,
				"payroll_entry_reference",
				salary_slip.payroll_entry,
				update_modified=False,
			)
		journal_account = frappe.db.get_value(
			"Journal Entry Account", {"parent": salary_slip.journal_entry}, "name"
		)
		if journal_account:
			frappe.db.set_value(
				"Journal Entry Account",
				journal_account,
				{"reference_type": "Payroll Entry", "reference_name": salary_slip.payroll_entry},
				update_modified=False,
			)
		frappe.db.set_value(
			"Salary Slip",
			salary_slip.name,
			"salary_accrual_status",
			"تعهد ثبت شد",
			update_modified=False,
		)
