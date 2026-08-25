import frappe
from frappe.utils import flt, getdate


def upsert_fa_translation(source_text, translated_text):
	existing = frappe.db.get_value(
		"Translation",
		{"language": "fa", "source_text": source_text},
		"name",
	)

	if existing:
		frappe.db.set_value("Translation", existing, "translated_text", translated_text, update_modified=False)
		return existing

	doc = frappe.new_doc("Translation")
	doc.language = "fa"
	doc.source_text = source_text
	doc.translated_text = translated_text
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def setup_employment_contract_translations():
	upsert_fa_translation("Employment Contract", "قرارداد کار")
	upsert_fa_translation("Employment Contract Settings", "تنظیم قرارداد کار")
	frappe.clear_cache()
	return {"ok": True}


@frappe.whitelist()
def get_contract_settings_defaults():
	if not frappe.db.exists("DocType", "Employment Contract Settings"):
		return {}

	settings = frappe.get_single("Employment Contract Settings")
	workplaces = [{"branch": row.branch} for row in (settings.workplaces or []) if row.branch]
	return {
		"employer_name": settings.employer_name,
		"employer_company_name": settings.employer_company_name,
		"employer_representative": settings.employer_representative,
		"employer_phone": settings.employer_phone,
		"employer_address": settings.employer_address,
		"default_contract_type": settings.default_contract_type,
		"default_work_hours_per_week": settings.default_work_hours_per_week,
		"default_job_title": settings.default_job_title,
		"default_workplace_details": settings.default_workplace_details,
		"employee_payment_bank": settings.employee_payment_bank,
		"employer_bank_name": settings.employer_bank_name,
		"employer_bank_account": settings.employer_bank_account,
		"employer_iban": settings.employer_iban,
		"letterhead_title": settings.letterhead_title,
		"workplaces": workplaces,
	}


@frappe.whitelist()
def get_employee_contract_defaults(employee, start_date=None):
	if not employee:
		return {}

	meta = frappe.get_meta("Employee")

	employee_core = frappe.db.get_value(
		"Employee",
		employee,
		[
			"employee_name",
			"company",
			"designation",
			"department",
			"branch",
			"cell_number",
			"current_address",
			"bank_name",
			"bank_ac_no",
			"iban",
		],
		as_dict=True,
	) or {}

	def pick_first_value(candidates):
		for fieldname in candidates:
			if meta.has_field(fieldname):
				value = frappe.db.get_value("Employee", employee, fieldname)
				if value:
					return value
		return ""

	national_id = pick_first_value(
		["custom_national_id_code", "national_id", "national_code", "national_identification_number"]
	)
	id_number = pick_first_value(["birth_certificate_number", "id_number", "shenasname_number", "identity_number"])
	id_issue_place = pick_first_value(["birth_certificate_issue_place"])
	father_name = pick_first_value(["custom_father_name", "father_name", "fathers_name"])

	salary_info = _get_latest_salary_assignment(employee, start_date)
	payroll_components = _build_payroll_components(employee)

	return {
		"employee": employee,
		"employee_name": employee_core.get("employee_name"),
		"company": employee_core.get("company"),
		"designation": employee_core.get("designation"),
		"department": employee_core.get("department"),
		"branch": employee_core.get("branch"),
		"employee_phone": employee_core.get("cell_number"),
		"employee_address": employee_core.get("current_address"),
		"national_id": national_id,
		"id_number": id_number,
		"id_issue_place": id_issue_place,
		"father_name": father_name,
		"employee_bank_name": employee_core.get("bank_name"),
		"employee_bank_account": employee_core.get("bank_ac_no"),
		"employee_iban": employee_core.get("iban"),
		"salary_structure_assignment": salary_info.get("name"),
		"base_salary": salary_info.get("base_salary", 0),
		"variable_salary": salary_info.get("variable_salary", 0),
		"monthly_salary": salary_info.get("monthly_salary", 0),
		"salary_currency": salary_info.get("salary_currency"),
		"payroll_components": payroll_components,
	}


def _get_latest_salary_assignment(employee, start_date=None):
	filters = {
		"employee": employee,
		"docstatus": ["!=", 2],
	}

	if start_date:
		filters["from_date"] = ["<=", getdate(start_date)]

	rows = frappe.get_all(
		"Salary Structure Assignment",
		filters=filters,
		fields=["name", "base", "variable", "salary_structure", "currency", "from_date"],
		order_by="from_date desc, creation desc",
		limit_page_length=1,
	)

	if not rows and start_date:
		rows = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": employee, "docstatus": ["!=", 2]},
			fields=["name", "base", "variable", "salary_structure", "currency", "from_date"],
			order_by="from_date desc, creation desc",
			limit_page_length=1,
		)

	if not rows:
		return {}

	row = rows[0]
	salary_currency = row.get("currency")
	if not salary_currency and row.get("salary_structure"):
		salary_currency = frappe.db.get_value("Salary Structure", row.get("salary_structure"), "currency")

	base_salary = flt(row.get("base"))
	variable_salary = flt(row.get("variable"))

	return {
		"name": row.get("name"),
		"base_salary": base_salary,
		"variable_salary": variable_salary,
		"monthly_salary": base_salary + variable_salary,
		"salary_currency": salary_currency,
	}


def _build_payroll_components(employee):
	meta = frappe.get_meta("Employee")

	def has_field(fieldname):
		return bool(fieldname and meta.has_field(fieldname))

	def get_value(fieldname):
		if not has_field(fieldname):
			return None
		return flt(frappe.db.get_value("Employee", employee, fieldname) or 0)

	def get_first_value(candidates):
		for candidate in candidates:
			if has_field(candidate):
				return get_value(candidate)
		return None

	def build_fixed_monthly_row(label, monthly_field):
		monthly_amount = get_value(monthly_field)
		if monthly_amount is None:
			return None

		return {
			"label": label,
			"amount_31_days": flt(monthly_amount),
			"amount_30_days": flt(monthly_amount),
			"remarks": "",
		}

	def build_scaled_monthly_row(label, monthly_field):
		monthly_amount = get_value(monthly_field)
		if monthly_amount is None:
			return None
		amount_30 = flt(monthly_amount)
		amount_31 = flt((amount_30 / 30) * 31)
		return {
			"label": label,
			"amount_31_days": amount_31,
			"amount_30_days": amount_30,
			"remarks": "",
		}

	component_rows = [
		build_fixed_monthly_row("حق مسکن", "housing_allowance"),
		build_fixed_monthly_row("بن خواربار", "grocery_allowance"),
		build_scaled_monthly_row("پایه سنوات ماهانه", "employee_seniority_monthly_base"),
		build_scaled_monthly_row("حقوق پایه ماهانه", "monthly_base_pay"),
		build_fixed_monthly_row("حق تاهل", "marriage_allowance"),
		build_fixed_monthly_row("حق اولاد", "child_allowance"),
	]

	rows = []
	for row in component_rows:
		if row:
			rows.append(row)

	return rows
