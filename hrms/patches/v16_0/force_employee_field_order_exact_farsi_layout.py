import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from hrms.overrides.company import run_regional_setup


IRAN_COUNTRY_ALIASES = {
	"iran",
	"iran, islamic republic of",
	"islamic republic of iran",
	"ایران",
}

EXACT_FIELD_ORDER = [
	# Tab 1: اطلاعات پایه
	"basic_details_tab",
	"basic_information",
	"employee",
	"naming_series",
	"first_name",
	"middle_name",
	"last_name",
	"employee_name",
	"column_break_9",
	"gender",
	"date_of_birth",
	"personnel_case_no",
	"salutation",
	"column_break1",
	"date_of_joining",
	"image",
	"status",
	"company_details_section",
	"company",
	"department",
	"column_break_25",
	"designation",
	"employment_type",
	"grade",
	"reports_to",
	"column_break_18",
	"branch",
	"approvers_section",
	"expense_approver",
	"leave_approver",
	"column_break_45",
	"shift_request_approver",
	"payroll_cost_center",
	"erpnext_user",
	"user_id",
	"column_break_xwnm",
	"create_user_automatically",
	"create_user_permission",
	# Tab 2: سازمانی و شغلی
	"contact_details",
	"employee_designations",
	"employee_number",
	# Tab 3: تماس و آدرس
	"attendance_and_leave_details",
	"cell_number",
	"company_email",
	"personal_email",
	"column_break4",
	"prefered_contact_email",
	"prefered_email",
	"unsubscribed",
	"address_section",
	"current_address",
	"current_accommodation_type",
	"column_break_46",
	"permanent_address",
	"permanent_accommodation_type",
	"emergency_contact_details",
	"person_to_be_contacted",
	"column_break_55",
	"emergency_phone_number",
	"column_break_19",
	"relation",
	# Tab 4: حضور و شیفت
	"salary_information",
	"attendance_device_id",
	"column_break_44",
	"holiday_list",
	"attendance_device_info_section",
	"custom_attendance_device_mappings",
	"is_shift_allocator",
	"needs_shift_registration",
	"has_rotational_shift",
	"variable_shift",
	"forbidden_shift_days",
	"employee_shift_duty_roles",
	# Tab 5: حقوق و پرداخت
	"personal_details",
	"ctc",
	"salary_currency",
	"salary_mode",
	"salary_cb",
	"iran_payroll_section",
	"employee_salary_type",
	"insurance_start_date",
	"children_count",
	"daily_pay",
	"monthly_base_pay",
	"base_pay",
	"fixed_monthly_salary",
	"employee_hourly_salary",
	"technical_bonus_daily",
	"monthly_technical_bonus",
	"technical_allowance_monthly",
	"technical_bonus",
	"supervision_allowance",
	"service_allowance_monthly",
	"employee_seniority_daily_base",
	"employee_seniority_monthly_base",
	"housing_allowance",
	"grocery_allowance",
	"marriage_allowance",
	"child_allowance_per_child",
	"child_allowance",
	"min_hourly_wage",
	"overtime_rate",
	"absence_deduction",
	"total_receivable",
	"employer_insurance_share",
	"employee_insurance_share",
	"unemployment_insurance_share",
	"organization_monthly_cost",
	"bank_details_section",
	"bank_name",
	"column_break_heye",
	"bank_ac_no",
	"iban",
	"has_imprest",
	"imprest_accounts",
	# Tab 6: مشخصات فردی
	"profile_tab",
	"marital_status",
	"family_background",
	"column_break6",
	"blood_group",
	"column_break_40",
	"custom_national_id_code",
	"custom_father_name",
	"health_details",
	"national_id_details_section",
	"birth_certificate_number",
	"birth_certificate_issue_date",
	"birth_certificate_issue_place",
	"birth_certificate_column_break",
	"birth_certificate_serial",
	"health_insurance_section",
	"health_insurance_provider",
	"health_insurance_no",
	"passport_details_section",
	"passport_number",
	"valid_upto",
	"column_break_73",
	"date_of_issue",
	"place_of_issue",
	# Tab 7: سوابق و پروفایل
	"employment_details",
	"bio",
	"educational_qualification",
	"education",
	"previous_work_experience",
	"external_work_history",
	"history_in_company",
	"internal_work_history",
	# Tab 8: استخدام و قرارداد
	"exit",
	"job_applicant",
	"scheduled_confirmation_date",
	"column_break_32",
	"final_confirmation_date",
	"contract_end_date",
	"col_break_22",
	"notice_number_of_days",
	"date_of_retirement",
	"development_planning_section",
	"active_idp",
	"latest_nine_box_assessment",
	"target_career_transition",
	# Tab 9: خروج و ارتباطات
	"connections_tab",
	"resignation_letter_date",
	"relieving_date",
	"exit_interview_details",
	"held_on",
	"new_workplace",
	"column_break_99",
	"leave_encashed",
	"encashment_date",
	"feedback_section",
	"reason_for_leaving",
	"column_break_104",
	"feedback",
	"lft",
	"rgt",
	"old_parent",
]


def execute():
	if not frappe.db.exists("DocType", "Employee"):
		return

	ensure_iran_custom_fields_exist()
	meta = frappe.get_meta("Employee")
	all_fields = [df.fieldname for df in meta.fields if df.fieldname]
	final_order = [field for field in EXACT_FIELD_ORDER if field in all_fields]

	# Keep any unforeseen fields at the end, without losing them.
	missing = [field for field in all_fields if field not in final_order]
	final_order.extend(missing)

	make_property_setter(
		"Employee",
		None,
		"field_order",
		"\n".join(final_order),
		"Text",
		validate_fields_for_doctype=False,
	)

	frappe.clear_cache(doctype="Employee")


def ensure_iran_custom_fields_exist():
	for country in frappe.get_all("Company", pluck="country", distinct=True):
		if (country or "").strip().lower() in IRAN_COUNTRY_ALIASES:
			run_regional_setup(country)
			return
