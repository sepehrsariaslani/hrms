import frappe
from frappe.utils import flt, getdate

from hrms.setup import delete_custom_fields


LEGACY_BREAK_FIELDS = [
	"attendance_break_settings",
	"deduct_morning_break",
	"morning_break_start",
	"morning_break_end",
	"col_break_1",
	"deduct_lunch_break",
	"lunch_break_start",
	"lunch_break_end",
	"sec_break_2",
	"deduct_afternoon_break",
	"afternoon_break_start",
	"afternoon_break_end",
	"col_break_2",
	"deduct_evening_break",
	"evening_break_start",
	"evening_break_end",
]

LEGACY_BREAK_CONFIG = [
	{
		"title": "Morning Break",
		"enabled_field": "deduct_morning_break",
		"start_field": "morning_break_start",
		"end_field": "morning_break_end",
		"default_start": "09:40:00",
		"default_end": "10:00:00",
	},
	{
		"title": "Lunch Break",
		"enabled_field": "deduct_lunch_break",
		"start_field": "lunch_break_start",
		"end_field": "lunch_break_end",
		"default_start": "13:00:00",
		"default_end": "14:00:00",
	},
	{
		"title": "Afternoon Break",
		"enabled_field": "deduct_afternoon_break",
		"start_field": "afternoon_break_start",
		"end_field": "afternoon_break_end",
		"default_start": "17:15:00",
		"default_end": "17:35:00",
	},
	{
		"title": "Evening Break",
		"enabled_field": "deduct_evening_break",
		"start_field": "evening_break_start",
		"end_field": "evening_break_end",
		"default_start": "20:40:00",
		"default_end": "21:00:00",
	},
]


def execute():
	if not frappe.db.exists("DocType", "Break Hours") or not frappe.db.exists("DocType", "Break Assignment"):
		return

	if not frappe.db.has_column("Employee", "deduct_morning_break"):
		delete_legacy_fields()
		return

	migrate_employee_break_data()
	delete_legacy_fields()



def migrate_employee_break_data():
	employee_fields = ["name", "status", "date_of_joining"] + [
		f for cfg in LEGACY_BREAK_CONFIG for f in (cfg["enabled_field"], cfg["start_field"], cfg["end_field"])
	]
	employees = frappe.get_all("Employee", fields=employee_fields)
	break_hours_cache = {}

	for employee in employees:
		employee_name = employee.get("name")
		if not employee_name:
			continue
		if employee.get("status") == "Inactive":
			continue

		assignment_start = employee.get("date_of_joining") or getdate()

		for cfg in LEGACY_BREAK_CONFIG:
			if not is_enabled(employee.get(cfg["enabled_field"])):
				continue

			start_time = normalize_time(employee.get(cfg["start_field"]) or cfg["default_start"])
			end_time = normalize_time(employee.get(cfg["end_field"]) or cfg["default_end"])
			window_hours = get_window_hours(start_time, end_time)
			if window_hours <= 0:
				continue

			deduction_hours = flt(window_hours, 4)
			cache_key = (start_time, end_time, deduction_hours)

			break_hours_name = break_hours_cache.get(cache_key)
			if not break_hours_name:
				break_hours_name = get_or_create_break_hours(cfg["title"], start_time, end_time, deduction_hours)
				break_hours_cache[cache_key] = break_hours_name

			if not has_active_assignment(employee_name, break_hours_name):
				create_break_assignment(employee_name, break_hours_name, assignment_start)



def is_enabled(value) -> bool:
	return value in (None, 1, "1", True)



def normalize_time(value) -> str:
	time_text = str(value or "").strip()
	if not time_text:
		return "00:00:00"

	if "." in time_text:
		time_text = time_text.split(".", 1)[0]

	parts = time_text.split(":")
	if len(parts) == 2:
		return f"{int(parts[0]):02d}:{int(parts[1]):02d}:00"
	if len(parts) >= 3:
		return f"{int(parts[0]):02d}:{int(parts[1]):02d}:{int(parts[2]):02d}"

	return "00:00:00"



def get_window_hours(start_time: str, end_time: str) -> float:
	start_seconds = seconds_from_hms(start_time)
	end_seconds = seconds_from_hms(end_time)
	if end_seconds == start_seconds:
		return 0
	if end_seconds < start_seconds:
		end_seconds += 24 * 3600
	return flt((end_seconds - start_seconds) / 3600, 4)



def seconds_from_hms(value: str) -> int:
	parts = value.split(":")
	if len(parts) < 2:
		return 0

	hours = int(parts[0] or 0)
	minutes = int(parts[1] or 0)
	seconds = int(parts[2] or 0) if len(parts) > 2 else 0
	return (hours * 3600) + (minutes * 60) + seconds



def get_or_create_break_hours(title: str, break_start: str, break_end: str, deduction_hours: float) -> str:
	existing = frappe.db.get_value(
		"Break Hours",
		{
			"break_start": break_start,
			"break_end": break_end,
			"deduction_hours": deduction_hours,
			"is_active": 1,
		},
		"name",
	)
	if existing:
		return existing

	base_label = f"{title} {break_start[:5]}-{break_end[:5]} ({deduction_hours:g}h)"
	break_name = base_label
	counter = 2
	while frappe.db.exists("Break Hours", {"break_name": break_name}):
		break_name = f"{base_label} #{counter}"
		counter += 1

	doc = frappe.get_doc(
		{
			"doctype": "Break Hours",
			"break_name": break_name,
			"break_start": break_start,
			"break_end": break_end,
			"deduction_hours": deduction_hours,
			"is_active": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name



def has_active_assignment(employee: str, break_hours: str) -> bool:
	return bool(
		frappe.db.exists(
			"Break Assignment",
			{
				"employee": employee,
				"break_hours": break_hours,
				"docstatus": 1,
				"status": "Active",
			},
		)
	)



def create_break_assignment(employee: str, break_hours: str, from_date):
	doc = frappe.get_doc(
		{
			"doctype": "Break Assignment",
			"naming_series": "HR-BRA-.YYYY.-",
			"employee": employee,
			"break_hours": break_hours,
			"status": "Active",
			"from_date": from_date,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()



def delete_legacy_fields():
	delete_custom_fields(
		{
			"Employee": [{"fieldname": fieldname} for fieldname in LEGACY_BREAK_FIELDS],
		}
	)
