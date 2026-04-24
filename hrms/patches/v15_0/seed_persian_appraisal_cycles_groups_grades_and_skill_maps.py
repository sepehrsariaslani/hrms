import frappe
from frappe.utils import getdate, today


MANAGER_TEMPLATE = [
	"رهبری تیم",
	"تصمیم گیری مدیریتی",
	"برنامه ریزی عملیاتی",
	"حل مسئله",
	"ارتباط سازمانی",
]

COOK_TEMPLATE = [
	"آماده سازی غذا",
	"بهداشت و ایمنی مواد غذایی",
	"کنترل موجودی مواد اولیه",
	"برنامه ریزی پخت",
	"کنترل کیفیت غذا",
]

BAR_TEMPLATE = [
	"آماده سازی نوشیدنی",
	"خدمات مشتری",
	"نظم محیط کار",
	"کار تیمی",
]

CASHIER_TEMPLATE = [
	"کار با صندوق فروشگاهی",
	"ثبت دقیق تراکنش",
	"خدمات مشتری",
	"انضباط مالی",
]

ICECREAM_TEMPLATE = [
	"آماده سازی بستنی و دسر",
	"کنترل کیفیت محصول",
	"خدمات مشتری",
	"نگهداری مواد اولیه",
]

GENERAL_TEMPLATE = [
	"کار تیمی",
	"ارتباط موثر",
	"نظم و مسئولیت پذیری",
	"خدمات مشتری",
]

OPERATION_KEYWORDS = ["آشپز", "بار", "صندوق", "بستنی", "cook", "cashier", "barista"]
MANAGER_KEYWORDS = ["مدیر", "رئیس", "معاون", "manager", "director", "head", "chief"]

APPRAISAL_SEASONS = [
	("بهار", (3, 21), (6, 20)),
	("تابستان", (6, 21), (9, 22)),
	("پاییز", (9, 23), (12, 20)),
	("زمستان", (12, 21), (3, 20)),
]


def execute():
	ensure_employee_grades()
	ensure_skills()
	ensure_employee_groups()
	ensure_appraisal_cycles()
	ensure_employee_skill_maps()


def ensure_employee_grades():
	grades = [
		"G1 - کارآموز",
		"G2 - کارمند",
		"G3 - کارشناس",
		"G4 - ارشد",
		"G5 - سرپرست",
		"G6 - مدیر",
	]

	for grade_name in grades:
		if frappe.db.exists("Employee Grade", grade_name):
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Employee Grade",
				"name": grade_name,
			}
		)
		doc.insert(ignore_permissions=True)


def ensure_skills():
	skills = {
		"رهبری تیم": "توان هدایت تیم و پیگیری هدف های عملیاتی",
		"تصمیم گیری مدیریتی": "توان تحلیل شرایط و اتخاذ تصمیم موثر",
		"برنامه ریزی عملیاتی": "توان زمان بندی و اجرای برنامه های کاری",
		"حل مسئله": "توان تحلیل مسئله و ارائه راه حل قابل اجرا",
		"ارتباط سازمانی": "تعامل موثر با کارکنان و مدیریت",
		"آماده سازی غذا": "توان آماده سازی و اجرای دستور پخت استاندارد",
		"بهداشت و ایمنی مواد غذایی": "رعایت اصول بهداشت فردی و ایمنی مواد غذایی",
		"کنترل موجودی مواد اولیه": "بررسی موجودی و اعلام کسری به موقع",
		"برنامه ریزی پخت": "هماهنگی پخت بر اساس تعداد سفارش و برنامه روز",
		"کنترل کیفیت غذا": "کنترل طعم، ظاهر و کیفیت نهایی غذا",
		"آماده سازی نوشیدنی": "آماده سازی انواع نوشیدنی گرم و سرد",
		"خدمات مشتری": "برخورد حرفه ای و پاسخ گویی مناسب به مشتری",
		"نظم محیط کار": "حفظ نظم، پاکیزگی و چیدمان صحیح محیط",
		"کار با صندوق فروشگاهی": "ثبت سفارش و دریافت پرداخت با دقت",
		"ثبت دقیق تراکنش": "ثبت صحیح مبالغ و مغایرت گیری روزانه",
		"انضباط مالی": "رعایت دستورالعمل های مالی و امانت داری",
		"آماده سازی بستنی و دسر": "آماده سازی و سرو بستنی و دسر استاندارد",
		"کنترل کیفیت محصول": "کنترل کیفیت و انطباق محصول با دستورالعمل",
		"نگهداری مواد اولیه": "نگهداری صحیح مواد اولیه در شرایط استاندارد",
		"کار تیمی": "همکاری موثر با همکاران برای رسیدن به خروجی بهتر",
		"ارتباط موثر": "انتقال روشن اطلاعات و تعامل سازنده",
		"نظم و مسئولیت پذیری": "انجام به موقع وظایف با دقت و تعهد",
	}

	for skill_name, description in skills.items():
		if frappe.db.exists("Skill", skill_name):
			continue

		doc = frappe.new_doc("Skill")
		doc.skill_name = skill_name
		doc.description = description
		doc.insert(ignore_permissions=True)


def ensure_employee_groups():
	if not frappe.db.exists("DocType", "Employee Group"):
		return

	companies = frappe.get_all("Company", pluck="name")
	for company in companies:
		employees = frappe.get_all(
			"Employee",
			filters={"status": "Active", "company": company},
			fields=["name", "designation"],
			order_by="name asc",
			limit=0,
		)
		if not employees:
			continue

		groups = {
			f"مدیریت و سرپرستی - {company}": [],
			f"عملیات شعبه - {company}": [],
			f"عمومی و پشتیبانی - {company}": [],
		}

		for employee in employees:
			designation = get_primary_designation(employee.name, employee.designation)
			bucket = get_group_bucket(designation)
			groups[bucket.format(company=company)].append(employee.name)

		for group_name, employee_names in groups.items():
			if not employee_names:
				continue
			upsert_employee_group(group_name, employee_names)


def get_group_bucket(designation: str) -> str:
	value = (designation or "").strip().lower()
	if any(keyword in value for keyword in MANAGER_KEYWORDS):
		return "مدیریت و سرپرستی - {company}"
	if any(keyword in value for keyword in OPERATION_KEYWORDS):
		return "عملیات شعبه - {company}"
	return "عمومی و پشتیبانی - {company}"


def upsert_employee_group(group_name: str, employee_names: list[str]):
	if frappe.db.exists("Employee Group", group_name):
		doc = frappe.get_doc("Employee Group", group_name)
	else:
		doc = frappe.new_doc("Employee Group")
		doc.employee_group_name = group_name

	doc.employee_list = []
	for employee_name in sorted(set(employee_names)):
		doc.append("employee_list", {"employee": employee_name})

	doc.flags.ignore_permissions = True
	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)


def ensure_appraisal_cycles():
	companies = frappe.get_all("Company", pluck="name")
	if not companies:
		return

	today_date = getdate(today())
	year = today_date.year

	for company in companies:
		for season_name, start_tuple, end_tuple in APPRAISAL_SEASONS:
			start_year = year
			end_year = year
			if season_name == "زمستان":
				end_year = year + 1

			start_date = getdate(f"{start_year}-{start_tuple[0]:02d}-{start_tuple[1]:02d}")
			end_date = getdate(f"{end_year}-{end_tuple[0]:02d}-{end_tuple[1]:02d}")

			cycle_name = f"چرخه ارزیابی {season_name} {year} - {company}"
			if frappe.db.exists("Appraisal Cycle", cycle_name):
				continue

			doc = frappe.new_doc("Appraisal Cycle")
			doc.cycle_name = cycle_name
			doc.company = company
			doc.start_date = start_date
			doc.end_date = end_date
			doc.description = f"ارزیابی عملکرد {season_name} {year} برای شرکت {company}"
			doc.kra_evaluation_method = "Manual Rating"
			doc.insert(ignore_permissions=True)

			frappe.db.set_value(
				"Appraisal Cycle",
				cycle_name,
				"status",
				get_cycle_status(today_date, start_date, end_date),
				update_modified=False,
			)


def get_cycle_status(today_date, start_date, end_date) -> str:
	if today_date < start_date:
		return "Not Started"
	if today_date > end_date:
		return "Completed"
	return "In Progress"


def ensure_employee_skill_maps():
	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "designation"],
		order_by="name asc",
		limit=0,
	)

	for employee in employees:
		if frappe.db.exists("Employee Skill Map", {"employee": employee.name}):
			continue

		designation = get_primary_designation(employee.name, employee.designation)
		skill_names = get_skill_template_for_designation(designation)
		if not skill_names:
			continue

		doc = frappe.new_doc("Employee Skill Map")
		doc.employee = employee.name

		for idx, skill_name in enumerate(skill_names):
			if not frappe.db.exists("Skill", skill_name):
				continue
			doc.append(
				"employee_skills",
				{
					"skill": skill_name,
					"proficiency": get_initial_proficiency(designation, idx),
					"evaluation_date": today(),
				},
			)

		if not doc.employee_skills:
			continue

		doc.insert(ignore_permissions=True)


def get_initial_proficiency(designation: str, index: int) -> int:
	value = (designation or "").lower()
	if any(keyword in value for keyword in MANAGER_KEYWORDS):
		return 4 if index < 2 else 3
	if any(keyword in value for keyword in OPERATION_KEYWORDS):
		return 4 if index == 0 else 3
	return 3


def get_skill_template_for_designation(designation: str) -> list[str]:
	value = (designation or "").strip().lower()

	if any(keyword in value for keyword in MANAGER_KEYWORDS):
		return MANAGER_TEMPLATE

	if "آشپز" in value or "cook" in value or "chef" in value:
		return COOK_TEMPLATE
	if "بار" in value or "bar" in value:
		return BAR_TEMPLATE
	if "صندوق" in value or "cashier" in value:
		return CASHIER_TEMPLATE
	if "بستنی" in value or "ice" in value:
		return ICECREAM_TEMPLATE

	return GENERAL_TEMPLATE


def get_primary_designation(employee_name: str, fallback_designation: str | None = None) -> str:
	if frappe.db.exists("DocType", "Employee Designation Assignment"):
		primary = frappe.db.get_value(
			"Employee Designation Assignment",
			{
				"parent": employee_name,
				"parenttype": "Employee",
				"parentfield": "employee_designations",
				"is_primary": 1,
			},
			"designation",
		)
		if primary:
			return primary

		first_row = frappe.db.get_value(
			"Employee Designation Assignment",
			{
				"parent": employee_name,
				"parenttype": "Employee",
				"parentfield": "employee_designations",
			},
			"designation",
		)
		if first_row:
			return first_row

	return fallback_designation or ""
