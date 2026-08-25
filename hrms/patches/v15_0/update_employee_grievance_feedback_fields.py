import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.api import ensure_iran_grievance_types


def execute():
	ensure_iran_grievance_types()
	create_custom_fields(
		{
			"Employee Grievance": [
				{
					"fieldname": "feedback_type",
					"fieldtype": "Select",
					"label": "Feedback Type",
					"options": "شکایت\nپیشنهاد\nانتقاد\nایده",
					"default": "انتقاد",
					"reqd": 1,
					"insert_after": "subject",
				}
			]
		},
		ignore_validate=True,
		update=True,
	)

	if frappe.db.has_column("Employee Grievance", "feedback_type"):
		frappe.db.sql(
			"""
			update `tabEmployee Grievance`
			set feedback_type = 'انتقاد'
			where ifnull(feedback_type, '') = ''
			"""
		)
