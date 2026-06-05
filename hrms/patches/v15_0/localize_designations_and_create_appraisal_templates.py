import frappe
from frappe.model.rename_doc import rename_doc


DESIGNATION_TRANSLATIONS = {
	"Accountant": "حسابدار",
	"Administrative Assistant": "دستیار اداری",
	"Administrative Officer": "کارشناس اداری",
	"Analyst": "تحلیلگر",
	"Associate": "همکار",
	"Business Analyst": "تحلیلگر کسب‌وکار",
	"Business Development Manager": "مدیر توسعه کسب‌وکار",
	"Consultant": "مشاور",
	"Chief Executive Officer": "مدیرعامل",
	"Chief Financial Officer": "مدیر مالی",
	"Chief Operating Officer": "مدیر عملیات",
	"Chief Technology Officer": "مدیر فناوری",
	"Customer Service Representative": "کارشناس خدمات مشتریان",
	"Designer": "طراح",
	"Engineer": "مهندس",
	"Executive Assistant": "دستیار اجرایی",
	"Finance Manager": "مدیر مالی",
	"HR Manager": "مدیر منابع انسانی",
	"Head of Marketing and Sales": "مدیر ارشد بازاریابی و فروش",
	"Manager": "مدیر",
	"Managing Director": "مدیر اجرایی",
	"Marketing Manager": "مدیر بازاریابی",
	"Marketing Specialist": "کارشناس بازاریابی",
	"President": "رئیس",
	"Product Manager": "مدیر محصول",
	"Project Manager": "مدیر پروژه",
	"Researcher": "پژوهشگر",
	"Sales Representative": "کارشناس فروش",
	"Secretary": "منشی",
	"Software Developer": "توسعه‌دهنده نرم‌افزار",
	"Vice President": "معاون",
}

MANAGER_TEMPLATE = "الگوی ارزیابی نقش‌های مدیریتی"
SPECIALIST_TEMPLATE = "الگوی ارزیابی نقش‌های کارشناسی"
OPERATION_TEMPLATE = "الگوی ارزیابی نقش‌های عملیاتی"


def execute():
	translate_designations()
	ensure_appraisal_master_data()
	create_or_update_templates()
	assign_templates_to_designations()


def translate_designations():
	for source_name, target_name in DESIGNATION_TRANSLATIONS.items():
		if not frappe.db.exists("Designation", source_name):
			continue

		if source_name == target_name:
			continue

		if frappe.db.exists("Designation", target_name):
			rename_doc("Designation", source_name, target_name, merge=True, force=True)
		else:
			rename_doc("Designation", source_name, target_name, force=True)


def ensure_appraisal_master_data():
	kras = [
		("تحقق اهداف کمی", "میزان تحقق اهداف عملیاتی و عددی تعریف‌شده"),
		("کیفیت انجام کار", "دقت، کیفیت خروجی و رعایت استانداردها"),
		("انضباط و مسئولیت‌پذیری", "حضور به‌موقع، پیگیری و پاسخگویی"),
		("همکاری تیمی", "تعامل موثر با همکاران و روحیه همکاری"),
		("ارتقای مهارت و یادگیری", "توسعه دانش و مهارت‌های شغلی"),
	]
	for title, description in kras:
		if frappe.db.exists("KRA", title):
			continue
		doc = frappe.new_doc("KRA")
		doc.title = title
		doc.description = description
		doc.insert(ignore_permissions=True)

	criteria = [
		"تعهد سازمانی",
		"مهارت ارتباطی",
		"حل مسئله",
		"رعایت فرآیندها",
		"رضایت ذی‌نفعان",
	]
	for criteria_name in criteria:
		if frappe.db.exists("Employee Feedback Criteria", criteria_name):
			continue
		doc = frappe.new_doc("Employee Feedback Criteria")
		doc.criteria = criteria_name
		doc.insert(ignore_permissions=True)


def create_or_update_templates():
	manager_goals = [
		("تحقق اهداف کمی", 30),
		("کیفیت انجام کار", 20),
		("انضباط و مسئولیت‌پذیری", 15),
		("همکاری تیمی", 15),
		("ارتقای مهارت و یادگیری", 20),
	]
	specialist_goals = [
		("تحقق اهداف کمی", 25),
		("کیفیت انجام کار", 30),
		("انضباط و مسئولیت‌پذیری", 20),
		("همکاری تیمی", 15),
		("ارتقای مهارت و یادگیری", 10),
	]
	operation_goals = [
		("تحقق اهداف کمی", 20),
		("کیفیت انجام کار", 25),
		("انضباط و مسئولیت‌پذیری", 30),
		("همکاری تیمی", 20),
		("ارتقای مهارت و یادگیری", 5),
	]
	feedback_weights = [
		("تعهد سازمانی", 20),
		("مهارت ارتباطی", 20),
		("حل مسئله", 20),
		("رعایت فرآیندها", 20),
		("رضایت ذی‌نفعان", 20),
	]

	upsert_appraisal_template(
		MANAGER_TEMPLATE,
		"الگوی ارزیابی ویژه نقش‌های مدیریتی سازمان",
		manager_goals,
		feedback_weights,
	)
	upsert_appraisal_template(
		SPECIALIST_TEMPLATE,
		"الگوی ارزیابی ویژه نقش‌های کارشناسی و تخصصی",
		specialist_goals,
		feedback_weights,
	)
	upsert_appraisal_template(
		OPERATION_TEMPLATE,
		"الگوی ارزیابی ویژه نقش‌های اجرایی و عملیاتی",
		operation_goals,
		feedback_weights,
	)


def upsert_appraisal_template(template_title, description, goals, rating_criteria):
	if frappe.db.exists("Appraisal Template", template_title):
		doc = frappe.get_doc("Appraisal Template", template_title)
	else:
		doc = frappe.new_doc("Appraisal Template")
		doc.template_title = template_title

	doc.description = description
	doc.goals = []
	doc.rating_criteria = []

	for kra_title, weightage in goals:
		doc.append(
			"goals",
			{
				"key_result_area": kra_title,
				"per_weightage": weightage,
			},
		)

	for criteria_name, weightage in rating_criteria:
		doc.append(
			"rating_criteria",
			{
				"criteria": criteria_name,
				"per_weightage": weightage,
			},
		)

	doc.flags.ignore_permissions = True
	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)


def assign_templates_to_designations():
	designation_names = frappe.get_all("Designation", pluck="name")
	for designation_name in designation_names:
		template = get_template_for_designation(designation_name)
		if not template:
			continue
		frappe.db.set_value(
			"Designation",
			designation_name,
			"appraisal_template",
			template,
			update_modified=False,
		)


def get_template_for_designation(designation_name: str) -> str:
	name = (designation_name or "").strip().lower()

	manager_keywords = [
		"مدیر",
		"رئیس",
		"معاون",
		"chief",
		"manager",
		"president",
		"vice president",
		"director",
		"head",
	]
	operation_keywords = [
		"صندوق",
		"آشپز",
		"بار",
		"بستنی",
		"assistant",
		"officer",
		"secretary",
		"representative",
	]

	if any(keyword in name for keyword in manager_keywords):
		return MANAGER_TEMPLATE
	if any(keyword in name for keyword in operation_keywords):
		return OPERATION_TEMPLATE
	return SPECIALIST_TEMPLATE
