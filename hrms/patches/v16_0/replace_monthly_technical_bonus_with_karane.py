import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
	if not frappe.db.exists("DocType", "Employee"):
		return

	ensure_karane_custom_field()
	ensure_technical_allowance_monthly_position()
	backfill_karane_from_monthly_technical_bonus()
	drop_monthly_technical_bonus_column_if_exists()
	delete_monthly_technical_bonus_custom_field_if_exists()
	remove_monthly_technical_bonus_property_setters()
	ensure_karane_editable_visible()
	frappe.clear_cache(doctype="Employee")


def ensure_karane_custom_field():
	if frappe.db.get_value("Custom Field", {"dt": "Employee", "fieldname": "karane"}, "name"):
		return

	frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": "Employee",
			"fieldname": "karane",
			"label": "کارانه",
			"fieldtype": "Currency",
			"default": "0",
			"insert_after": "base_pay",
		}
	).insert(ignore_permissions=True)


def ensure_technical_allowance_monthly_position():
	custom_field_name = frappe.db.get_value(
		"Custom Field", {"dt": "Employee", "fieldname": "technical_allowance_monthly"}, "name"
	)
	if not custom_field_name:
		return

	frappe.db.set_value("Custom Field", custom_field_name, "insert_after", "karane", update_modified=False)


def backfill_karane_from_monthly_technical_bonus():
	if not frappe.db.has_column("Employee", "karane"):
		return

	if frappe.db.has_column("Employee", "monthly_technical_bonus"):
		frappe.db.sql(
			"""
			UPDATE `tabEmployee`
			SET karane = COALESCE(monthly_technical_bonus, 0)
			WHERE COALESCE(karane, 0) = 0
			"""
		)


def drop_monthly_technical_bonus_column_if_exists():
	if frappe.db.has_column("Employee", "monthly_technical_bonus"):
		frappe.db.sql_ddl("ALTER TABLE `tabEmployee` DROP COLUMN `monthly_technical_bonus`")


def delete_monthly_technical_bonus_custom_field_if_exists():
	custom_field_name = frappe.db.get_value(
		"Custom Field", {"dt": "Employee", "fieldname": "monthly_technical_bonus"}, "name"
	)
	if custom_field_name:
		frappe.delete_doc("Custom Field", custom_field_name, force=1, ignore_permissions=True)


def remove_monthly_technical_bonus_property_setters():
	frappe.db.delete(
		"Property Setter",
		{
			"doc_type": "Employee",
			"field_name": "monthly_technical_bonus",
		},
	)


def ensure_karane_editable_visible():
	if not frappe.get_meta("Employee").get_field("karane"):
		return

	make_property_setter(
		"Employee",
		"karane",
		"read_only",
		0,
		"Check",
		validate_fields_for_doctype=False,
	)
	make_property_setter(
		"Employee",
		"karane",
		"hidden",
		0,
		"Check",
		validate_fields_for_doctype=False,
	)
