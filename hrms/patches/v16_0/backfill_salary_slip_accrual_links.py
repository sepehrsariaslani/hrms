import frappe


def execute():
	"""Restore Salary Slip links and statuses for existing group accrual entries."""
	for payroll_entry in frappe.get_all("Payroll Entry", fields=["name"]):
		journal_entry = None
		for reference in frappe.get_all(
			"Journal Entry Account",
			filters={"reference_type": "Payroll Entry", "reference_name": payroll_entry.name},
			fields=["parent"],
			order_by="creation desc",
		):
			journal = frappe.db.get_value(
				"Journal Entry", reference.parent, ["docstatus", "voucher_type"], as_dict=True
			)
			if journal and journal.docstatus == 1 and journal.voucher_type == "Journal Entry":
				journal_entry = reference.parent
				break
		if not journal_entry:
			continue

		for salary_slip in frappe.get_all(
			"Salary Slip",
			filters={"payroll_entry": payroll_entry.name, "docstatus": 1},
			fields=["name", "employee", "journal_entry"],
		):
			if salary_slip.journal_entry and salary_slip.journal_entry != journal_entry:
				continue
			frappe.db.set_value(
				"Salary Slip",
				salary_slip.name,
				{"journal_entry": journal_entry, "salary_accrual_status": "تعهد ثبت شد"},
				update_modified=False,
			)
			frappe.db.set_value(
				"Journal Entry Account",
				{"parent": journal_entry, "party_type": "Employee", "party": salary_slip.employee},
				{"reference_type": "Salary Slip", "reference_name": salary_slip.name},
				update_modified=False,
			)
		payroll_reference_row = frappe.db.get_value(
			"Journal Entry Account", {"parent": journal_entry, "party": ["in", ("", None)]}, "name"
		)
		if payroll_reference_row:
			frappe.db.set_value(
				"Journal Entry Account",
				payroll_reference_row,
				{"reference_type": "Payroll Entry", "reference_name": payroll_entry.name},
				update_modified=False,
			)
