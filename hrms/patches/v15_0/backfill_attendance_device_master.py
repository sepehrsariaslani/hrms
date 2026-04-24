import frappe

from hrms.utils.attendance_device_mapping import (
	append_employee_device_mapping,
	ensure_attendance_device,
	ensure_employee_device_mapping_setup,
	normalize_code,
	normalize_text,
)


def execute():
	frappe.reload_doc("hr", "doctype", "attendance_device")
	frappe.reload_doc("hr", "doctype", "employee_attendance_device_mapping")
	ensure_employee_device_mapping_setup(hide_legacy_field=True)
	backfill_employee_device_mappings()
	backfill_attendance_device_master()


def split_codes(raw_value):
	return [normalize_code(value) for value in str(raw_value or "").split("|") if normalize_code(value)]


def backfill_employee_device_mappings():
	employee_meta = frappe.get_meta("Employee")
	if not employee_meta.has_field("custom_attendance_device_mappings"):
		return

	fields = [
		"name",
		"company",
		"attendance_device_id",
	]
	for fieldname in ("custom_employee_codes", "custom_machine_nos", "custom_branch_codes"):
		if employee_meta.has_field(fieldname) and frappe.db.has_column("Employee", fieldname):
			fields.append(fieldname)
	employees = frappe.get_all("Employee", fields=fields, limit_page_length=0)
	for row in employees:
		employee_doc = frappe.get_doc("Employee", row["name"])
		changed = False

		if append_employee_device_mapping(
			employee_doc,
			row.get("attendance_device_id"),
			device_id=row.get("custom_machine_nos"),
			company=row.get("company"),
		):
			changed = True

		codes = split_codes(row.get("custom_employee_codes"))
		machines = split_codes(row.get("custom_machine_nos"))
		branches = split_codes(row.get("custom_branch_codes"))
		for index, code in enumerate(codes):
			machine = machines[index] if index < len(machines) else ""
			branch = branches[index] if index < len(branches) else ""
			if append_employee_device_mapping(
				employee_doc,
				code,
				device_id=machine or branch,
				company=row.get("company"),
				location=branch,
			):
				changed = True

		if not changed:
			continue

		employee_doc.flags.ignore_permissions = True
		employee_doc.flags.ignore_mandatory = True
		employee_doc.save(ignore_permissions=True)


def backfill_attendance_device_master():
	rows = frappe.get_all(
		"Employee Attendance Device Mapping",
		fields=["name", "parent", "device_id", "device_company", "device_location"],
		filters={"parenttype": "Employee"},
		limit_page_length=0,
	)
	if not rows:
		return

	employee_company = {
		row.name: row.company
		for row in frappe.get_all("Employee", fields=["name", "company"], limit_page_length=0)
	}
	for row in rows:
		device_id = normalize_code(row.get("device_id"))
		if not device_id:
			continue
		location = normalize_text(row.get("device_location"))
		company = employee_company.get(row.get("parent"))
		device_name = ensure_attendance_device(device_id, company=company, location=location)
		device_company, device_location = frappe.db.get_value(
			"Attendance Device",
			device_name,
			["company", "location"],
		)
		updates = {}
		if device_name != row.get("device_id"):
			updates["device_id"] = device_name
		if device_company and device_company != row.get("device_company"):
			updates["device_company"] = device_company
		if device_location and device_location != row.get("device_location"):
			updates["device_location"] = device_location
		if updates:
			frappe.db.set_value(
				"Employee Attendance Device Mapping",
				row.get("name"),
				updates,
				update_modified=False,
			)
