import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


FIELDS_TO_REMOVE = (
	"custom_source_person_id",
	"custom_membership_date_jalali",
	"custom_membership_date_gregorian",
	"custom_latest_attendance_date_jalali",
	"custom_latest_attendance_date_gregorian",
	"custom_attendance_source_databases",
	"custom_branch_codes",
	"custom_machine_nos",
	"custom_employee_codes",
	"custom_device_map_detail",
	"custom_total_attendance_records",
	"custom_total_clock_punches",
	"default_shift",
)


def _delete_custom_field(fieldname):
	field_id = frappe.db.get_value("Custom Field", {"dt": "Employee", "fieldname": fieldname}, "name")
	if not field_id:
		return
	frappe.delete_doc("Custom Field", field_id, force=1, ignore_permissions=True)


def execute():
	if not frappe.db.exists("DocType", "Employee"):
		return

	for fieldname in FIELDS_TO_REMOVE:
		_delete_custom_field(fieldname)

	create_custom_fields(
		{
			"Employee": [
				{
					"fieldname": "birth_certificate_column_break",
					"fieldtype": "Column Break",
					"insert_after": "birth_certificate_number",
				},
				{
					"fieldname": "birth_certificate_serial",
					"fieldtype": "Data",
					"label": "سری شناسنامه",
					"insert_after": "birth_certificate_column_break",
				},
			]
		},
		update=True,
	)

	if frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": "personnel_case_no"}):
		frappe.db.set_value(
			"Custom Field",
			{"dt": "Employee", "fieldname": "personnel_case_no"},
			"insert_after",
			"salutation",
			update_modified=False,
		)

	make_property_setter(
		"Employee",
		"family_background",
		"insert_after",
		"marital_status",
		"Data",
		validate_fields_for_doctype=False,
	)
	make_property_setter(
		"Employee",
		"column_break6",
		"insert_after",
		"family_background",
		"Data",
		validate_fields_for_doctype=False,
	)
	make_property_setter(
		"Employee",
		"blood_group",
		"insert_after",
		"column_break6",
		"Data",
		validate_fields_for_doctype=False,
	)
	make_property_setter(
		"Employee",
		"health_details",
		"insert_after",
		"blood_group",
		"Data",
		validate_fields_for_doctype=False,
	)

	frappe.clear_cache(doctype="Employee")
