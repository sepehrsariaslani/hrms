import frappe
from frappe.utils import flt, getdate


def repair_leave_application_metrics(
	application_names=None,
	employee=None,
	from_date=None,
	to_date=None,
	dry_run=True,
):
	"""Recalculate leave metrics and rebuild ledgers for submitted leave applications."""

	filters = {"docstatus": 1}

	if application_names:
		if isinstance(application_names, str):
			application_names = [d.strip() for d in application_names.split(",") if d.strip()]
		filters["name"] = ["in", application_names]

	if employee:
		filters["employee"] = employee

	if from_date:
		filters["from_date"] = [">=", getdate(from_date)]

	if to_date:
		filters.setdefault("to_date", ["<=", getdate(to_date)])

	applications = frappe.get_all(
		"Leave Application",
		filters=filters,
		fields=["name", "employee", "from_date", "to_date", "total_leave_days", "total_leave_hours"],
		order_by="from_date asc, name asc",
	)

	results = []
	base_flags = getattr(frappe.local, "flags", None)
	previous_in_patch = getattr(base_flags, "in_patch", False) if base_flags else False
	frappe.flags.in_patch = True

	try:
		for row in applications:
			doc = frappe.get_doc("Leave Application", row.name)
			old_days = flt(doc.total_leave_days, 6)
			old_hours = flt(doc.total_leave_hours, 6)
			precision = frappe.get_precision("Leave Application", "total_leave_days") or 2
			doc.set_total_leave_metrics(precision)
			new_days = flt(doc.total_leave_days, 6)
			new_hours = flt(doc.total_leave_hours, 6)

			if abs(old_days - new_days) <= 0.000001 and abs(old_hours - new_hours) <= 0.000001:
				continue

			result = {
				"name": doc.name,
				"employee": doc.employee,
				"from_date": str(doc.from_date),
				"to_date": str(doc.to_date),
				"old_days": old_days,
				"new_days": new_days,
				"old_hours": old_hours,
				"new_hours": new_hours,
			}
			results.append(result)

			if dry_run:
				continue

			frappe.db.sql(
				"""
				DELETE FROM `tabLeave Ledger Entry`
				WHERE transaction_type = 'Leave Application'
				  AND transaction_name = %s
				""",
				(doc.name,),
			)
			frappe.db.set_value(
				"Leave Application",
				doc.name,
				{
					"total_leave_days": new_days,
					"total_leave_hours": new_hours,
				},
				update_modified=False,
			)
			doc.total_leave_days = new_days
			doc.total_leave_hours = new_hours
			doc.create_leave_ledger_entry(submit=True)

		if not dry_run:
			frappe.db.commit()
	finally:
		frappe.flags.in_patch = previous_in_patch

	return results
