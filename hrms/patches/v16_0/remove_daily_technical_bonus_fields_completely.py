import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


LEGACY_DAILY_TECHNICAL_FIELDS = ("technical_bonus_daily", "technical_bonus")


def execute():
	if not frappe.db.exists("DocType", "Employee"):
		return

	remove_legacy_technical_custom_fields()
	remove_legacy_technical_property_setters()
	drop_legacy_technical_columns_if_present()
	ensure_monthly_technical_fields_editable()
	frappe.clear_cache(doctype="Employee")


def remove_legacy_technical_custom_fields():
	for fieldname in LEGACY_DAILY_TECHNICAL_FIELDS:
		custom_field_name = frappe.db.get_value("Custom Field", {"dt": "Employee", "fieldname": fieldname}, "name")
		if custom_field_name:
			frappe.delete_doc("Custom Field", custom_field_name, force=1, ignore_permissions=True)


def remove_legacy_technical_property_setters():
	frappe.db.delete(
		"Property Setter",
		{
			"doc_type": "Employee",
			"field_name": ["in", LEGACY_DAILY_TECHNICAL_FIELDS],
		},
	)


def drop_legacy_technical_columns_if_present():
	for fieldname in LEGACY_DAILY_TECHNICAL_FIELDS:
		if frappe.db.has_column("Employee", fieldname):
			frappe.db.sql_ddl(f"ALTER TABLE `tabEmployee` DROP COLUMN `{fieldname}`")


def ensure_monthly_technical_fields_editable():
	for fieldname in ("karane", "technical_allowance_monthly"):
		if not frappe.get_meta("Employee").get_field(fieldname):
			continue
		make_property_setter(
			"Employee",
			fieldname,
			"read_only",
			0,
			"Check",
			validate_fields_for_doctype=False,
		)
		make_property_setter(
			"Employee",
			fieldname,
			"hidden",
			0,
			"Check",
			validate_fields_for_doctype=False,
		)
