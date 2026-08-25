import frappe
from frappe.utils import cint


def sync_employee_designations(doc, method=None):
	if not hasattr(doc, "employee_designations"):
		return

	rows = [row for row in (doc.employee_designations or []) if row.designation]
	row_designations = {row.designation for row in rows}

	# Keep legacy designation field in sync for compatibility with existing code paths.
	if doc.designation and doc.designation not in row_designations:
		doc.append("employee_designations", {"designation": doc.designation, "is_primary": 1})
		rows = [row for row in (doc.employee_designations or []) if row.designation]

	if not rows:
		return

	primary_row = None
	for row in rows:
		if cint(row.is_primary):
			primary_row = row
			break

	if not primary_row:
		primary_row = rows[0]
		primary_row.is_primary = 1

	for row in rows:
		if row.name != primary_row.name:
			row.is_primary = 0

	doc.designation = primary_row.designation
