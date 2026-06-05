from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
	create_custom_fields(
		{"Designation": get_designation_custom_fields()},
		ignore_validate=True,
		update=True,
	)
	update_standard_designation_field_labels()


def update_standard_designation_field_labels():
	field_labels = {
		"designation_name": "عنوان شغل",
		"description": "شرح کلی شغل",
		"color": "رنگ",
	}

	for fieldname, label in field_labels.items():
		make_property_setter(
			"Designation",
			fieldname,
			"label",
			label,
			"Data",
			validate_fields_for_doctype=False,
		)


def get_designation_custom_fields():
	return [
		{
			"fieldname": "appraisal_template",
			"fieldtype": "Link",
			"label": "الگوی ارزیابی",
			"options": "Appraisal Template",
			"insert_after": "description",
			"allow_in_quick_entry": 1,
		},
		{
			"fieldname": "required_skills_section",
			"fieldtype": "Section Break",
			"label": "مهارت‌های موردنیاز",
			"insert_after": "appraisal_template",
		},
		{
			"fieldname": "skills",
			"fieldtype": "Table",
			"label": "مهارت‌های تخصصی",
			"options": "Designation Skill",
			"insert_after": "required_skills_section",
		},
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
		{
			"fieldname": "job_architecture_section",
			"fieldtype": "Section Break",
			"label": "گریدینگ و خانواده مشاغل",
			"insert_after": "other_assigned_duties_text",
		},
		{
			"fieldname": "job_family",
			"fieldtype": "Link",
			"label": "خانواده شغلی",
			"options": "Job Family",
			"insert_after": "job_architecture_section",
		},
		{
			"fieldname": "job_grade",
			"fieldtype": "Link",
			"label": "گرید شغلی",
			"options": "Job Grade",
			"insert_after": "job_family",
		},
		{
			"fieldname": "job_architecture_column_break",
			"fieldtype": "Column Break",
			"insert_after": "job_grade",
		},
		{
			"fieldname": "grading_model",
			"fieldtype": "Select",
			"label": "مدل ارزیابی شغل",
			"options": "\nمرسر\nهی گروپ\nسفارشی",
			"insert_after": "job_architecture_column_break",
		},
		{
			"fieldname": "career_track",
			"fieldtype": "Select",
			"label": "مسیر شغلی",
			"options": "\nتخصصی\nمدیریتی\nعملیاتی\nعمومی",
			"insert_after": "grading_model",
		},
		{
			"fieldname": "grading_scores_section",
			"fieldtype": "Section Break",
			"label": "امتیازدهی شغل",
			"insert_after": "career_track",
		},
		{
			"fieldname": "know_how_score",
			"fieldtype": "Float",
			"label": "امتیاز دانش و مهارت",
			"insert_after": "grading_scores_section",
		},
		{
			"fieldname": "problem_solving_score",
			"fieldtype": "Float",
			"label": "امتیاز حل مسئله",
			"insert_after": "know_how_score",
		},
		{
			"fieldname": "accountability_score",
			"fieldtype": "Float",
			"label": "امتیاز پاسخگویی",
			"insert_after": "problem_solving_score",
		},
		{
			"fieldname": "job_score",
			"fieldtype": "Float",
			"label": "امتیاز کل شغل",
			"read_only": 1,
			"insert_after": "accountability_score",
		},
		{
			"fieldname": "pay_band_section",
			"fieldtype": "Section Break",
			"label": "بازه حقوقی",
			"insert_after": "job_score",
		},
		{
			"fieldname": "grade_currency",
			"fieldtype": "Link",
			"label": "ارز",
			"options": "Currency",
			"fetch_from": "job_grade.currency",
			"read_only": 1,
			"insert_after": "pay_band_section",
		},
		{
			"fieldname": "pay_band_min",
			"fieldtype": "Currency",
			"label": "حداقل حقوق گرید",
			"options": "grade_currency",
			"fetch_from": "job_grade.min_salary",
			"read_only": 1,
			"insert_after": "grade_currency",
		},
		{
			"fieldname": "pay_band_max",
			"fieldtype": "Currency",
			"label": "حداکثر حقوق گرید",
			"options": "grade_currency",
			"fetch_from": "job_grade.max_salary",
			"read_only": 1,
			"insert_after": "pay_band_min",
		},
		{
			"fieldname": "pay_band_spread_percent",
			"fieldtype": "Percent",
			"label": "اسپرد حقوقی (%)",
			"fetch_from": "job_grade.spread_percent",
			"read_only": 1,
			"insert_after": "pay_band_max",
		},
	]
