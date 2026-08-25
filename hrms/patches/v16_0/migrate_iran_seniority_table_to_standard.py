import frappe
from frappe.utils import getdate


def execute():
	if not frappe.db.exists("DocType", "Iran Seniority Table"):
		return

	target_doc = get_or_create_target_doc()
	if not target_doc:
		return

	migrate_single_child_rows(target_doc.name)


def get_or_create_target_doc():
	existing = frappe.db.get_value("Iran Seniority Table", {"enabled": 1}, "name")
	if existing:
		return frappe.get_doc("Iran Seniority Table", existing)

	fiscal_year = get_fiscal_year_by_date()
	if not fiscal_year:
		return None

	doc = frappe.get_doc(
		{
			"doctype": "Iran Seniority Table",
			"fiscal_year": fiscal_year,
			"enabled": cint_single_value("Iran Seniority Table", "enabled", default=1),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def migrate_single_child_rows(target_parent_name: str):
	legacy_parent_name = "Iran Seniority Table"

	rows = frappe.get_all(
		"Iran Seniority Rule",
		filters={
			"parenttype": "Iran Seniority Table",
			"parentfield": "rules",
			"parent": legacy_parent_name,
		},
		fields=["name"],
		order_by="idx asc",
	)

	for row in rows:
		frappe.db.set_value(
			"Iran Seniority Rule",
			row.name,
			{
				"parent": target_parent_name,
				"parenttype": "Iran Seniority Table",
				"parentfield": "rules",
			},
			update_modified=False,
		)


def get_fiscal_year_by_date(reference_date=None):
	reference_date = getdate(reference_date) if reference_date else getdate()
	fiscal_year = frappe.db.get_value(
		"Fiscal Year",
		{
			"year_start_date": ["<=", reference_date],
			"year_end_date": [">=", reference_date],
		},
		"name",
	)
	return fiscal_year or frappe.db.get_value("Fiscal Year", {}, "name")


def cint_single_value(doctype: str, field: str, default=0) -> int:
	value = frappe.db.sql(
		"""
		SELECT value
		FROM tabSingles
		WHERE doctype=%s AND field=%s
		LIMIT 1
		""",
		(doctype, field),
	)
	value = value[0][0] if value else None
	try:
		return int(value)
	except Exception:
		return int(default)
