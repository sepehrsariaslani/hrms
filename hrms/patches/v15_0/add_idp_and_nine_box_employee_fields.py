from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{"Employee": get_employee_fields()},
		ignore_validate=True,
		update=True,
	)


def get_employee_fields():
	return [
		{
			"fieldname": "development_planning_section",
			"fieldtype": "Section Break",
			"label": "برنامه توسعه فردی",
			"insert_after": "job_applicant",
		},
		{
			"fieldname": "active_idp",
			"fieldtype": "Link",
			"label": "برنامه توسعه فردی فعال",
			"options": "Individual Development Plan",
			"insert_after": "development_planning_section",
		},
		{
			"fieldname": "latest_nine_box_assessment",
			"fieldtype": "Link",
			"label": "آخرین ارزیابی ۹ خانه",
			"options": "Nine Box Assessment",
			"insert_after": "active_idp",
		},
		{
			"fieldname": "target_career_transition",
			"fieldtype": "Link",
			"label": "مسیر شغلی هدف",
			"options": "Career Path Transition",
			"insert_after": "latest_nine_box_assessment",
		},
	]
