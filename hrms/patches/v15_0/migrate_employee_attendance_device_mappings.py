import frappe

from hrms.utils.attendance_device_mapping import (
	DEVICE_MAPPING_TABLE_FIELD,
	append_employee_device_mapping,
	ensure_employee_device_mapping_setup,
	normalize_code,
)


def execute():
	frappe.reload_doc("hr", "doctype", "attendance_device")
	frappe.reload_doc("hr", "doctype", "employee_attendance_device_mapping")
	ensure_employee_device_mapping_setup(hide_legacy_field=True)
	migrate_legacy_employee_device_codes()


def split_codes(raw_value):
	return [normalize_code(value) for value in str(raw_value or "").split("|") if normalize_code(value)]


def migrate_legacy_employee_device_codes():
	employee_meta = frappe.get_meta("Employee")
	if not employee_meta.has_field(DEVICE_MAPPING_TABLE_FIELD):
		return

	fields = [
		"name",
		"attendance_device_id",
	]
	for fieldname in ("custom_employee_codes", "custom_machine_nos", "custom_branch_codes"):
		if employee_meta.has_field(fieldname) and frappe.db.has_column("Employee", fieldname):
			fields.append(fieldname)
	employees = frappe.get_all("Employee", fields=fields, limit_page_length=0)
	updated = 0

	for row in employees:
		employee_doc = frappe.get_doc("Employee", row["name"])
		changed = False

		if append_employee_device_mapping(
			employee_doc,
			row.get("attendance_device_id"),
			device_id=row.get("custom_machine_nos"),
		):
			changed = True

		codes = split_codes(row.get("custom_employee_codes"))
		machines = split_codes(row.get("custom_machine_nos"))
		branches = split_codes(row.get("custom_branch_codes"))

		for index, code in enumerate(codes):
			machine = machines[index] if index < len(machines) else ""
			branch = branches[index] if index < len(branches) else ""

			# Store a device hint for disambiguation when code values are shared across devices.
			device_hint = machine or branch
			if append_employee_device_mapping(
				employee_doc,
				code,
				device_id=device_hint,
				location=branch,
			):
				changed = True

		if not changed:
			continue

		employee_doc.flags.ignore_permissions = True
		employee_doc.flags.ignore_mandatory = True
		employee_doc.save(ignore_permissions=True)
		updated += 1

	if updated:
		frappe.db.commit()
