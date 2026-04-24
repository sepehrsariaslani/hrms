from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Designation": get_designation_competency_fields(),
			"HR Settings": get_hr_settings_competency_fields(),
		},
		ignore_validate=True,
		update=True,
	)


def get_designation_competency_fields():
	return [
		{
			"fieldname": "competency_model_section",
			"fieldtype": "Section Break",
			"label": "مدل شایستگی",
			"insert_after": "pay_band_spread_percent",
		},
		{
			"fieldname": "required_competencies",
			"fieldtype": "Table",
			"label": "شایستگی‌های موردنیاز شغل",
			"options": "Competency Requirement",
			"insert_after": "competency_model_section",
		},
	]


def get_hr_settings_competency_fields():
	return [
		{
			"fieldname": "competency_model_settings_section",
			"fieldtype": "Section Break",
			"label": "مدل شایستگی سازمانی",
			"insert_after": "attendance_settings_section",
		},
		{
			"fieldname": "core_competencies",
			"fieldtype": "Table",
			"label": "شایستگی‌های عمومی سازمان",
			"options": "Competency Requirement",
			"insert_after": "competency_model_settings_section",
		},
	]

