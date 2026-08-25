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

# Move the starting field of each major block to a dedicated tab.
BLOCK_START_INSERT_AFTER = {
	"basic_information": "basic_details_tab",
	"company_details_section": "contact_details",
	"cell_number": "attendance_and_leave_details",
	"attendance_device_id": "salary_information",
	"salary_currency": "personal_details",
	"marital_status": "profile_tab",
	"bio": "employment_details",
	"job_applicant": "exit",
	"resignation_letter_date": "connections_tab",
}

# Refine ordering inside tabs / sections.
INSERT_AFTER_UPDATES = {
	# Tab 1: Basic
	"basic_information": "basic_details_tab",
	"employee": "basic_information",
	"naming_series": "employee",
	"first_name": "naming_series",
	"middle_name": "first_name",
	"last_name": "middle_name",
	"employee_name": "last_name",
	"column_break_9": "employee_name",
	"gender": "column_break_9",
	"date_of_birth": "gender",
	"salutation": "date_of_birth",
	"personnel_case_no": "salutation",
	"column_break1": "personnel_case_no",
	"date_of_joining": "column_break1",
	"status": "date_of_joining",
	"image": "status",
	"erpnext_user": "image",
	"user_id": "erpnext_user",
	"column_break_xwnm": "user_id",
	"create_user_automatically": "column_break_xwnm",
	"create_user_permission": "create_user_automatically",
	# Tab 2: Organization
	"company_details_section": "contact_details",
	"company": "company_details_section",
	"department": "company",
	"branch": "department",
	"column_break_25": "branch",
	"designation": "column_break_25",
	"employment_type": "designation",
	"grade": "employment_type",
	"column_break_18": "grade",
	"reports_to": "column_break_18",
	"employee_number": "reports_to",
	"employee_designations": "employee_number",
	"approvers_section": "employee_designations",
	"expense_approver": "approvers_section",
	"leave_approver": "expense_approver",
	"column_break_45": "leave_approver",
	"shift_request_approver": "column_break_45",
	"payroll_cost_center": "shift_request_approver",
	# Tab 3: Contact & Address
	"cell_number": "attendance_and_leave_details",
	"custom_national_id_code": "cell_number",
	"custom_father_name": "custom_national_id_code",
	"column_break_40": "custom_father_name",
	"company_email": "column_break_40",
	"personal_email": "company_email",
	"column_break4": "personal_email",
	"prefered_contact_email": "column_break4",
	"prefered_email": "prefered_contact_email",
	"unsubscribed": "prefered_email",
	"address_section": "unsubscribed",
	"current_address": "address_section",
	"current_accommodation_type": "current_address",
	"column_break_46": "current_accommodation_type",
	"permanent_address": "column_break_46",
	"permanent_accommodation_type": "permanent_address",
	"emergency_contact_details": "permanent_accommodation_type",
	"person_to_be_contacted": "emergency_contact_details",
	"column_break_55": "person_to_be_contacted",
	"emergency_phone_number": "column_break_55",
	"column_break_19": "emergency_phone_number",
	"relation": "column_break_19",
	# Tab 4: Attendance & Shift
	"attendance_device_id": "salary_information",
	"column_break_44": "attendance_device_id",
	"holiday_list": "column_break_44",
	"attendance_device_info_section": "holiday_list",
	"custom_attendance_device_mappings": "attendance_device_info_section",
	"is_shift_allocator": "custom_attendance_device_mappings",
	"needs_shift_registration": "is_shift_allocator",
	"has_rotational_shift": "needs_shift_registration",
	"variable_shift": "has_rotational_shift",
	"forbidden_shift_days": "variable_shift",
	"employee_shift_duty_roles": "forbidden_shift_days",
	# Tab 5: Salary & Payment
	"salary_currency": "personal_details",
	"salary_mode": "salary_currency",
	"ctc": "salary_mode",
	"salary_cb": "ctc",
	"iran_payroll_section": "salary_cb",
	"daily_pay": "iran_payroll_section",
	"monthly_base_pay": "daily_pay",
	"base_pay": "monthly_base_pay",
	"employee_salary_type": "base_pay",
	"insurance_start_date": "employee_salary_type",
	"fixed_monthly_salary": "insurance_start_date",
	"employee_hourly_salary": "fixed_monthly_salary",
	"technical_bonus_daily": "employee_hourly_salary",
	"monthly_technical_bonus": "technical_bonus_daily",
	"technical_bonus": "monthly_technical_bonus",
	"supervision_allowance": "technical_bonus",
	"service_allowance_monthly": "supervision_allowance",
	"employee_seniority_daily_base": "service_allowance_monthly",
	"employee_seniority_monthly_base": "employee_seniority_daily_base",
	"housing_allowance": "employee_seniority_monthly_base",
	"grocery_allowance": "housing_allowance",
	"marriage_allowance": "grocery_allowance",
	"child_allowance_per_child": "marriage_allowance",
	"child_allowance": "child_allowance_per_child",
	"children_count": "child_allowance",
	"min_hourly_wage": "children_count",
	"overtime_rate": "min_hourly_wage",
	"absence_deduction": "overtime_rate",
	"total_receivable": "absence_deduction",
	"employer_insurance_share": "total_receivable",
	"employee_insurance_share": "employer_insurance_share",
	"unemployment_insurance_share": "employee_insurance_share",
	"organization_monthly_cost": "unemployment_insurance_share",
	"bank_details_section": "organization_monthly_cost",
	"bank_name": "bank_details_section",
	"column_break_heye": "bank_name",
	"bank_ac_no": "column_break_heye",
	"iban": "bank_ac_no",
	"has_imprest": "iban",
	"imprest_accounts": "has_imprest",
	# Tab 6: Personal
	"marital_status": "profile_tab",
	"blood_group": "marital_status",
	"health_insurance_section": "blood_group",
	"health_insurance_provider": "health_insurance_section",
	"health_insurance_no": "health_insurance_provider",
	"family_background": "health_insurance_no",
	"health_details": "family_background",
	"column_break6": "health_details",
	"national_id_details_section": "column_break6",
	"birth_certificate_number": "national_id_details_section",
	"birth_certificate_issue_date": "birth_certificate_number",
	"birth_certificate_issue_place": "birth_certificate_issue_date",
	"birth_certificate_column_break": "birth_certificate_issue_place",
	"birth_certificate_serial": "birth_certificate_column_break",
	"passport_details_section": "birth_certificate_serial",
	"passport_number": "passport_details_section",
	"date_of_issue": "passport_number",
	"valid_upto": "date_of_issue",
	"column_break_73": "valid_upto",
	"place_of_issue": "column_break_73",
	# Tab 7: Profile & History
	"bio": "employment_details",
	"educational_qualification": "bio",
	"education": "educational_qualification",
	"previous_work_experience": "education",
	"external_work_history": "previous_work_experience",
	"history_in_company": "external_work_history",
	"internal_work_history": "history_in_company",
	"development_planning_section": "internal_work_history",
	"active_idp": "development_planning_section",
	"latest_nine_box_assessment": "active_idp",
	"target_career_transition": "latest_nine_box_assessment",
	# Tab 8: Joining & Contract
	"job_applicant": "exit",
	"scheduled_confirmation_date": "job_applicant",
	"column_break_32": "scheduled_confirmation_date",
	"final_confirmation_date": "column_break_32",
	"contract_end_date": "final_confirmation_date",
	"col_break_22": "contract_end_date",
	"notice_number_of_days": "col_break_22",
	"date_of_retirement": "notice_number_of_days",
	# Tab 9: Exit & Connections
	"resignation_letter_date": "connections_tab",
	"relieving_date": "resignation_letter_date",
	"exit_interview_details": "relieving_date",
	"held_on": "exit_interview_details",
	"new_workplace": "held_on",
	"column_break_99": "new_workplace",
	"leave_encashed": "column_break_99",
	"encashment_date": "leave_encashed",
	"feedback_section": "encashment_date",
	"reason_for_leaving": "feedback_section",
	"column_break_104": "reason_for_leaving",
	"feedback": "column_break_104",
}

HIDDEN_FIELD_UPDATES = {
	"employee": 1,
	"employee_number": 1,
	"lft": 1,
	"rgt": 1,
	"old_parent": 1,
	"image": 1,
}


def execute():
	if not frappe.db.exists("DocType", "Employee"):
		return

	ensure_iran_custom_fields_exist()
	meta = frappe.get_meta("Employee")

	for fieldname, label in TAB_LABEL_UPDATES.items():
		_set_field_property(meta, fieldname, "label", label, "Data")

	for fieldname, insert_after in BLOCK_START_INSERT_AFTER.items():
		_set_insert_after(meta, fieldname, insert_after)

	for fieldname, insert_after in INSERT_AFTER_UPDATES.items():
		_set_insert_after(meta, fieldname, insert_after)

	for fieldname, hidden in HIDDEN_FIELD_UPDATES.items():
		_set_field_property(meta, fieldname, "hidden", hidden, "Check")

	frappe.clear_cache(doctype="Employee")


def ensure_iran_custom_fields_exist():
	for country in frappe.get_all("Company", pluck="country", distinct=True):
		if (country or "").strip().lower() in IRAN_COUNTRY_ALIASES:
			run_regional_setup(country)
			return


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
