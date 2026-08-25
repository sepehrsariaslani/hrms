import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from hrms.overrides.company import run_regional_setup


IRAN_COUNTRY_ALIASES = {
	"iran",
	"iran, islamic republic of",
	"islamic republic of iran",
	"ایران",
}

TAB_LABEL_UPDATES = {
	"basic_details_tab": "اطلاعات پایه",
	"contact_details": "سازمانی و شغلی",
	"attendance_and_leave_details": "تماس و آدرس",
	"salary_information": "حضور و شیفت",
	"personal_details": "حقوق و پرداخت",
	"profile_tab": "مشخصات فردی",
	"employment_details": "سوابق و پروفایل",
	"exit": "استخدام و قرارداد",
	"connections_tab": "خروج و ارتباطات",
}

TAB_FIELD_CHAINS = [
	(
		"basic_details_tab",
		[
			"basic_information",
			"employee",
			"naming_series",
			"first_name",
			"middle_name",
			"last_name",
			"employee_name",
			"column_break_9",
			"gender",
			"salutation",
			"date_of_birth",
			"personnel_case_no",
			"column_break1",
			"status",
			"date_of_joining",
			"image",
			"company_details_section",
			"company",
			"department",
			"branch",
			"column_break_25",
			"designation",
			"employment_type",
			"grade",
			"column_break_18",
			"reports_to",
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
		],
	),
	(
		"contact_details",
		[
			"employee_designations",
			"employee_number",
		],
	),
	(
		"attendance_and_leave_details",
		[
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
	),
	(
		"salary_information",
		[
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
	),
	(
		"personal_details",
		[
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
	),
	(
		"profile_tab",
		[
			"marital_status",
			"blood_group",
			"custom_national_id_code",
			"custom_father_name",
			"column_break_40",
			"family_background",
			"health_details",
			"column_break6",
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
	),
	(
		"employment_details",
		[
			"bio",
			"educational_qualification",
			"education",
			"previous_work_experience",
			"external_work_history",
			"history_in_company",
			"internal_work_history",
		],
	),
	(
		"exit",
		[
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
	),
	(
		"connections_tab",
		[
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
		],
	),
]

HIDDEN_FIELD_UPDATES = {
	"employee": 1,
	"employee_number": 1,
	"image": 1,
	"lft": 1,
	"rgt": 1,
	"old_parent": 1,
}

SECTION_LABEL_UPDATES = {
	"erpnext_user": "کاربر سیستمی",
	"company_details_section": "جایگاه سازمانی",
	"approvers_section": "تاییدکنندگان",
	"address_section": "آدرس",
	"emergency_contact_details": "تماس اضطراری",
	"bank_details_section": "اطلاعات بانکی",
	"health_insurance_section": "بیمه درمانی",
	"passport_details_section": "اطلاعات گذرنامه",
	"educational_qualification": "تحصیلات",
	"previous_work_experience": "سوابق خارج از شرکت",
	"history_in_company": "سوابق داخل شرکت",
	"feedback_section": "بازخورد خروج",
}


def execute():
	if not frappe.db.exists("DocType", "Employee"):
		return

	ensure_iran_custom_fields_exist()
	meta = frappe.get_meta("Employee")

	for fieldname, label in TAB_LABEL_UPDATES.items():
		_set_field_property(meta, fieldname, "label", label, "Data")

	for fieldname, label in SECTION_LABEL_UPDATES.items():
		_set_field_property(meta, fieldname, "label", label, "Data")

	for tab_fieldname, ordered_fields in TAB_FIELD_CHAINS:
		_reorder_chain(meta, tab_fieldname, ordered_fields)

	for fieldname, hidden in HIDDEN_FIELD_UPDATES.items():
		_set_field_property(meta, fieldname, "hidden", hidden, "Check")

	frappe.clear_cache(doctype="Employee")


def ensure_iran_custom_fields_exist():
	for country in frappe.get_all("Company", pluck="country", distinct=True):
		if (country or "").strip().lower() in IRAN_COUNTRY_ALIASES:
			run_regional_setup(country)
			return


def _reorder_chain(meta, anchor_fieldname: str, ordered_fields: list[str]):
	if not meta.has_field(anchor_fieldname):
		return

	current_anchor = anchor_fieldname
	for fieldname in ordered_fields:
		if not meta.has_field(fieldname):
			continue
		_set_insert_after(meta, fieldname, current_anchor)
		current_anchor = fieldname


def _set_insert_after(meta, fieldname: str, insert_after: str):
	if not meta.has_field(fieldname) or not meta.has_field(insert_after):
		return

	if frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": fieldname}):
		frappe.db.set_value(
			"Custom Field",
			{"dt": "Employee", "fieldname": fieldname},
			"insert_after",
			insert_after,
			update_modified=False,
		)
	else:
		make_property_setter(
			"Employee",
			fieldname,
			"insert_after",
			insert_after,
			"Data",
			validate_fields_for_doctype=False,
		)


def _set_field_property(meta, fieldname: str, property_name: str, value, property_type: str):
	if not meta.has_field(fieldname):
		return

	make_property_setter(
		"Employee",
		fieldname,
		property_name,
		value,
		property_type,
		validate_fields_for_doctype=False,
	)
