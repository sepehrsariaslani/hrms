import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from hrms.overrides.company import run_regional_setup


IRAN_COUNTRY_ALIASES = {
	"iran",
	"iran, islamic republic of",
	"islamic republic of iran",
	"ایران",
}

TAB_SEQUENCE = [
	"basic_details_tab",
	"contact_details",
	"attendance_and_leave_details",
	"salary_information",
	"personal_details",
	"profile_tab",
	"employment_details",
	"exit",
	"connections_tab",
]

TAB_FIELD_CHAINS = {
	"contact_details": [
		"employee_designations",
		"employee_number",
	],
	"attendance_and_leave_details": [
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
	],
	"salary_information": [
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
	],
	"personal_details": [
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
	],
	"profile_tab": [
		"marital_status",
		"family_background",
		"column_break6",
		"blood_group",
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
	],
	"employment_details": [
		"bio",
		"educational_qualification",
		"education",
		"previous_work_experience",
		"external_work_history",
		"history_in_company",
		"internal_work_history",
	],
	"exit": [
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
	],
	"connections_tab": [
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
	],
}


def execute():
	if not frappe.db.exists("DocType", "Employee"):
		return

	ensure_iran_custom_fields_exist()
	meta = frappe.get_meta("Employee")
	field_order = build_field_order(meta)

	if field_order:
		make_property_setter(
			"Employee",
			None,
			"field_order",
			"\n".join(field_order),
			"Text",
			validate_fields_for_doctype=False,
		)

	frappe.clear_cache(doctype="Employee")


def ensure_iran_custom_fields_exist():
	for country in frappe.get_all("Company", pluck="country", distinct=True):
		if (country or "").strip().lower() in IRAN_COUNTRY_ALIASES:
			run_regional_setup(country)
			return


def build_field_order(meta) -> list[str]:
	all_fields = [df.fieldname for df in meta.fields if df.fieldname]
	field_to_tab = get_field_to_tab_mapping(meta)
	used = set()
	ordered = []

	for tab in TAB_SEQUENCE:
		if tab in all_fields and tab not in used:
			ordered.append(tab)
			used.add(tab)

		for fieldname in TAB_FIELD_CHAINS.get(tab, []):
			if fieldname in all_fields and fieldname not in used:
				ordered.append(fieldname)
				used.add(fieldname)

		for fieldname in all_fields:
			if fieldname in used:
				continue
			if field_to_tab.get(fieldname) == tab:
				ordered.append(fieldname)
				used.add(fieldname)

	for fieldname in all_fields:
		if fieldname not in used:
			ordered.append(fieldname)
			used.add(fieldname)

	return ordered


def get_field_to_tab_mapping(meta) -> dict[str, str]:
	field_to_tab = {}
	current_tab = None
	for df in meta.fields:
		if df.fieldtype == "Tab Break":
			current_tab = df.fieldname
		if df.fieldname:
			field_to_tab[df.fieldname] = current_tab or ""
	return field_to_tab
