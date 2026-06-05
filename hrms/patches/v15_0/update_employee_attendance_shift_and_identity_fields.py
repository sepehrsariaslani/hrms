import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.regional.iran.setup import make_custom_fields as make_iran_custom_fields
from hrms.setup import get_custom_fields


def execute():
	create_custom_fields({"Employee": get_custom_fields().get("Employee", [])}, update=True)
	make_iran_custom_fields(update=True)
	reorder_children_count()
	update_attendance_mapping_field_label()
	update_employee_table_labels()


def reorder_children_count():
	if not frappe.db.exists("DocType", "Employee"):
		return
	if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": "children_count"}):
		return

	frappe.db.set_value(
		"Custom Field",
		{"dt": "Employee", "fieldname": "children_count"},
		"insert_after",
		"marital_status",
		update_modified=False,
	)


def update_employee_table_labels():
	if frappe.db.exists("DocType", "Employee Attendance Device Mapping"):
		mapping_doc = frappe.get_doc("DocType", "Employee Attendance Device Mapping")
		updated = False
		for field in mapping_doc.fields:
			if field.fieldname == "device_id" and field.label != "شناسه دستگاه":
				field.label = "شناسه دستگاه"
				updated = True
			elif field.fieldname == "device_company" and field.label != "شرکت":
				field.label = "شرکت"
				updated = True
			elif field.fieldname == "device_location" and field.label != "موقعیت":
				field.label = "موقعیت"
				updated = True
			elif field.fieldname == "attendance_device_id" and field.label != "کد دستگاه حضور و غیاب":
				field.label = "کد دستگاه حضور و غیاب"
				updated = True

		if updated:
			mapping_doc.save(ignore_permissions=True)

	if frappe.db.exists("DocType", "Employee Shift Duty Role"):
		shift_role_doc = frappe.get_doc("DocType", "Employee Shift Duty Role")
		updated = False
		for field in shift_role_doc.fields:
			if field.fieldname == "shift_duty_role" and field.label != "نقش شیفت":
				field.label = "نقش شیفت"
				updated = True
			elif field.fieldname == "proficiency_level" and field.label != "سطح مهارت":
				field.label = "سطح مهارت"
				updated = True

		if updated:
			shift_role_doc.save(ignore_permissions=True)


def update_attendance_mapping_field_label():
	if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": "custom_attendance_device_mappings"}):
		return

	frappe.db.set_value(
		"Custom Field",
		{"dt": "Employee", "fieldname": "custom_attendance_device_mappings"},
		{
			"label": "نگاشت‌های دستگاه حضور غیاب",
			"insert_after": "attendance_device_info_section",
		},
		update_modified=False,
	)
