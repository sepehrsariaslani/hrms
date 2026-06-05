import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from hrms.regional.iran.utils import recalculate_iran_employee_seniority_fields


LEGACY_TECHNICAL_FIELDS = ("technical_bonus_daily", "technical_bonus")


def execute():
	if not frappe.db.exists("DocType", "Employee"):
		return

	backfill_monthly_technical_bonus_from_daily_if_missing()
	remove_legacy_hourly_and_daily_technical_fields()
	make_monthly_technical_fields_editable()
	recalculate_iran_employee_seniority_fields()
	frappe.clear_cache(doctype="Employee")


def backfill_monthly_technical_bonus_from_daily_if_missing():
	if not frappe.db.has_column("Employee", "monthly_technical_bonus"):
		return
	if not frappe.db.has_column("Employee", "technical_bonus_daily"):
		return

	frappe.db.sql(
		"""
		UPDATE `tabEmployee`
		SET monthly_technical_bonus = technical_bonus_daily * 30
		WHERE COALESCE(monthly_technical_bonus, 0) = 0
		  AND COALESCE(technical_bonus_daily, 0) > 0
		"""
	)


def remove_legacy_hourly_and_daily_technical_fields():
	for fieldname in LEGACY_TECHNICAL_FIELDS:
		delete_custom_field_if_exists("Employee", fieldname)

	frappe.db.delete(
		"Property Setter",
		{
			"doc_type": "Employee",
			"field_name": ["in", LEGACY_TECHNICAL_FIELDS],
		},
	)


def make_monthly_technical_fields_editable():
	for fieldname in ("monthly_technical_bonus", "technical_allowance_monthly"):
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


def delete_custom_field_if_exists(doctype: str, fieldname: str):
	custom_field_name = frappe.db.get_value("Custom Field", {"dt": doctype, "fieldname": fieldname}, "name")
	if not custom_field_name:
		return

	frappe.delete_doc("Custom Field", custom_field_name, force=1, ignore_permissions=True)
