import frappe


def execute():
	# Create the Iran Salary Slip custom fields (including the monthly seniority
	# base field) for existing sites, not just fresh installs.
	try:
		from hrms.regional.iran.setup import make_custom_fields

		make_custom_fields()
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Unable to create Iran salary slip custom fields",
		)
