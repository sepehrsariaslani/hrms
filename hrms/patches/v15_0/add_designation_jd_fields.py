from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{"Designation": get_designation_jd_fields()},
		ignore_validate=True,
		update=True,
	)


def get_designation_jd_fields():
	return [
		{
			"fieldname": "jd_section",
			"fieldtype": "Section Break",
			"label": "اطلاعات پایه و جایگاه سازمانی",
			"insert_after": "skills",
		},
		{
			"fieldname": "jd_department",
			"fieldtype": "Link",
			"label": "دپارتمان / واحد",
			"options": "Department",
			"insert_after": "jd_section",
		},
		{
			"fieldname": "reports_to_designation",
			"fieldtype": "Link",
			"label": "گزارش می‌دهد به (سمت)",
			"options": "Designation",
			"insert_after": "jd_department",
		},
		{
			"fieldname": "reports_to_column_break",
			"fieldtype": "Column Break",
			"insert_after": "reports_to_designation",
		},
		{
			"fieldname": "work_location",
			"fieldtype": "Data",
			"label": "محل خدمت",
			"insert_after": "reports_to_column_break",
		},
		{
			"fieldname": "direct_reports",
			"fieldtype": "Table",
			"label": "گزارش می‌گیرد از",
			"options": "Designation Direct Report",
			"insert_after": "work_location",
		},
		{
			"fieldname": "job_purpose_section",
			"fieldtype": "Section Break",
			"label": "هدف اصلی شغل",
			"insert_after": "direct_reports",
		},
		{
			"fieldname": "job_purpose",
			"fieldtype": "Small Text",
			"label": "هدف اصلی شغل",
			"insert_after": "job_purpose_section",
		},
		{
			"fieldname": "key_responsibilities_section",
			"fieldtype": "Section Break",
			"label": "شرح وظایف و مسئولیت‌های اصلی",
			"insert_after": "job_purpose",
		},
		{
			"fieldname": "key_responsibilities",
			"fieldtype": "Table",
			"label": "وظایف کلیدی",
			"options": "Designation Responsibility",
			"insert_after": "key_responsibilities_section",
		},
		{
			"fieldname": "qualifications_section",
			"fieldtype": "Section Break",
			"label": "شرایط احراز شغل",
			"insert_after": "key_responsibilities",
		},
		{
			"fieldname": "min_education",
			"fieldtype": "Data",
			"label": "حداقل تحصیلات",
			"insert_after": "qualifications_section",
		},
		{
			"fieldname": "min_experience_years",
			"fieldtype": "Float",
			"label": "حداقل سابقه (سال)",
			"insert_after": "min_education",
		},
		{
			"fieldname": "qualifications_column_break",
			"fieldtype": "Column Break",
			"insert_after": "min_experience_years",
		},
		{
			"fieldname": "required_soft_skills",
			"fieldtype": "Table",
			"label": "مهارت‌های نرم",
			"options": "Designation Soft Skill",
			"insert_after": "qualifications_column_break",
		},
		{
			"fieldname": "kpi_section",
			"fieldtype": "Section Break",
			"label": "شاخص‌های کلیدی عملکرد",
			"insert_after": "required_soft_skills",
		},
		{
			"fieldname": "kpis",
			"fieldtype": "Table",
			"label": "شاخص‌های عملکرد",
			"options": "Designation KPI",
			"insert_after": "kpi_section",
		},
		{
			"fieldname": "working_conditions_section",
			"fieldtype": "Section Break",
			"label": "شرایط فیزیکی و محیط کار",
			"insert_after": "kpis",
		},
		{
			"fieldname": "working_conditions",
			"fieldtype": "Table",
			"label": "شرایط محیط کار",
			"options": "Designation Working Condition",
			"insert_after": "working_conditions_section",
		},
		{
			"default": "1",
			"fieldname": "other_assigned_duties_clause",
			"fieldtype": "Check",
			"label": "فعال‌سازی بند سایر امور محوله",
			"insert_after": "working_conditions",
		},
		{
			"default": "انجام سایر امور محوله از سوی مدیر مستقیم در چارچوب اهداف سازمانی.",
			"fieldname": "other_assigned_duties_text",
			"fieldtype": "Small Text",
			"label": "متن بند سایر امور محوله",
			"insert_after": "other_assigned_duties_clause",
		},
	]
