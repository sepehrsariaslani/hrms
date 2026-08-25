import frappe


def execute():
	# Ensure the standard_working_hours column exists on Shift Type for existing
	# sites (the field was added to the doctype JSON, but the column may not have
	# been created if the site hasn't migrated yet).
	try:
		if not frappe.db.has_column("Shift Type", "standard_working_hours"):
			frappe.db.sql_ddl(
				"ALTER TABLE `tabShift Type` ADD COLUMN `standard_working_hours` DECIMAL(21,6) NULL"
			)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Unable to add standard_working_hours column to Shift Type",
		)
