# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import annotations

from datetime import datetime, timedelta
import json
import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, get_date_str, get_time, getdate, now_datetime, nowdate

from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from hrms.hr.doctype.shift_assignment.shift_assignment import OverlappingShiftError

PLAN_STATUSES = ["Draft", "Submitted", "Approved", "Rejected", "Replaced", "Cancelled"]
HR_ROLES = {"HR Manager", "HR User", "System Manager"}
HOURS_PER_WORK_DAY = 8
DAY_NAME_TO_WEEKDAY = {
	"Monday": 0,
	"Tuesday": 1,
	"Wednesday": 2,
	"Thursday": 3,
	"Friday": 4,
	"Saturday": 5,
	"Sunday": 6,
}
WEEKDAY_TO_DAY_NAME = {value: key for key, value in DAY_NAME_TO_WEEKDAY.items()}
PERSIAN_DIGITS_TRANSLATION = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


class WeeklyShiftPlan(Document):
	def before_validate(self):
		self.normalize_week()
		self.set_default_approver()
		self.apply_slot_defaults()
		self.set_totals()
		if not self.status:
			self.status = "Draft"

	def validate(self):
		self.validate_status()
		self.validate_slot_dates()
		self.validate_duplicate_slots()
		self.validate_edit_permissions()

	def before_submit(self):
		self.validate_submission_rules()
		self.status = "Submitted"
		self.submitted_by_user = frappe.session.user

	def on_cancel(self):
		self.db_set("status", "Cancelled", update_modified=False)

	def normalize_week(self):
		self.week_start_date = get_week_start_date(self.week_start_date or nowdate())
		self.week_end_date = add_days(self.week_start_date, 6)

	def set_default_approver(self):
		if not self.employee:
			return

		if not self.company:
			self.company = frappe.db.get_value("Employee", self.employee, "company")

		if not self.approver:
			self.approver = get_employee_shift_request_approver(self.employee) or frappe.session.user

		current_employee = get_employee_for_user(frappe.session.user)
		self.planned_for_by_allocator = 1 if current_employee and current_employee != self.employee else 0

	def apply_slot_defaults(self):
		auto_role = get_default_duty_role_for_employee(self.employee)

		shift_cache = {}
		for slot in self.slot_details or []:
			if not slot.slot_code and not slot.shift_type:
				continue

			if not slot.shift_type and slot.slot_code:
				slot.shift_type = get_shift_type_for_slot(slot.slot_code)

			if slot.shift_type and slot.shift_type not in shift_cache:
				shift_cache[slot.shift_type] = frappe.db.get_value(
					"Shift Type",
					slot.shift_type,
					["start_time", "end_time"],
					as_dict=True,
				)

			shift_info = shift_cache.get(slot.shift_type) or {}
			if slot.shift_type and not shift_info:
				frappe.throw(_("Shift Type {0} does not exist.").format(frappe.bold(slot.shift_type)))

			if slot.shift_type and not slot.start_time:
				slot.start_time = shift_info.start_time
			if slot.shift_type and not slot.end_time:
				slot.end_time = shift_info.end_time

			if not slot.duty_role:
				slot.duty_role = auto_role

			slot.hours = calculate_slot_hours(slot.start_time, slot.end_time)

	def set_totals(self):
		valid_dates = {slot.work_date for slot in (self.slot_details or []) if slot.work_date}
		self.total_days = len(valid_dates)
		self.total_hours = round(sum(flt(slot.hours) for slot in (self.slot_details or [])), 2)

	def validate_status(self):
		if self.status and self.status not in PLAN_STATUSES:
			frappe.throw(_("Invalid status {0}").format(frappe.bold(self.status)))

	def validate_slot_dates(self):
		if not self.week_start_date or not self.week_end_date:
			return

		start = getdate(self.week_start_date)
		end = getdate(self.week_end_date)
		for slot in self.slot_details or []:
			if not slot.work_date:
				continue

			date = getdate(slot.work_date)
			if date < start or date > end:
				frappe.throw(
					_("Row #{0}: Work Date must be inside this week.").format(slot.idx),
					title=_("Invalid Slot Date"),
				)

	def validate_duplicate_slots(self):
		seen = set()
		for slot in self.slot_details or []:
			if not (slot.work_date and slot.slot_code):
				continue

			key = (get_date_str(slot.work_date), slot.slot_code)
			if key in seen:
				frappe.throw(
					_("Row #{0}: Duplicate slot for {1} - {2}.").format(
						slot.idx,
						frappe.bold(get_date_str(slot.work_date)),
						frappe.bold(slot.slot_code),
					),
					title=_("Duplicate Slot"),
				)
			seen.add(key)

	def validate_edit_permissions(self):
		if (
			self.docstatus == 1
			and self._action != "submit"
			and not self.flags.ignore_validate_update_after_submit
		):
			frappe.throw(_("Submitted plans can only be updated via approval actions."))

		if self.docstatus == 0 and self.employee and not can_manage_employee(frappe.session.user, self.employee):
			frappe.throw(_("You are not allowed to create or edit this plan."), frappe.PermissionError)

	def validate_submission_rules(self):
		rules = get_dynamic_planner_rules(self.employee, self.week_start_date)
		required_days = int(rules["required_days_per_week"])
		minimum_hours = flt(rules["minimum_hours_per_week"])
		auto_role = get_default_duty_role_for_employee(self.employee)
		forbidden_weekdays = get_employee_forbidden_weekdays(self.employee)

		valid_slots = [
			slot
			for slot in (self.slot_details or [])
			if slot.work_date and slot.shift_type and slot.duty_role
		]
		unique_days = {get_date_str(slot.work_date) for slot in valid_slots}
		total_hours = sum(flt(slot.hours) for slot in valid_slots)

		if len(unique_days) != required_days:
			frappe.throw(
				_("Weekly plan must include exactly {0} working days.").format(frappe.bold(required_days))
			)

		if total_hours < minimum_hours:
			frappe.throw(
				_("Weekly plan must include at least {0} work hours.").format(frappe.bold(minimum_hours))
			)

		for slot in self.slot_details or []:
			if not slot.work_date:
				frappe.throw(_("Row #{0}: Work Date is mandatory.").format(slot.idx))
			if getdate(slot.work_date).weekday() in forbidden_weekdays:
				day_name = WEEKDAY_TO_DAY_NAME.get(getdate(slot.work_date).weekday(), "")
				frappe.throw(
					_("Row #{0}: Work Date is in employee forbidden days ({1}).").format(slot.idx, day_name)
				)
			if not slot.slot_code:
				frappe.throw(_("Row #{0}: Slot is mandatory.").format(slot.idx))
			if not slot.shift_type:
				frappe.throw(_("Row #{0}: Shift Type is mandatory.").format(slot.idx))
			if not slot.duty_role:
				slot.duty_role = auto_role
			if not slot.duty_role:
				frappe.throw(
					_(
						"Row #{0}: Employee designation must be set before submitting weekly shift plan."
					).format(slot.idx)
				)
			if not slot.start_time or not slot.end_time:
				frappe.throw(_("Row #{0}: Start/End Time is mandatory.").format(slot.idx))


# API
@frappe.whitelist()
def get_weekly_shift_context(
	target_date: str | None = None,
	week_start_date: str | None = None,
	employee: str | None = None,
) -> dict:
	user = frappe.session.user
	current_employee = get_employee_for_user(user)
	if not current_employee:
		frappe.throw(_("You are not linked to an active employee."))

	week_start = get_week_start_date(week_start_date or target_date or nowdate())
	week_end = add_days(week_start, 6)
	target_employee = employee or current_employee

	if not can_manage_employee(user, target_employee) and not can_view_team(user, target_employee):
		frappe.throw(_("You are not allowed to access this employee's plan."), frappe.PermissionError)

	plan = frappe.get_all(
		"Weekly Shift Plan",
		filters={
			"employee": target_employee,
			"week_start_date": week_start,
			"docstatus": ("!=", 2),
		},
		fields=["name"],
		order_by="modified desc",
		limit=1,
	)

	plan_doc = frappe.get_doc("Weekly Shift Plan", plan[0].name) if plan else None
	employee_designation = frappe.db.get_value("Employee", target_employee, "designation")
	default_duty_role = get_default_duty_role_for_employee(target_employee)
	forbidden_weekdays = sorted(list(get_employee_forbidden_weekdays(target_employee)))
	employee_duty_roles = get_employee_duty_role_options(target_employee)

	return {
		"week_start_date": week_start,
		"week_end_date": week_end,
		"employee": target_employee,
		"current_employee": current_employee,
		"can_plan_for_others": is_shift_allocator(user) or is_hr_user(user),
		"manageable_employees": get_manageable_employees(user),
		"duty_roles": frappe.get_all(
			"Shift Duty Role",
			filters={"is_active": 1},
			fields=["name", "role_name"],
			order_by="role_name asc",
		),
		"slot_templates": get_slot_templates(),
		"plan": serialize_plan(plan_doc) if plan_doc else None,
		"rules": get_dynamic_planner_rules(target_employee, week_start),
		"employee_requires_shift_registration": is_shift_registration_required(target_employee),
		"employee_designation": employee_designation,
		"default_duty_role": default_duty_role,
		"forbidden_weekdays": forbidden_weekdays,
		"employee_duty_roles": employee_duty_roles,
	}


@frappe.whitelist()
def upsert_weekly_shift_plan(payload: str | dict | None = None) -> dict:
	data = parse_payload(payload)
	user = frappe.session.user
	current_employee = get_employee_for_user(user)
	if not current_employee:
		frappe.throw(_("You are not linked to an active employee."))

	plan_name = data.get("name")
	target_employee = data.get("employee") or current_employee
	week_start_date = get_week_start_date(data.get("week_start_date") or nowdate())
	slots = data.get("slots") or []

	if not can_manage_employee(user, target_employee):
		frappe.throw(_("You are not allowed to create or edit this plan."), frappe.PermissionError)

	if plan_name:
		doc = frappe.get_doc("Weekly Shift Plan", plan_name)
		if doc.docstatus != 0 or doc.status != "Draft":
			frappe.throw(_("Only draft plans can be edited."))
		if not can_manage_employee(user, doc.employee):
			frappe.throw(_("You are not allowed to edit this plan."), frappe.PermissionError)
	else:
		doc = frappe.new_doc("Weekly Shift Plan")

	doc.employee = target_employee
	doc.week_start_date = week_start_date
	doc.slot_details = []

	for slot in slots:
		doc.append(
			"slot_details",
			{
				"work_date": normalize_calendar_date(slot.get("work_date")),
				"slot_code": slot.get("slot_code"),
				"shift_type": slot.get("shift_type"),
				"start_time": slot.get("start_time"),
				"end_time": slot.get("end_time"),
				"duty_role": slot.get("duty_role"),
			},
		)

	doc.status = "Draft"
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	doc.add_comment(
		"Info",
		_("Plan saved as draft by {0}.").format(frappe.bold(frappe.session.user)),
	)
	return serialize_plan(doc)


@frappe.whitelist()
def submit_weekly_shift_plan(plan_name: str) -> dict:
	doc = frappe.get_doc("Weekly Shift Plan", plan_name)
	if doc.docstatus != 0:
		frappe.throw(_("Only draft plans can be submitted."))
	if not can_manage_employee(frappe.session.user, doc.employee):
		frappe.throw(_("You are not allowed to submit this plan."), frappe.PermissionError)

	doc.flags.ignore_permissions = True
	doc.submit()
	doc.add_comment("Info", _("Plan submitted for approval."))
	return serialize_plan(doc)


@frappe.whitelist()
def list_my_weekly_shift_plans(
	week_start_date: str | None = None,
	status: str | None = None,
) -> list[dict]:
	employee = get_employee_for_user(frappe.session.user)
	if not employee:
		return []

	filters: dict = {"employee": employee, "docstatus": ("!=", 2)}
	if week_start_date:
		filters["week_start_date"] = get_week_start_date(week_start_date)
	if status:
		filters["status"] = status

	return frappe.get_all(
		"Weekly Shift Plan",
		filters=filters,
		fields=[
			"name",
			"week_start_date",
			"week_end_date",
			"status",
			"total_days",
			"total_hours",
			"employee",
			"employee_name",
			"approver",
			"docstatus",
		],
		order_by="week_start_date desc, modified desc",
	)


@frappe.whitelist()
def list_team_weekly_shift_plans(
	week_start_date: str | None = None,
	status: str | None = None,
) -> list[dict]:
	user = frappe.session.user
	if not (is_hr_user(user) or is_shift_allocator(user) or has_shift_approver_team(user)):
		return []

	filters: dict = {"docstatus": ("!=", 2)}
	if week_start_date:
		filters["week_start_date"] = get_week_start_date(week_start_date)
	if status:
		filters["status"] = status

	if not is_hr_user(user):
		team = get_team_employee_ids_for_user(user)
		if not team:
			return []
		filters["employee"] = ["in", team]

	plan_names = frappe.get_all(
		"Weekly Shift Plan",
		filters=filters,
		pluck="name",
		order_by="employee_name asc, week_start_date desc",
	)

	return [serialize_plan(frappe.get_doc("Weekly Shift Plan", name)) for name in plan_names]


@frappe.whitelist()
def get_shift_allocator_team_overview(week_start_date: str | None = None) -> dict:
	user = frappe.session.user
	week_start = get_week_start_date(week_start_date or nowdate())

	if not (is_hr_user(user) or is_shift_allocator(user) or has_shift_approver_team(user)):
		return {"week_start_date": week_start, "employees": []}

	employee_filters: dict = {"status": "Active", "docstatus": ("<", 2)}
	has_shift_approver_field = has_shift_request_approver_field()
	if not is_hr_user(user):
		if not has_shift_approver_field:
			return {"week_start_date": week_start, "employees": []}
		employee_filters["shift_request_approver"] = user

	employee_fields = ["name", "employee_name", "designation", "department"]
	if has_shift_approver_field:
		employee_fields.append("shift_request_approver")
	for optional_field in ["has_rotational_shift", "needs_shift_registration", "forbidden_shift_days"]:
		if frappe.db.has_column("Employee", optional_field):
			employee_fields.append(optional_field)
	if frappe.db.has_column("Employee", "variable_shift"):
		employee_fields.append("variable_shift")

	employees = frappe.get_all(
		"Employee",
		filters=employee_filters,
		fields=employee_fields,
		order_by="employee_name asc",
	)
	employees = [employee for employee in employees if is_weekly_planning_employee(employee)]
	if not employees:
		return {"week_start_date": week_start, "employees": []}

	designation_color_map = {}
	designation_names = sorted(
		{employee.designation for employee in employees if employee.get("designation")}
	)
	if designation_names and frappe.db.has_column("Designation", "color"):
		for designation in frappe.get_all(
			"Designation",
			filters={"name": ["in", designation_names]},
			fields=["name", "color"],
		):
			designation_color_map[designation.name] = designation.color

	plan_names = frappe.get_all(
		"Weekly Shift Plan",
		filters={
			"employee": ["in", [employee.name for employee in employees]],
			"week_start_date": week_start,
			"docstatus": ("!=", 2),
		},
		fields=["name", "employee"],
		order_by="modified desc",
	)

	latest_plan_by_employee = {}
	for row in plan_names:
		latest_plan_by_employee.setdefault(row.employee, row.name)

	records = []
	for employee in employees:
		rules = get_dynamic_planner_rules(employee.name, week_start)
		plan_name = latest_plan_by_employee.get(employee.name)
		serialized_plan = serialize_plan(frappe.get_doc("Weekly Shift Plan", plan_name)) if plan_name else None
		records.append(
			{
				"name": employee.name,
				"employee_name": employee.employee_name,
				"designation": employee.designation,
				"designation_color": designation_color_map.get(employee.designation),
				"department": employee.department,
				"shift_request_approver": employee.get("shift_request_approver"),
				"has_rotational_shift": employee.get("has_rotational_shift"),
				"variable_shift": employee.get("variable_shift"),
				"needs_shift_registration": employee.get("needs_shift_registration"),
				"forbidden_shift_days": employee.get("forbidden_shift_days"),
				"forbidden_weekdays": sorted(list(get_employee_forbidden_weekdays(employee.name))),
				"available_duty_roles": get_employee_duty_role_options(employee.name),
				"default_duty_role": get_default_duty_role_for_employee(employee.name),
				"required_days_per_week": rules.get("required_days_per_week"),
				"minimum_hours_per_week": rules.get("minimum_hours_per_week"),
				"official_holidays_in_week": rules.get("official_holidays_in_week"),
				"plan": serialized_plan,
			}
		)

	return {"week_start_date": week_start, "employees": records}


@frappe.whitelist()
def approve_weekly_shift_plan(plan_name: str, note: str | None = None) -> dict:
	doc = frappe.get_doc("Weekly Shift Plan", plan_name)
	if doc.docstatus != 1:
		frappe.throw(_("Plan must be submitted before approval."))
	if doc.status not in ["Submitted", "Rejected"]:
		frappe.throw(_("Only submitted plans can be approved."))

	if not can_approve_plan(frappe.session.user, doc):
		frappe.throw(_("You are not allowed to approve this plan."), frappe.PermissionError)

	doc.flags.ignore_validate_update_after_submit = True
	doc.flags.ignore_permissions = True
	doc.status = "Approved"
	doc.approval_note = note or ""
	doc.rejection_reason = ""
	doc.approved_by = frappe.session.user
	doc.approved_on = now_datetime()
	doc.save(ignore_permissions=True)

	if doc.amended_from:
		frappe.db.set_value("Weekly Shift Plan", doc.amended_from, "status", "Replaced")

	doc.add_comment("Info", _("Plan approved as employee preference. Final allocation is required."))
	return serialize_plan(doc)


@frappe.whitelist()
def reject_weekly_shift_plan(plan_name: str, reason: str | None = None) -> dict:
	doc = frappe.get_doc("Weekly Shift Plan", plan_name)
	if doc.docstatus != 1:
		frappe.throw(_("Plan must be submitted before rejection."))
	if doc.status != "Submitted":
		frappe.throw(_("Only submitted plans can be rejected."))
	if not can_approve_plan(frappe.session.user, doc):
		frappe.throw(_("You are not allowed to reject this plan."), frappe.PermissionError)

	doc.flags.ignore_validate_update_after_submit = True
	doc.flags.ignore_permissions = True
	doc.status = "Rejected"
	doc.rejection_reason = reason or _("Rejected by approver")
	doc.approval_note = ""
	doc.approved_by = frappe.session.user
	doc.approved_on = now_datetime()
	doc.save(ignore_permissions=True)
	doc.add_comment("Info", _("Plan rejected."))
	return serialize_plan(doc)


@frappe.whitelist()
def create_weekly_shift_plan_amendment(source_plan_name: str) -> dict:
	source_doc = frappe.get_doc("Weekly Shift Plan", source_plan_name)
	if source_doc.docstatus != 1:
		frappe.throw(_("Only submitted plans can be amended."))
	if not can_manage_employee(frappe.session.user, source_doc.employee):
		frappe.throw(_("You are not allowed to create an amendment."), frappe.PermissionError)

	amendment = frappe.copy_doc(source_doc)
	amendment.docstatus = 0
	amendment.status = "Draft"
	amendment.submitted_by_user = ""
	amendment.approved_by = ""
	amendment.approved_on = None
	amendment.approval_note = ""
	amendment.rejection_reason = ""
	amendment.generated_assignments_count = 0
	amendment.amended_from = source_doc.name
	for slot in amendment.slot_details or []:
		slot.assignment = ""

	amendment.flags.ignore_permissions = True
	amendment.insert(ignore_permissions=True)
	amendment.add_comment("Info", _("Amendment created from {0}.").format(frappe.bold(source_doc.name)))
	return serialize_plan(amendment)


@frappe.whitelist()
def get_weekly_shift_slot_templates() -> list[dict]:
	return get_slot_templates()


# helpers

def parse_payload(payload: str | dict | None) -> dict:
	if not payload:
		return {}
	if isinstance(payload, dict):
		return payload
	if isinstance(payload, str):
		try:
			return json.loads(payload)
		except Exception:
			return {}
	return {}


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> tuple[int, int, int]:
	gy = 621 if jy <= 979 else 1600
	jy -= 0 if jy <= 979 else 979
	days = (
		365 * jy
		+ (jy // 33) * 8
		+ ((jy % 33 + 3) // 4)
		+ 78
		+ jd
		+ ((jm - 1) * 31 if jm < 7 else (jm - 7) * 30 + 186)
	)
	gy += 400 * (days // 146097)
	days %= 146097
	if days > 36524:
		days -= 1
		gy += 100 * (days // 36524)
		days %= 36524
		if days >= 365:
			days += 1
	gy += 4 * (days // 1461)
	days %= 1461
	if days > 365:
		gy += (days - 1) // 365
		days = (days - 1) % 365

	gd_m = [
		0,
		31,
		29 if (gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0 else 28,
		31,
		30,
		31,
		30,
		31,
		31,
		30,
		31,
		30,
		31,
	]
	gm = 0
	while gm < 13 and days >= gd_m[gm]:
		days -= gd_m[gm]
		gm += 1
	return gy, gm, days + 1


def normalize_calendar_date(value: str | None) -> str | None:
	if not value:
		return None

	text = str(value).strip().translate(PERSIAN_DIGITS_TRANSLATION)
	if "T" in text:
		text = text.split("T", 1)[0]
	if " " in text:
		text = text.split(" ", 1)[0]

	match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
	if not match:
		try:
			return get_date_str(getdate(text))
		except Exception:
			return None

	year, month, day = [int(part) for part in match.groups()]
	if year < 1700:
		year, month, day = jalali_to_gregorian(year, month, day)

	try:
		return get_date_str(getdate(f"{year:04d}-{month:02d}-{day:02d}"))
	except Exception:
		return None



def get_week_start_date(value: str) -> str:
	date = getdate(normalize_calendar_date(value) or value)
	offset = (date.weekday() - 5) % 7
	return get_date_str(add_days(date, -offset))



def calculate_slot_hours(start_time, end_time) -> float:
	if not start_time or not end_time:
		return 0.0

	start = get_time(start_time)
	end = get_time(end_time)
	start_dt = datetime.combine(getdate(nowdate()), start)
	end_dt = datetime.combine(getdate(nowdate()), end)
	if end_dt <= start_dt:
		end_dt += timedelta(days=1)
	return round((end_dt - start_dt).total_seconds() / 3600, 2)



def get_planner_settings() -> dict:
	defaults = {
		"required_days_per_week": 6,
		"minimum_hours_per_week": 48.0,
		"auto_generate_assignments": 1,
		"morning_shift_type": "",
		"evening_shift_type": "",
	}

	if not frappe.db.exists("DocType", "Weekly Shift Planner Settings"):
		return defaults

	try:
		values = frappe.db.get_singles_dict("Weekly Shift Planner Settings", cast=True)
	except Exception:
		return defaults

	defaults.update(
		{
			"required_days_per_week": values.get("required_days_per_week") or 6,
			"minimum_hours_per_week": values.get("minimum_hours_per_week") or 48.0,
			"auto_generate_assignments": values.get("auto_generate_assignments", 1),
			"morning_shift_type": values.get("morning_shift_type") or "",
			"evening_shift_type": values.get("evening_shift_type") or "",
		}
	)
	return defaults


def get_dynamic_planner_rules(employee: str | None, week_start_date: str | None) -> dict:
	settings = get_planner_settings()
	base_required_days = int(settings["required_days_per_week"] or 0)
	base_minimum_hours = flt(settings["minimum_hours_per_week"])
	official_holidays = count_official_holidays_in_week(employee, week_start_date)

	return {
		"base_required_days_per_week": base_required_days,
		"base_minimum_hours_per_week": base_minimum_hours,
		"required_days_per_week": max(0, base_required_days - official_holidays),
		"minimum_hours_per_week": max(0, base_minimum_hours - (official_holidays * HOURS_PER_WORK_DAY)),
		"official_holidays_in_week": official_holidays,
	}


def count_official_holidays_in_week(employee: str | None, week_start_date: str | None) -> int:
	if not employee or not week_start_date:
		return 0

	holiday_list = get_holiday_list_for_employee(employee, raise_exception=False)
	if not holiday_list:
		return 0

	week_start = get_week_start_date(week_start_date)
	filters = {
		"parent": holiday_list,
		"holiday_date": ["between", [week_start, add_days(week_start, 6)]],
	}
	if frappe.db.has_column("Holiday", "weekly_off"):
		filters["weekly_off"] = 0

	return frappe.db.count("Holiday", filters)



def get_slot_templates() -> list[dict]:
	settings = get_planner_settings()
	templates = [
		{"slot_code": "Morning", "shift_type": settings.get("morning_shift_type")},
		{"slot_code": "Evening", "shift_type": settings.get("evening_shift_type")},
	]
	for template in templates:
		shift_type = template.get("shift_type")
		if not shift_type:
			template.update({"start_time": None, "end_time": None})
			continue
		start_time, end_time = frappe.db.get_value("Shift Type", shift_type, ["start_time", "end_time"])
		template.update({"start_time": start_time, "end_time": end_time})
	return templates



def get_shift_type_for_slot(slot_code: str) -> str:
	settings = get_planner_settings()
	mapping = {
		"Morning": settings.get("morning_shift_type"),
		"Evening": settings.get("evening_shift_type"),
	}
	shift_type = mapping.get(slot_code)
	if not shift_type:
		frappe.throw(_("Please configure {0} Shift Type in Weekly Shift Planner Settings.").format(slot_code))
	return shift_type



def get_employee_for_user(user: str) -> str | None:
	return frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")



def is_hr_user(user: str) -> bool:
	return bool(HR_ROLES.intersection(set(frappe.get_roles(user))))



def has_shift_allocator_flag(user: str) -> bool:
	employee = get_employee_for_user(user)
	if not employee or not frappe.db.has_column("Employee", "is_shift_allocator"):
		return False
	return bool(frappe.db.get_value("Employee", employee, "is_shift_allocator"))



def is_shift_allocator(user: str) -> bool:
	return has_shift_allocator_flag(user)


def is_shift_registration_required(employee: str | None) -> bool:
	if not employee:
		return False

	columns = []
	if frappe.db.has_column("Employee", "needs_shift_registration"):
		columns.append("needs_shift_registration")
	if frappe.db.has_column("Employee", "has_rotational_shift"):
		columns.append("has_rotational_shift")
	if frappe.db.has_column("Employee", "variable_shift"):
		columns.append("variable_shift")
	if not columns:
		return False

	values = frappe.db.get_value("Employee", employee, columns, as_dict=True) or {}
	return bool(
		values.get("needs_shift_registration")
		or values.get("has_rotational_shift")
		or values.get("variable_shift")
	)


def is_weekly_planning_employee(employee_row: dict) -> bool:
	if not employee_row:
		return False

	flag_names = ["needs_shift_registration", "has_rotational_shift", "variable_shift"]
	existing_flag_names = [field for field in flag_names if field in employee_row]
	if not existing_flag_names:
		return True

	return any(bool(employee_row.get(flag_name)) for flag_name in existing_flag_names)


def get_employee_forbidden_weekdays(employee: str | None) -> set[int]:
	if not employee or not frappe.db.has_column("Employee", "forbidden_shift_days"):
		return set()

	day_string = frappe.db.get_value("Employee", employee, "forbidden_shift_days") or ""
	if not day_string:
		return set()

	weekdays = set()
	for token in str(day_string).replace("\n", ",").split(","):
		day_name = token.strip()
		if day_name in DAY_NAME_TO_WEEKDAY:
			weekdays.add(DAY_NAME_TO_WEEKDAY[day_name])
	return weekdays


def get_or_create_shift_role_for_designation(employee: str | None) -> str:
	if not employee:
		return ""

	designation = get_primary_employee_designation(employee)
	if not designation or not frappe.db.exists("DocType", "Shift Duty Role"):
		return ""

	role_name = frappe.db.get_value("Shift Duty Role", {"role_name": designation}, "name")
	if role_name:
		if frappe.db.get_value("Shift Duty Role", role_name, "is_active") == 0:
			frappe.db.set_value("Shift Duty Role", role_name, "is_active", 1, update_modified=False)
		return role_name

	role_doc = frappe.new_doc("Shift Duty Role")
	role_doc.role_name = designation
	role_doc.is_active = 1
	role_doc.insert(ignore_permissions=True)
	return role_doc.name


def get_primary_employee_designation(employee: str | None) -> str:
	if not employee:
		return ""

	if frappe.db.exists("DocType", "Employee Designation Assignment"):
		rows = frappe.get_all(
			"Employee Designation Assignment",
			filters={
				"parent": employee,
				"parenttype": "Employee",
				"parentfield": "employee_designations",
			},
			fields=["designation", "is_primary", "idx"],
			order_by="is_primary desc, idx asc",
			limit=1,
		)
		if rows and rows[0].get("designation"):
			return rows[0]["designation"]

	return frappe.db.get_value("Employee", employee, "designation") or ""


def get_default_shift_role_name() -> str:
	if not frappe.db.exists("DocType", "Shift Duty Role"):
		return ""

	role_name = frappe.db.get_value("Shift Duty Role", {"is_active": 1}, "name", order_by="creation asc")
	return role_name or ""


def get_employee_duty_role_names(employee: str | None) -> list[str]:
	if not employee or not frappe.db.exists("DocType", "Employee Shift Duty Role"):
		return []

	rows = frappe.get_all(
		"Employee Shift Duty Role",
		filters={"parent": employee, "parenttype": "Employee", "parentfield": "employee_shift_duty_roles"},
		pluck="shift_duty_role",
	)
	return [row for row in rows if row]


def get_default_duty_role_for_employee(employee: str | None) -> str:
	for role in get_employee_duty_role_names(employee):
		return role
	return get_or_create_shift_role_for_designation(employee) or get_default_shift_role_name()


def get_employee_duty_role_options(employee: str | None) -> list[dict]:
	role_names = []
	seen = set()
	for role in get_employee_duty_role_names(employee):
		if role in seen:
			continue
		seen.add(role)
		role_names.append(role)

	default_role = get_default_duty_role_for_employee(employee)
	if default_role and default_role not in seen:
		role_names.append(default_role)

	options = []
	for role_name in role_names:
		label = frappe.db.get_value("Shift Duty Role", role_name, "role_name") if role_name else ""
		options.append({"name": role_name, "role_name": label or role_name})
	return options



def has_shift_approver_team(user: str) -> bool:
	if not has_shift_request_approver_field():
		return False

	return bool(
		frappe.db.count("Employee", {"status": "Active", "shift_request_approver": user, "docstatus": ("<", 2)})
	)



def get_team_employee_ids_for_user(user: str) -> list[str]:
	if not has_shift_request_approver_field():
		return []

	return frappe.get_all(
		"Employee",
		filters={"status": "Active", "shift_request_approver": user, "docstatus": ("<", 2)},
		pluck="name",
	)



def can_manage_employee(user: str, target_employee: str) -> bool:
	if is_hr_user(user):
		return True

	current_employee = get_employee_for_user(user)
	if not current_employee:
		return False

	if current_employee == target_employee:
		return True

	if is_shift_allocator(user):
		return get_employee_shift_request_approver(target_employee) == user

	return False



def can_view_team(user: str, target_employee: str) -> bool:
	if is_hr_user(user):
		return True
	if get_employee_shift_request_approver(target_employee) == user:
		return True
	return False



def can_approve_plan(user: str, plan: WeeklyShiftPlan) -> bool:
	if is_hr_user(user):
		return True
	if plan.approver == user:
		return True
	if is_shift_allocator(user) and (get_employee_shift_request_approver(plan.employee) == user):
		return True
	return False


def has_shift_request_approver_field() -> bool:
	return frappe.db.has_column("Employee", "shift_request_approver")


def get_employee_shift_request_approver(employee: str | None) -> str | None:
	if not employee or not has_shift_request_approver_field():
		return None
	return frappe.db.get_value("Employee", employee, "shift_request_approver")



def cancel_generated_assignments_for_plan(plan_name: str) -> None:
	if not frappe.db.has_column("Shift Assignment", "weekly_shift_plan"):
		return

	assignments = frappe.get_all(
		"Shift Assignment",
		filters={"weekly_shift_plan": plan_name, "docstatus": 1},
		pluck="name",
	)
	for assignment_name in assignments:
		assignment_doc = frappe.get_doc("Shift Assignment", assignment_name)
		assignment_doc.flags.ignore_permissions = True
		try:
			assignment_doc.cancel()
		except Exception as error:
			frappe.throw(
				_("Unable to cancel old assignment {0}: {1}").format(
					frappe.bold(assignment_name), frappe.bold(str(error))
				)
			)



def generate_shift_assignments_for_plan(doc: WeeklyShiftPlan) -> list[str]:
	created = []
	for slot in sorted(doc.slot_details or [], key=lambda d: (get_date_str(d.work_date), d.slot_code or "")):
		if slot.assignment and frappe.db.exists("Shift Assignment", slot.assignment):
			continue

		assignment = frappe.new_doc("Shift Assignment")
		assignment.employee = doc.employee
		assignment.company = doc.company
		assignment.shift_type = slot.shift_type
		assignment.start_date = slot.work_date
		assignment.end_date = slot.work_date
		assignment.status = "Active"

		if frappe.db.has_column("Shift Assignment", "weekly_shift_plan"):
			assignment.weekly_shift_plan = doc.name
		if frappe.db.has_column("Shift Assignment", "weekly_shift_plan_slot"):
			assignment.weekly_shift_plan_slot = slot.name
		if frappe.db.has_column("Shift Assignment", "generated_from_weekly_plan"):
			assignment.generated_from_weekly_plan = 1

		assignment.flags.ignore_permissions = True

		try:
			assignment.insert(ignore_permissions=True)
			assignment.submit()
		except OverlappingShiftError as error:
			frappe.throw(
				_("Shift overlap on {0}: {1}").format(
					frappe.bold(get_date_str(slot.work_date)), frappe.bold(str(error))
				)
			)
		except Exception as error:
			frappe.throw(
				_("Failed creating Shift Assignment for {0}: {1}").format(
					frappe.bold(get_date_str(slot.work_date)), frappe.bold(str(error))
				)
			)

		slot.assignment = assignment.name
		created.append(assignment.name)

	doc.flags.ignore_validate_update_after_submit = True
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	return created



def get_manageable_employees(user: str) -> list[dict]:
	current_employee = get_employee_for_user(user)
	result = []
	seen = set()

	if current_employee:
		employee_name = frappe.db.get_value("Employee", current_employee, "employee_name")
		result.append({"name": current_employee, "employee_name": employee_name})
		seen.add(current_employee)

	if is_hr_user(user):
		for row in frappe.get_all(
			"Employee",
			filters={"status": "Active", "docstatus": ("<", 2)},
			fields=["name", "employee_name"],
			order_by="employee_name asc",
		):
			if row.name not in seen:
				result.append(row)
				seen.add(row.name)
		return result

	if is_shift_allocator(user) or has_shift_approver_team(user):
		if not has_shift_request_approver_field():
			return result
		for row in frappe.get_all(
			"Employee",
			filters={"status": "Active", "shift_request_approver": user, "docstatus": ("<", 2)},
			fields=["name", "employee_name"],
			order_by="employee_name asc",
		):
			if row.name not in seen:
				result.append(row)
				seen.add(row.name)

	return result



def serialize_plan(doc: WeeklyShiftPlan | None) -> dict | None:
	if not doc:
		return None

	payload = doc.as_dict()
	rules = get_dynamic_planner_rules(doc.employee, doc.week_start_date)
	payload["slot_details"] = sorted(
		[
			{
				"name": d.name,
				"work_date": get_date_str(d.work_date) if d.work_date else None,
				"slot_code": d.slot_code,
				"shift_type": d.shift_type,
				"start_time": str(d.start_time) if d.start_time else None,
				"end_time": str(d.end_time) if d.end_time else None,
				"duty_role": d.duty_role,
				"hours": flt(d.hours),
				"assignment": d.assignment,
			}
			for d in doc.slot_details or []
		],
		key=lambda d: ((d.get("work_date") or ""), (d.get("slot_code") or "")),
	)
	payload["can_approve"] = can_approve_plan(frappe.session.user, doc)
	payload["can_manage"] = can_manage_employee(frappe.session.user, doc.employee)
	payload["minimum_hours_required"] = rules["minimum_hours_per_week"]
	payload["required_days_per_week"] = rules["required_days_per_week"]
	payload["official_holidays_in_week"] = rules["official_holidays_in_week"]
	payload["employee_designation"] = frappe.db.get_value("Employee", doc.employee, "designation")
	payload["employee_requires_shift_registration"] = is_shift_registration_required(doc.employee)
	return payload
