import os

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.desk.page.setup_wizard.install_fixtures import (
	_,  # NOTE: this is not the real translation function
)
from frappe.desk.page.setup_wizard.setup_wizard import make_records
from frappe.installer import update_site_config

from hrms.overrides.company import delete_company_fixtures


def after_install():
	create_custom_fields(get_custom_fields(), ignore_validate=True)
	create_salary_slip_loan_fields()
	make_fixtures()
	setup_notifications()
	update_hr_defaults()
	add_non_standard_user_types()
	set_single_defaults()
	ensure_global_print_style()
	create_default_role_profiles()
	run_post_install_patches()
	sync_hr_workspace_extensions()
	remove_home_workspace_sidebar()


def before_uninstall():
	delete_custom_fields(get_custom_fields())
	delete_custom_fields(get_salary_slip_loan_fields())
	delete_company_fixtures()


def after_app_install(app_name):
	"""Set up loan integration with payroll"""
	if app_name != "lending":
		return

	print("Updating payroll setup for loans")
	create_custom_fields(get_salary_slip_loan_fields(), ignore_validate=True)
	add_lending_docperms_to_ess()
	remove_home_workspace_sidebar()


def before_app_uninstall(app_name):
	"""Clean up loan integration with payroll"""
	if app_name != "lending":
		return

	print("Updating payroll setup for loans")
	delete_custom_fields(get_salary_slip_loan_fields())
	remove_lending_docperms_from_ess()


def remove_home_workspace_sidebar():
	if not frappe.db.table_exists("Workspace Sidebar"):
		return

	if frappe.db.exists("Workspace Sidebar", "Home"):
		frappe.delete_doc("Workspace Sidebar", "Home", force=True)
		frappe.clear_cache()


def get_custom_fields():
	"""HR specific custom fields that need to be added to the masters in ERPNext"""
	return {
		"Company": [
			{
				"fieldname": "hr_and_payroll_tab",
				"fieldtype": "Tab Break",
				"label": _("HR & Payroll"),
				"insert_after": "credit_limit",
			},
			{
				"fieldname": "hr_settings_section",
				"fieldtype": "Section Break",
				"label": _("HR & Payroll Settings"),
				"insert_after": "hr_and_payroll_tab",
			},
			{
				"depends_on": "eval:!doc.__islocal",
				"fieldname": "default_expense_claim_payable_account",
				"fieldtype": "Link",
				"ignore_user_permissions": 1,
				"label": _("Default Expense Claim Payable Account"),
				"no_copy": 1,
				"options": "Account",
				"insert_after": "hr_settings_section",
			},
			{
				"fieldname": "default_employee_advance_account",
				"fieldtype": "Link",
				"label": _("Default Employee Advance Account"),
				"no_copy": 1,
				"options": "Account",
				"insert_after": "default_expense_claim_payable_account",
			},
			{
				"fieldname": "column_break_10",
				"fieldtype": "Column Break",
				"insert_after": "default_employee_advance_account",
			},
			{
				"depends_on": "eval:!doc.__islocal",
				"fieldname": "default_payroll_payable_account",
				"fieldtype": "Link",
				"ignore_user_permissions": 1,
				"label": _("Default Payroll Payable Account"),
				"no_copy": 1,
				"options": "Account",
				"insert_after": "column_break_10",
			},
		],
		"Department": [
			{
				"fieldname": "section_break_4",
				"fieldtype": "Section Break",
				"insert_after": "disabled",
			},
			{
				"fieldname": "payroll_cost_center",
				"fieldtype": "Link",
				"label": _("Payroll Cost Center"),
				"options": "Cost Center",
				"insert_after": "section_break_4",
			},
			{
				"fieldname": "column_break_9",
				"fieldtype": "Column Break",
				"insert_after": "payroll_cost_center",
			},
			{
				"description": _("Days for which Holidays are blocked for this department."),
				"fieldname": "leave_block_list",
				"fieldtype": "Link",
				"in_list_view": 1,
				"label": _("Leave Block List"),
				"options": "Leave Block List",
				"insert_after": "column_break_9",
			},
			{
				"description": _("The first Approver in the list will be set as the default Approver."),
				"fieldname": "approvers",
				"fieldtype": "Section Break",
				"label": _("Approvers"),
				"insert_after": "leave_block_list",
			},
			{
				"fieldname": "shift_request_approver",
				"fieldtype": "Table",
				"label": _("Shift Request Approver"),
				"options": "Department Approver",
				"insert_after": "approvers",
			},
			{
				"fieldname": "leave_approvers",
				"fieldtype": "Table",
				"label": _("Leave Approver"),
				"options": "Department Approver",
				"insert_after": "shift_request_approver",
			},
			{
				"fieldname": "expense_approvers",
				"fieldtype": "Table",
				"label": _("Expense Approver"),
				"options": "Department Approver",
				"insert_after": "leave_approvers",
			},
		],
		"Designation": [
			{
				"fieldname": "appraisal_template",
				"fieldtype": "Link",
				"label": _("الگوی ارزیابی"),
				"options": "Appraisal Template",
				"insert_after": "description",
				"allow_in_quick_entry": 1,
			},
			{
				"fieldname": "required_skills_section",
				"fieldtype": "Section Break",
				"label": _("مهارت‌های موردنیاز"),
				"insert_after": "appraisal_template",
			},
			{
				"fieldname": "skills",
				"fieldtype": "Table",
				"label": _("مهارت‌های تخصصی"),
				"options": "Designation Skill",
				"insert_after": "required_skills_section",
			},
			{
				"fieldname": "jd_section",
				"fieldtype": "Section Break",
				"label": _("اطلاعات پایه و جایگاه سازمانی"),
				"insert_after": "skills",
			},
			{
				"fieldname": "jd_department",
				"fieldtype": "Link",
				"label": _("دپارتمان / واحد"),
				"options": "Department",
				"insert_after": "jd_section",
			},
			{
				"fieldname": "reports_to_designation",
				"fieldtype": "Link",
				"label": _("گزارش می‌دهد به (سمت)"),
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
				"label": _("محل خدمت"),
				"insert_after": "reports_to_column_break",
			},
			{
				"fieldname": "direct_reports",
				"fieldtype": "Table",
				"label": _("گزارش می‌گیرد از"),
				"options": "Designation Direct Report",
				"insert_after": "work_location",
			},
			{
				"fieldname": "job_purpose_section",
				"fieldtype": "Section Break",
				"label": _("هدف اصلی شغل"),
				"insert_after": "direct_reports",
			},
			{
				"fieldname": "job_purpose",
				"fieldtype": "Small Text",
				"label": _("هدف اصلی شغل"),
				"insert_after": "job_purpose_section",
			},
			{
				"fieldname": "key_responsibilities_section",
				"fieldtype": "Section Break",
				"label": _("شرح وظایف و مسئولیت‌های اصلی"),
				"insert_after": "job_purpose",
			},
			{
				"fieldname": "key_responsibilities",
				"fieldtype": "Table",
				"label": _("وظایف کلیدی"),
				"options": "Designation Responsibility",
				"insert_after": "key_responsibilities_section",
			},
			{
				"fieldname": "qualifications_section",
				"fieldtype": "Section Break",
				"label": _("شرایط احراز شغل"),
				"insert_after": "key_responsibilities",
			},
			{
				"fieldname": "min_education",
				"fieldtype": "Data",
				"label": _("حداقل تحصیلات"),
				"insert_after": "qualifications_section",
			},
			{
				"fieldname": "min_experience_years",
				"fieldtype": "Float",
				"label": _("حداقل سابقه (سال)"),
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
				"label": _("مهارت‌های نرم"),
				"options": "Designation Soft Skill",
				"insert_after": "qualifications_column_break",
			},
			{
				"fieldname": "kpi_section",
				"fieldtype": "Section Break",
				"label": _("شاخص‌های کلیدی عملکرد"),
				"insert_after": "required_soft_skills",
			},
			{
				"fieldname": "kpis",
				"fieldtype": "Table",
				"label": _("شاخص‌های عملکرد"),
				"options": "Designation KPI",
				"insert_after": "kpi_section",
			},
			{
				"fieldname": "working_conditions_section",
				"fieldtype": "Section Break",
				"label": _("شرایط فیزیکی و محیط کار"),
				"insert_after": "kpis",
			},
			{
				"fieldname": "working_conditions",
				"fieldtype": "Table",
				"label": _("شرایط محیط کار"),
				"options": "Designation Working Condition",
				"insert_after": "working_conditions_section",
			},
			{
				"default": "1",
				"fieldname": "other_assigned_duties_clause",
				"fieldtype": "Check",
				"label": _("فعال‌سازی بند سایر امور محوله"),
				"insert_after": "working_conditions",
			},
			{
				"default": _(
					"انجام سایر امور محوله از سوی مدیر مستقیم در چارچوب اهداف سازمانی."
				),
				"fieldname": "other_assigned_duties_text",
				"fieldtype": "Small Text",
				"label": _("متن بند سایر امور محوله"),
				"insert_after": "other_assigned_duties_clause",
			},
			{
				"fieldname": "job_architecture_section",
				"fieldtype": "Section Break",
				"label": _("گریدینگ و خانواده مشاغل"),
				"insert_after": "other_assigned_duties_text",
			},
			{
				"fieldname": "job_family",
				"fieldtype": "Link",
				"label": _("خانواده شغلی"),
				"options": "Job Family",
				"insert_after": "job_architecture_section",
			},
			{
				"fieldname": "job_grade",
				"fieldtype": "Link",
				"label": _("گرید شغلی"),
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
				"label": _("مدل ارزیابی شغل"),
				"options": "\nمرسر\nهی گروپ\nسفارشی",
				"insert_after": "job_architecture_column_break",
			},
			{
				"fieldname": "career_track",
				"fieldtype": "Select",
				"label": _("مسیر شغلی"),
				"options": "\nتخصصی\nمدیریتی\nعملیاتی\nعمومی",
				"insert_after": "grading_model",
			},
			{
				"fieldname": "grading_scores_section",
				"fieldtype": "Section Break",
				"label": _("امتیازدهی شغل"),
				"insert_after": "career_track",
			},
			{
				"fieldname": "know_how_score",
				"fieldtype": "Float",
				"label": _("امتیاز دانش و مهارت"),
				"insert_after": "grading_scores_section",
			},
			{
				"fieldname": "problem_solving_score",
				"fieldtype": "Float",
				"label": _("امتیاز حل مسئله"),
				"insert_after": "know_how_score",
			},
			{
				"fieldname": "accountability_score",
				"fieldtype": "Float",
				"label": _("امتیاز پاسخگویی"),
				"insert_after": "problem_solving_score",
			},
			{
				"fieldname": "job_score",
				"fieldtype": "Float",
				"label": _("امتیاز کل شغل"),
				"read_only": 1,
				"insert_after": "accountability_score",
			},
			{
				"fieldname": "pay_band_section",
				"fieldtype": "Section Break",
				"label": _("بازه حقوقی"),
				"insert_after": "job_score",
			},
			{
				"fieldname": "grade_currency",
				"fieldtype": "Link",
				"label": _("ارز"),
				"options": "Currency",
				"fetch_from": "job_grade.currency",
				"read_only": 1,
				"insert_after": "pay_band_section",
			},
			{
				"fieldname": "pay_band_min",
				"fieldtype": "Currency",
				"label": _("حداقل حقوق گرید"),
				"options": "grade_currency",
				"fetch_from": "job_grade.min_salary",
				"read_only": 1,
				"insert_after": "grade_currency",
			},
			{
				"fieldname": "pay_band_max",
				"fieldtype": "Currency",
				"label": _("حداکثر حقوق گرید"),
				"options": "grade_currency",
				"fetch_from": "job_grade.max_salary",
				"read_only": 1,
				"insert_after": "pay_band_min",
			},
			{
				"fieldname": "pay_band_spread_percent",
				"fieldtype": "Percent",
				"label": _("اسپرد حقوقی (%)"),
				"fetch_from": "job_grade.spread_percent",
				"read_only": 1,
				"insert_after": "pay_band_max",
			},
			{
				"fieldname": "competency_model_section",
				"fieldtype": "Section Break",
				"label": _("مدل شایستگی"),
				"insert_after": "pay_band_spread_percent",
			},
			{
				"fieldname": "required_competencies",
				"fieldtype": "Table",
				"label": _("شایستگی‌های موردنیاز شغل"),
				"options": "Competency Requirement",
				"insert_after": "competency_model_section",
			},
		],
		"HR Settings": [
			{
				"fieldname": "competency_model_settings_section",
				"fieldtype": "Section Break",
				"label": _("مدل شایستگی سازمانی"),
				"insert_after": "attendance_settings_section",
			},
			{
				"fieldname": "core_competencies",
				"fieldtype": "Table",
				"label": _("شایستگی‌های عمومی سازمان"),
				"options": "Competency Requirement",
				"insert_after": "competency_model_settings_section",
			},
		],
		"Employee": [
			{
				"fieldname": "employment_type",
				"fieldtype": "Link",
				"ignore_user_permissions": 1,
				"label": _("Employment Type"),
				"options": "Employment Type",
				"insert_after": "department",
			},
			{
				"fieldname": "job_applicant",
				"fieldtype": "Link",
				"label": _("Job Applicant"),
				"options": "Job Applicant",
				"insert_after": "employment_details",
			},
			{
				"fieldname": "development_planning_section",
				"fieldtype": "Section Break",
				"label": _("برنامه توسعه فردی"),
				"insert_after": "job_applicant",
			},
			{
				"fieldname": "active_idp",
				"fieldtype": "Link",
				"label": _("برنامه توسعه فردی فعال"),
				"options": "Individual Development Plan",
				"insert_after": "development_planning_section",
			},
			{
				"fieldname": "latest_nine_box_assessment",
				"fieldtype": "Link",
				"label": _("آخرین ارزیابی ۹ خانه"),
				"options": "Nine Box Assessment",
				"insert_after": "active_idp",
			},
			{
				"fieldname": "target_career_transition",
				"fieldtype": "Link",
				"label": _("مسیر شغلی هدف"),
				"options": "Career Path Transition",
				"insert_after": "latest_nine_box_assessment",
			},
			{
				"fieldname": "grade",
				"fieldtype": "Link",
				"label": _("Grade"),
				"options": "Employee Grade",
				"insert_after": "branch",
			},
			{
				"fieldname": "national_id_details_section",
				"fieldtype": "Section Break",
				"label": _("مشخصات شناسنامه"),
				"insert_after": "marital_status",
			},
			{
				"fieldname": "birth_certificate_number",
				"fieldtype": "Data",
				"label": _("شماره شناسنامه"),
				"insert_after": "national_id_details_section",
			},
			{
				"fieldname": "birth_certificate_column_break",
				"fieldtype": "Column Break",
				"insert_after": "birth_certificate_number",
			},
			{
				"fieldname": "birth_certificate_serial",
				"fieldtype": "Data",
				"label": _("سری شناسنامه"),
				"insert_after": "birth_certificate_column_break",
			},
			{
				"fieldname": "birth_certificate_issue_date",
				"fieldtype": "Date",
				"label": _("تاریخ صدور شناسنامه"),
				"insert_after": "birth_certificate_serial",
			},
			{
				"fieldname": "birth_certificate_issue_place",
				"fieldtype": "Data",
				"label": _("محل صدور شناسنامه"),
				"insert_after": "birth_certificate_issue_date",
			},
			{
				"fieldname": "children_count",
				"fieldtype": "Int",
				"label": _("تعداد فرزند"),
				"default": "0",
				"insert_after": "marital_status",
			},
			{
				"fieldname": "personnel_case_no",
				"fieldtype": "Data",
				"label": _("شماره پرونده"),
				"insert_after": "salutation",
				"in_preview": 1,
			},
			{
				"fieldname": "attendance_device_info_section",
				"fieldtype": "Section Break",
				"label": _("دستگاه حضور غیاب"),
				"insert_after": "personnel_case_no",
				"collapsible": 1,
			},
			{
				"collapsible": 1,
				"fieldname": "health_insurance_section",
				"fieldtype": "Section Break",
				"label": _("Health Insurance"),
				"insert_after": "health_details",
			},
			{
				"fieldname": "health_insurance_provider",
				"fieldtype": "Link",
				"label": _("Health Insurance Provider"),
				"options": "Employee Health Insurance",
				"insert_after": "health_insurance_section",
			},
			{
				"depends_on": "eval:doc.health_insurance_provider",
				"fieldname": "health_insurance_no",
				"fieldtype": "Data",
				"label": _("Health Insurance No"),
				"insert_after": "health_insurance_provider",
			},
			{
				"fieldname": "approvers_section",
				"fieldtype": "Section Break",
				"label": _("Approvers"),
				"insert_after": "holiday_list",
			},
			{
				"fieldname": "expense_approver",
				"fieldtype": "Link",
				"label": _("Expense Approver"),
				"options": "User",
				"insert_after": "approvers_section",
			},
			{
				"fieldname": "leave_approver",
				"fieldtype": "Link",
				"label": _("Leave Approver"),
				"options": "User",
				"insert_after": "expense_approver",
			},
			{
				"fieldname": "column_break_45",
				"fieldtype": "Column Break",
				"insert_after": "leave_approver",
			},
			{
				"fieldname": "shift_request_approver",
				"fieldtype": "Link",
				"label": _("Shift Request Approver"),
				"options": "User",
				"insert_after": "column_break_45",
			},
			{
				"default": "0",
				"fieldname": "is_shift_allocator",
				"fieldtype": "Check",
				"label": _("تخصیص‌دهنده شیفت"),
				"insert_after": "shift_request_approver",
			},
			{
				"default": "0",
				"fieldname": "needs_shift_registration",
				"fieldtype": "Check",
				"label": _("نیازمند ثبت شیفت"),
				"insert_after": "is_shift_allocator",
			},
			{
				"default": "0",
				"fieldname": "has_rotational_shift",
				"fieldtype": "Check",
				"label": _("دارای شیفت چرخشی"),
				"insert_after": "needs_shift_registration",
			},
			{
				"default": "0",
				"fieldname": "variable_shift",
				"fieldtype": "Check",
				"label": _("شیفت متغیر"),
				"insert_after": "has_rotational_shift",
			},
			{
				"fieldname": "forbidden_shift_days",
				"fieldtype": "Small Text",
				"label": _("روزهای غیرمجاز شیفت"),
				"options": "Saturday\nSunday\nMonday\nTuesday\nWednesday\nThursday\nFriday",
				"insert_after": "variable_shift",
			},
			{
				"fieldname": "employee_shift_duty_roles",
				"fieldtype": "Table",
				"label": _("نقش‌های شیفت کارمند"),
				"options": "Employee Shift Duty Role",
				"insert_after": "forbidden_shift_days",
			},
			{
				"fieldname": "salary_cb",
				"fieldtype": "Column Break",
				"insert_after": "employee_shift_duty_roles",
			},
			{
				"fetch_from": "department.payroll_cost_center",
				"fetch_if_empty": 1,
				"fieldname": "payroll_cost_center",
				"fieldtype": "Link",
				"label": _("Payroll Cost Center"),
				"options": "Cost Center",
				"insert_after": "salary_cb",
			},
		],
		"Shift Assignment": [
			{
				"default": "0",
				"fieldname": "generated_from_weekly_plan",
				"fieldtype": "Check",
				"label": _("Generated from Weekly Shift Plan"),
				"insert_after": "shift_request",
				"read_only": 1,
			},
			{
				"fieldname": "weekly_shift_plan",
				"fieldtype": "Link",
				"label": _("Weekly Shift Plan"),
				"options": "Weekly Shift Plan",
				"insert_after": "generated_from_weekly_plan",
				"read_only": 1,
			},
			{
				"fieldname": "weekly_shift_plan_slot",
				"fieldtype": "Data",
				"label": _("Weekly Shift Plan Slot"),
				"insert_after": "weekly_shift_plan",
				"read_only": 1,
			},
			{
				"default": "0",
				"fieldname": "generated_from_finalization",
				"fieldtype": "Check",
				"label": _("Generated from Weekly Shift Finalization"),
				"insert_after": "weekly_shift_plan_slot",
				"read_only": 1,
			},
			{
				"fieldname": "weekly_shift_finalization",
				"fieldtype": "Link",
				"label": _("Weekly Shift Finalization"),
				"options": "Weekly Shift Finalization",
				"insert_after": "generated_from_finalization",
				"read_only": 1,
			},
			{
				"fieldname": "weekly_shift_finalization_slot",
				"fieldtype": "Data",
				"label": _("Weekly Shift Finalization Slot"),
				"insert_after": "weekly_shift_finalization",
				"read_only": 1,
			},
		],
		"Project": [
			{
				"fieldname": "total_expense_claim",
				"fieldtype": "Currency",
				"label": _("Total Expense Claim (via Expense Claims)"),
				"read_only": 1,
				"insert_after": "total_costing_amount",
			},
		],
		"Task": [
			{
				"fieldname": "total_expense_claim",
				"fieldtype": "Currency",
				"label": _("Total Expense Claim (via Expense Claim)"),
				"options": "Company:company:default_currency",
				"read_only": 1,
				"insert_after": "total_costing_amount",
			},
		],
		"Timesheet": [
			{
				"fieldname": "salary_slip",
				"fieldtype": "Link",
				"label": _("Salary Slip"),
				"no_copy": 1,
				"options": "Salary Slip",
				"print_hide": 1,
				"read_only": 1,
				"insert_after": "column_break_3",
			},
		],
		"Leave Type": [
			{
				"fieldname": "leave_description_iran",
				"fieldtype": "Small Text",
				"label": _("توضیحات نوع مرخصی"),
				"description": _("توضیح قانونی یا سیاست داخلی سازمان برای این نوع مرخصی."),
				"insert_after": "leave_type_name",
			},
		],
		"Terms and Conditions": [
			{
				"default": "1",
				"fieldname": "hr",
				"fieldtype": "Check",
				"label": _("HR"),
				"insert_after": "buying",
			},
		],
	}


def make_fixtures():
	records = [
		# expense claim type
		{"doctype": "Expense Claim Type", "name": _("Calls"), "expense_type": _("Calls")},
		{"doctype": "Expense Claim Type", "name": _("Food"), "expense_type": _("Food")},
		{"doctype": "Expense Claim Type", "name": _("Medical"), "expense_type": _("Medical")},
		{"doctype": "Expense Claim Type", "name": _("Others"), "expense_type": _("Others")},
		{"doctype": "Expense Claim Type", "name": _("Travel"), "expense_type": _("Travel")},
		# vehicle service item
		{"doctype": "Vehicle Service Item", "service_item": "Brake Oil"},
		{"doctype": "Vehicle Service Item", "service_item": "Brake Pad"},
		{"doctype": "Vehicle Service Item", "service_item": "Clutch Plate"},
		{"doctype": "Vehicle Service Item", "service_item": "Engine Oil"},
		{"doctype": "Vehicle Service Item", "service_item": "Oil Change"},
		{"doctype": "Vehicle Service Item", "service_item": "Wheels"},
		# Employment Type
		{"doctype": "Employment Type", "employee_type_name": _("Full-time")},
		{"doctype": "Employment Type", "employee_type_name": _("Part-time")},
		{"doctype": "Employment Type", "employee_type_name": _("Probation")},
		{"doctype": "Employment Type", "employee_type_name": _("Contract")},
		{"doctype": "Employment Type", "employee_type_name": _("Commission")},
		{"doctype": "Employment Type", "employee_type_name": _("Piecework")},
		{"doctype": "Employment Type", "employee_type_name": _("Intern")},
		{"doctype": "Employment Type", "employee_type_name": _("Apprentice")},
		# Job Applicant Source
		{"doctype": "Job Applicant Source", "source_name": _("Website Listing")},
		{"doctype": "Job Applicant Source", "source_name": _("Walk In")},
		{"doctype": "Job Applicant Source", "source_name": _("Employee Referral")},
		{"doctype": "Job Applicant Source", "source_name": _("Campaign")},
		# Offer Term
		{"doctype": "Offer Term", "offer_term": _("Date of Joining")},
		{"doctype": "Offer Term", "offer_term": _("Annual Salary")},
		{"doctype": "Offer Term", "offer_term": _("Probationary Period")},
		{"doctype": "Offer Term", "offer_term": _("Employee Benefits")},
		{"doctype": "Offer Term", "offer_term": _("Working Hours")},
		{"doctype": "Offer Term", "offer_term": _("Stock Options")},
		{"doctype": "Offer Term", "offer_term": _("Department")},
		{"doctype": "Offer Term", "offer_term": _("Job Description")},
		{"doctype": "Offer Term", "offer_term": _("Responsibilities")},
		{"doctype": "Offer Term", "offer_term": _("Leaves per Year")},
		{"doctype": "Offer Term", "offer_term": _("Notice Period")},
		{"doctype": "Offer Term", "offer_term": _("Incentives")},
		# Email Account
		{"doctype": "Email Account", "email_id": "jobs@example.com", "append_to": "Job Applicant"},
	]

	records.extend(get_default_leave_type_records_for_iran())
	make_records(records)


def get_default_leave_type_records_for_iran():
	return [
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی استحقاقی"),
			"name": _("مرخصی استحقاقی"),
			"max_leaves_allowed": 26,
			"max_continuous_days_allowed": 26,
			"is_carry_forward": 1,
			"maximum_carry_forwarded_leaves": 9,
			"expire_carry_forwarded_leaves_after_days": 365,
			"allow_encashment": 1,
			"is_earned_leave": 1,
			"earned_leave_frequency": "Monthly",
			"allocate_on_day": "Last Day",
			"rounding": "0.5",
			"include_holiday": 0,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی ساعتی"),
			"name": _("مرخصی ساعتی"),
			"max_leaves_allowed": 24,
			"max_continuous_days_allowed": 1,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"include_holiday": 0,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی بدون حقوق"),
			"name": _("مرخصی بدون حقوق"),
			"max_leaves_allowed": 30,
			"applicable_after": 90,
			"max_continuous_days_allowed": 30,
			"is_carry_forward": 0,
			"is_lwp": 1,
			"include_holiday": 0,
			"allow_over_allocation": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی استعلاجی"),
			"name": _("مرخصی استعلاجی"),
			"max_leaves_allowed": 365,
			"max_continuous_days_allowed": 30,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"include_holiday": 1,
			"allow_over_allocation": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی زایمان"),
			"name": _("مرخصی زایمان"),
			"max_leaves_allowed": 270,
			"max_continuous_days_allowed": 270,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"include_holiday": 1,
			"allow_over_allocation": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی پدر هنگام تولد فرزند"),
			"name": _("مرخصی پدر هنگام تولد فرزند"),
			"max_leaves_allowed": 3,
			"max_continuous_days_allowed": 3,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"include_holiday": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی ازدواج"),
			"name": _("مرخصی ازدواج"),
			"max_leaves_allowed": 3,
			"max_continuous_days_allowed": 3,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"include_holiday": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی فوت بستگان درجه یک"),
			"name": _("مرخصی فوت بستگان درجه یک"),
			"max_leaves_allowed": 3,
			"max_continuous_days_allowed": 3,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"include_holiday": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی حج واجب"),
			"name": _("مرخصی حج واجب"),
			"max_leaves_allowed": 30,
			"applicable_after": 365,
			"max_continuous_days_allowed": 30,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"include_holiday": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی جبرانی"),
			"name": _("مرخصی جبرانی"),
			"max_leaves_allowed": 10,
			"max_continuous_days_allowed": 2,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"include_holiday": 0,
			"is_compensatory": 1,
			"allow_over_allocation": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("ماموریت"),
			"name": _("ماموریت"),
			"max_leaves_allowed": 60,
			"max_continuous_days_allowed": 15,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"include_holiday": 1,
			"allow_over_allocation": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی آموزشی/تحصیلی"),
			"name": _("مرخصی آموزشی/تحصیلی"),
			"max_leaves_allowed": 12,
			"applicable_after": 180,
			"max_continuous_days_allowed": 5,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"include_holiday": 0,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی اضطراری"),
			"name": _("مرخصی اضطراری"),
			"max_leaves_allowed": 3,
			"max_continuous_days_allowed": 2,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"allow_negative": 1,
			"allow_over_allocation": 1,
			"include_holiday": 0,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی اختیاری"),
			"name": _("مرخصی اختیاری"),
			"max_leaves_allowed": 2,
			"max_continuous_days_allowed": 1,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"is_optional_leave": 1,
			"include_holiday": 0,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی تشویقی"),
			"name": _("مرخصی تشویقی"),
			"max_leaves_allowed": 5,
			"max_continuous_days_allowed": 2,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"include_holiday": 0,
			"allow_over_allocation": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("مرخصی امور پزشکی"),
			"name": _("مرخصی امور پزشکی"),
			"max_leaves_allowed": 6,
			"max_continuous_days_allowed": 1,
			"is_carry_forward": 0,
			"allow_encashment": 0,
			"include_holiday": 0,
		},
	]


def setup_notifications():
	base_path = frappe.get_app_path("hrms", "hr", "doctype")

	# Leave Application
	response = frappe.read_file(
		os.path.join(base_path, "leave_application/leave_application_email_template.html")
	)
	records = [
		{
			"doctype": "Email Template",
			"name": _("Leave Approval Notification"),
			"response": response,
			"subject": _("Leave Approval Notification"),
			"owner": frappe.session.user,
		}
	]
	records += [
		{
			"doctype": "Email Template",
			"name": _("Leave Status Notification"),
			"response": response,
			"subject": _("Leave Status Notification"),
			"owner": frappe.session.user,
		}
	]

	# Interview
	response = frappe.read_file(
		os.path.join(base_path, "interview/interview_reminder_notification_template.html")
	)
	records += [
		{
			"doctype": "Email Template",
			"name": _("Interview Reminder"),
			"response": response,
			"subject": _("Interview Reminder"),
			"owner": frappe.session.user,
		}
	]
	response = frappe.read_file(
		os.path.join(base_path, "interview/interview_feedback_reminder_template.html")
	)
	records += [
		{
			"doctype": "Email Template",
			"name": _("Interview Feedback Reminder"),
			"response": response,
			"subject": _("Interview Feedback Reminder"),
			"owner": frappe.session.user,
		}
	]

	# Exit Interview
	response = frappe.read_file(
		os.path.join(base_path, "exit_interview/exit_questionnaire_notification_template.html")
	)
	records += [
		{
			"doctype": "Email Template",
			"name": _("Exit Questionnaire Notification"),
			"response": response,
			"subject": _("Exit Questionnaire Notification"),
			"owner": frappe.session.user,
		}
	]

	make_records(records)


def update_hr_defaults():
	hr_settings = frappe.get_doc("HR Settings")
	hr_settings.emp_created_by = "Naming Series"
	hr_settings.leave_approval_notification_template = _("Leave Approval Notification")
	hr_settings.leave_status_notification_template = _("Leave Status Notification")

	hr_settings.send_interview_reminder = 1
	hr_settings.interview_reminder_template = _("Interview Reminder")
	hr_settings.remind_before = "00:15:00"

	hr_settings.send_interview_feedback_reminder = 1
	hr_settings.feedback_reminder_notification_template = _("Interview Feedback Reminder")

	hr_settings.exit_questionnaire_notification_template = _("Exit Questionnaire Notification")
	hr_settings.save()


def set_single_defaults():
	for dt in ("HR Settings", "Payroll Settings"):
		default_values = frappe.get_all(
			"DocField",
			filters={"parent": dt},
			fields=["fieldname", "default"],
			as_list=True,
		)
		if default_values:
			try:
				doc = frappe.get_doc(dt, dt)
				for fieldname, value in default_values:
					doc.set(fieldname, value)
				doc.flags.ignore_mandatory = True
				doc.save()
			except frappe.ValidationError:
				pass


def create_default_role_profiles():
	for role_profile_name, roles in DEFAULT_ROLE_PROFILES.items():
		if frappe.db.exists("Role Profile", role_profile_name):
			continue

		role_profile = frappe.new_doc("Role Profile")
		role_profile.role_profile = role_profile_name
		for role in roles:
			role_profile.append("roles", {"role": role})

		role_profile.insert(ignore_permissions=True)


def get_post_install_patches():
	return (
		"erpnext.patches.v13_0.move_tax_slabs_from_payroll_period_to_income_tax_slab",
		"erpnext.patches.v13_0.move_doctype_reports_and_notification_from_hr_to_payroll",
		"erpnext.patches.v13_0.move_payroll_setting_separately_from_hr_settings",
		"erpnext.patches.v13_0.update_start_end_date_for_old_shift_assignment",
		"erpnext.patches.v13_0.updates_for_multi_currency_payroll",
		"erpnext.patches.v13_0.update_reason_for_resignation_in_employee",
		"erpnext.patches.v13_0.set_company_in_leave_ledger_entry",
		"erpnext.patches.v13_0.rename_stop_to_send_birthday_reminders",
		"erpnext.patches.v13_0.set_training_event_attendance",
		"erpnext.patches.v14_0.set_payroll_cost_centers",
		"erpnext.patches.v13_0.update_employee_advance_status",
		"erpnext.patches.v13_0.update_expense_claim_status_for_paid_advances",
		"erpnext.patches.v14_0.delete_employee_transfer_property_doctype",
		"erpnext.patches.v13_0.set_payroll_entry_status",
		# HRMS
		"create_country_fixtures",
		"update_allocate_on_in_leave_type",
		"update_performance_module_changes",
	)


def run_post_install_patches():
	print("\nPatching Existing Data...")

	POST_INSTALL_PATCHES = get_post_install_patches()
	frappe.flags.in_patch = True

	try:
		for patch in POST_INSTALL_PATCHES:
			patch_name = patch.split(".")[-1]
			if not patch_name:
				continue

			frappe.get_attr(f"hrms.patches.post_install.{patch_name}.execute")()
	finally:
		frappe.flags.in_patch = False


# LENDING APP SETUP & CLEANUP
def create_salary_slip_loan_fields():
	if "lending" in frappe.get_installed_apps():
		create_custom_fields(get_salary_slip_loan_fields(), ignore_validate=True)


def add_lending_docperms_to_ess():
	doc = frappe.get_doc("User Type", "Employee Self Service")

	loan_docperms = get_lending_docperms_for_ess()
	append_docperms_to_user_type(loan_docperms, doc)

	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


def remove_lending_docperms_from_ess():
	doc = frappe.get_doc("User Type", "Employee Self Service")

	loan_docperms = get_lending_docperms_for_ess()

	for row in list(doc.user_doctypes):
		if row.document_type in loan_docperms:
			doc.user_doctypes.remove(row)

	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


# ESS USER TYPE SETUP & CLEANUP
def add_non_standard_user_types():
	user_types = get_user_types_data()
	update_user_type_doctype_limit(user_types)

	for user_type, data in user_types.items():
		create_custom_role(data)
		create_user_type(user_type, data)


def update_user_type_doctype_limit(user_types=None):
	if not user_types:
		user_types = get_user_types_data()

	user_type_limit = {}
	for user_type, __ in user_types.items():
		user_type_limit.setdefault(frappe.scrub(user_type), 40)

	update_site_config("user_type_doctype_limit", user_type_limit)


def get_user_types_data():
	return {
		"Employee Self Service": {
			"role": "Employee Self Service",
			"apply_user_permission_on": "Employee",
			"user_id_field": "user_id",
			"doctypes": {
				# masters
				"Holiday List": ["read"],
				"Employee": ["read", "write"],
				"Company": ["read"],
				# payroll
				"Salary Slip": ["read"],
				"Employee Benefit Application": ["read", "write", "create", "delete"],
				# expenses
				"Expense Claim": ["read", "write", "create", "delete"],
				"Expense Claim Type": ["read"],
				"Employee Advance": ["read", "write", "create", "delete"],
				# leave and attendance
				"Leave Application": ["read", "write", "create", "delete"],
				"Attendance Request": ["read", "write", "create", "delete"],
				"Compensatory Leave Request": ["read", "write", "create", "delete"],
				# tax
				"Employee Tax Exemption Declaration": ["read", "write", "create", "delete"],
				"Employee Tax Exemption Proof Submission": ["read", "write", "create", "delete"],
				# projects
				"Timesheet": ["read", "write", "create", "delete", "submit", "cancel", "amend"],
				# trainings
				"Training Program": ["read"],
				"Training Feedback": ["read", "write", "create", "delete", "submit", "cancel", "amend"],
				# shifts
				"Employee Checkin": ["read"],
				"Shift Request": ["read", "write", "create", "delete", "submit", "cancel", "amend"],
				# misc
				"Employee Grievance": ["read", "write", "create", "delete"],
				"Employee Referral": ["read", "write", "create", "delete"],
				"Travel Request": ["read", "write", "create", "delete"],
			},
		}
	}


def get_lending_docperms_for_ess():
	return {
		"Loan": ["read"],
		"Loan Application": ["read", "write", "create", "delete", "submit"],
		"Loan Product": ["read"],
	}


def create_custom_role(data):
	if data.get("role") and not frappe.db.exists("Role", data.get("role")):
		frappe.get_doc(
			{"doctype": "Role", "role_name": data.get("role"), "desk_access": 1, "is_custom": 1}
		).insert(ignore_permissions=True)


def create_user_type(user_type, data):
	if frappe.db.exists("User Type", user_type):
		doc = frappe.get_cached_doc("User Type", user_type)
		doc.user_doctypes = []
	else:
		doc = frappe.new_doc("User Type")
		doc.update(
			{
				"name": user_type,
				"role": data.get("role"),
				"user_id_field": data.get("user_id_field"),
				"apply_user_permission_on": data.get("apply_user_permission_on"),
			}
		)

	docperms = data.get("doctypes")
	if doc.role == "Employee Self Service" and "lending" in frappe.get_installed_apps():
		docperms.update(get_lending_docperms_for_ess())

	append_docperms_to_user_type(docperms, doc)

	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


def append_docperms_to_user_type(docperms, doc):
	existing_doctypes = [d.document_type for d in doc.user_doctypes]

	for doctype, perms in docperms.items():
		if doctype in existing_doctypes:
			continue

		args = {"document_type": doctype}
		for perm in perms:
			args[perm] = 1

		doc.append("user_doctypes", args)


def update_select_perm_after_install():
	if frappe.flags.update_select_perm_after_migrate:
		frappe.flags.ignore_select_perm = False
		for row in frappe.get_all("User Type", filters={"is_standard": 0}):
			print("Updating user type :- ", row.name)
			doc = frappe.get_doc("User Type", row.name)
			doc.flags.ignore_links = True
			doc.save()

		frappe.flags.update_select_perm_after_migrate = False

	ensure_global_print_style()
	sync_hr_workspace_extensions()
	remove_home_workspace_sidebar()


def ensure_global_print_style():
	style_name = "Peyda Global Print"
	regular_url = frappe.utils.get_url("/assets/hrms/fonts/Pevda-Reqular.ttf")
	medium_url = frappe.utils.get_url("/assets/hrms/fonts/Peyda-Medium.ttf")
	semibold_url = frappe.utils.get_url("/assets/hrms/fonts/Peyda-SemiBold.ttf")
	bold_url = frappe.utils.get_url("/assets/hrms/fonts/Peyda-Bold.ttf")

	base_css = f"""
@font-face {{
	font-family: "Peyda";
	src: url("{regular_url}") format("truetype");
	font-weight: 400;
	font-style: normal;
}}

@font-face {{
	font-family: "Peyda";
	src: url("{medium_url}") format("truetype");
	font-weight: 500;
	font-style: normal;
}}

@font-face {{
	font-family: "Peyda";
	src: url("{semibold_url}") format("truetype");
	font-weight: 600;
	font-style: normal;
}}

@font-face {{
	font-family: "Peyda";
	src: url("{bold_url}") format("truetype");
	font-weight: 700;
	font-style: normal;
}}

.print-format,
.print-format * {{
	font-family: "Peyda", Tahoma, Arial, sans-serif !important;
}}
""".strip()

	if not frappe.db.exists("Print Style", style_name):
		frappe.get_doc(
			{
				"doctype": "Print Style",
				"print_style_name": style_name,
				"css": base_css,
				"standard": "No",
				"disabled": 0,
			}
		).insert(ignore_permissions=True)
	else:
		style_doc = frappe.get_doc("Print Style", style_name)
		if (style_doc.css or "").strip() != base_css:
			style_doc.css = base_css
			style_doc.save(ignore_permissions=True)

	if frappe.db.get_single_value("Print Settings", "print_style") != style_name:
		frappe.db.set_single_value("Print Settings", "print_style", style_name)

	frappe.clear_cache()


def make_people_workspace_standard():
	"""Compatibility hook used by before_migrate in v16."""
	if frappe.db.exists("Workspace Sidebar", "People"):
		frappe.db.set_value("Workspace Sidebar", "People", "standard", 1)


def sync_hr_workspace_extensions():
	try:
		from hrms.workspace_sync import sync_hr_workspace_setup

		sync_hr_workspace_setup()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "HR Workspace Sync Failed")


def delete_custom_fields(custom_fields: dict):
	"""
	:param custom_fields: a dict like `{'Salary Slip': [{fieldname: 'loans', ...}]}`
	"""
	for doctype, fields in custom_fields.items():
		frappe.db.delete(
			"Custom Field",
			{
				"fieldname": ("in", [field["fieldname"] for field in fields]),
				"dt": doctype,
			},
		)

		frappe.clear_cache(doctype=doctype)


DEFAULT_ROLE_PROFILES = {
	"HR": [
		"HR User",
		"HR Manager",
		"Leave Approver",
		"Expense Approver",
	],
}


def get_salary_slip_loan_fields():
	return {
		"Salary Slip": [
			{
				"fieldname": "loan_repayment_sb_1",
				"fieldtype": "Section Break",
				"label": _("Loan Repayment"),
				"depends_on": "total_loan_repayment",
				"insert_after": "base_total_deduction",
			},
			{
				"fieldname": "loans",
				"fieldtype": "Table",
				"label": _("Employee Loan"),
				"options": "Salary Slip Loan",
				"print_hide": 1,
				"insert_after": "loan_repayment_sb_1",
			},
			{
				"fieldname": "loan_details_sb_1",
				"fieldtype": "Section Break",
				"depends_on": "eval:doc.docstatus != 0",
				"insert_after": "loans",
			},
			{
				"fieldname": "total_principal_amount",
				"fieldtype": "Currency",
				"label": _("Total Principal Amount"),
				"default": "0",
				"options": "Company:company:default_currency",
				"read_only": 1,
				"insert_after": "loan_details_sb_1",
			},
			{
				"fieldname": "total_interest_amount",
				"fieldtype": "Currency",
				"label": _("Total Interest Amount"),
				"default": "0",
				"options": "Company:company:default_currency",
				"read_only": 1,
				"insert_after": "total_principal_amount",
			},
			{
				"fieldname": "loan_cb_1",
				"fieldtype": "Column Break",
				"insert_after": "total_interest_amount",
			},
			{
				"fieldname": "total_loan_repayment",
				"fieldtype": "Currency",
				"label": _("Total Loan Repayment"),
				"default": "0",
				"options": "Company:company:default_currency",
				"read_only": 1,
				"insert_after": "loan_cb_1",
			},
		],
		"Loan": [
			{
				"default": "0",
				"depends_on": 'eval:doc.applicant_type=="Employee"',
				"fieldname": "repay_from_salary",
				"fieldtype": "Check",
				"label": _("Repay From Salary"),
				"insert_after": "status",
			},
		],
		"Loan Repayment": [
			{
				"default": "0",
				"fieldname": "repay_from_salary",
				"fieldtype": "Check",
				"label": _("Repay From Salary"),
				"insert_after": "is_term_loan",
			},
			{
				"depends_on": "eval:doc.repay_from_salary",
				"fieldname": "payroll_payable_account",
				"fieldtype": "Link",
				"label": _("Payroll Payable Account"),
				"mandatory_depends_on": "eval:doc.repay_from_salary",
				"options": "Account",
				"insert_after": "payment_account",
			},
			{
				"default": "0",
				"depends_on": 'eval:doc.applicant_type=="Employee"',
				"fieldname": "process_payroll_accounting_entry_based_on_employee",
				"hidden": 1,
				"fieldtype": "Check",
				"label": _("Process Payroll Accounting Entry based on Employee"),
				"insert_after": "repay_from_salary",
			},
		],
	}
