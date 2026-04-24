import frappe

from hrms.utils.attendance_device_mapping import ensure_attendance_device, normalize_device_identifier


def execute():
	normalize_device_ids_in_employee_mappings()
	cleanup_orphaned_compound_device_ids()


def normalize_device_ids_in_employee_mappings():
	rows = frappe.get_all(
		"Employee Attendance Device Mapping",
		fields=["name", "device_id", "parent"],
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
		normalized_device_id = normalize_device_identifier(row.get("device_id"))
		if normalized_device_id == (row.get("device_id") or ""):
			continue

		device_doc = ensure_attendance_device(
			normalized_device_id,
			company=employee_company.get(row.get("parent")),
		)
		frappe.db.set_value(
			"Employee Attendance Device Mapping",
			row.get("name"),
			"device_id",
			device_doc,
			update_modified=False,
		)

	frappe.db.commit()


def cleanup_orphaned_compound_device_ids():
	if not frappe.db.exists("DocType", "Attendance Device"):
		return

	device_rows = frappe.get_all(
		"Attendance Device",
		fields=["name"],
		filters={"name": ("like", "%|%")},
		limit_page_length=0,
	)
	for row in device_rows:
		if frappe.db.exists("Employee Attendance Device Mapping", {"device_id": row.name}):
			continue
		frappe.delete_doc("Attendance Device", row.name, ignore_permissions=True, force=1)

