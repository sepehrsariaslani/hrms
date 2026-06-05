import frappe


HR_GOALS = [
	{
		"goal_name": "تکمیل و به‌روزرسانی پرونده پرسنلی کارکنان",
		"kra": "انضباط و مسئولیت‌پذیری",
		"description": "ثبت و تکمیل اطلاعات پرسنلی، قراردادها و سوابق ضروری برای همه کارکنان فعال.",
	},
	{
		"goal_name": "اجرای منظم ارزیابی عملکرد فصلی کارکنان",
		"kra": "تحقق اهداف کمی",
		"description": "هماهنگی، پیگیری و نهایی‌سازی ارزیابی عملکرد کارکنان در چرخه جاری.",
	},
	{
		"goal_name": "کاهش نرخ تاخیر و غیبت غیرموجه",
		"kra": "کیفیت انجام کار",
		"description": "پایش گزارش‌های حضور و غیاب و اجرای اقدامات اصلاحی برای کاهش تاخیر و غیبت.",
	},
	{
		"goal_name": "برگزاری آموزش‌های الزامی منابع انسانی",
		"kra": "ارتقای مهارت و یادگیری",
		"description": "برنامه‌ریزی و اجرای آموزش‌های بدو ورود، انضباط کاری و الزامات ایمنی.",
	},
	{
		"goal_name": "بهبود ارتباط و هم‌افزایی میان واحدها",
		"kra": "همکاری تیمی",
		"description": "تقویت ارتباط بین سرپرستان و کارکنان برای حل سریع‌تر مسائل عملیاتی.",
	},
]


def execute():
	target_employees = get_hr_target_employees()
	if not target_employees:
		return

	for employee in target_employees:
		cycle = get_target_cycle(employee.get("company"))
		if not cycle:
			continue

		for row in HR_GOALS:
			if goal_exists(employee.get("name"), cycle.get("name"), row["goal_name"]):
				continue

			doc = frappe.new_doc("Goal")
			doc.employee = employee.get("name")
			doc.goal_name = row["goal_name"]
			doc.appraisal_cycle = cycle.get("name")
			doc.kra = row["kra"]
			doc.start_date = cycle.get("start_date")
			doc.end_date = cycle.get("end_date")
			doc.progress = 0
			doc.description = row["description"]
			doc.insert(ignore_permissions=True)


def get_hr_target_employees() -> list[dict]:
	has_role_filters = {
		"parenttype": "User",
		"role": ["in", ["HR Manager", "HR User"]],
	}
	hr_users = set(frappe.get_all("Has Role", filters=has_role_filters, pluck="parent"))
	hr_users.difference_update({"Administrator", "Guest"})

	filters = {"status": "Active"}
	or_filters = [
		{"designation": ["like", "%منابع%"]},
		{"designation": ["like", "%HR%"]},
		{"department": ["like", "%منابع%"]},
		{"department": ["like", "%HR%"]},
	]
	if hr_users:
		or_filters.append({"user_id": ["in", list(hr_users)]})

	employees = frappe.get_all(
		"Employee",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "company"],
		order_by="modified desc",
		limit=0,
	)

	unique_employees = {}
	for employee in employees:
		unique_employees[employee.get("name")] = employee

	return list(unique_employees.values())


def get_target_cycle(company: str | None):
	if not company:
		return None

	cycle = frappe.db.get_value(
		"Appraisal Cycle",
		{"company": company, "status": "In Progress"},
		["name", "start_date", "end_date"],
		as_dict=True,
	)
	if cycle:
		return cycle

	return frappe.db.get_value(
		"Appraisal Cycle",
		{"company": company, "status": "Not Started"},
		["name", "start_date", "end_date"],
		as_dict=True,
		order_by="start_date asc",
	)


def goal_exists(employee: str, appraisal_cycle: str, goal_name: str) -> bool:
	return bool(
		frappe.db.exists(
			"Goal",
			{
				"employee": employee,
				"appraisal_cycle": appraisal_cycle,
				"goal_name": goal_name,
				"docstatus": ["<", 2],
			},
		)
	)
