import frappe
from frappe import _
from frappe.model import get_permitted_fields
from frappe.model.rename_doc import rename_doc
from frappe.model.workflow import get_workflow_name
from frappe.query_builder import Order
from frappe.utils import add_days, date_diff, getdate, strip_html

from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

SUPPORTED_FIELD_TYPES = [
	"Link",
	"Select",
	"Small Text",
	"Text",
	"Long Text",
	"Text Editor",
	"Table",
	"Check",
	"Data",
	"Float",
	"Int",
	"Section Break",
	"Date",
	"Time",
	"Datetime",
	"Currency",
]

HR_APPRAISAL_ROLES = {"HR Manager", "HR User", "System Manager"}
DOCSTATUS_LABELS = {0: "Draft", 1: "Submitted", 2: "Cancelled"}


@frappe.whitelist()
def get_current_user_info() -> dict:
	current_user = frappe.session.user
	user = frappe.db.get_value(
		"User", current_user, ["name", "first_name", "full_name", "user_image"], as_dict=True
	)
	user["roles"] = frappe.get_roles(current_user)

	return user


@frappe.whitelist()
def get_current_employee_info() -> dict:
	current_user = frappe.session.user
	employee_fields = [
		"name",
		"first_name",
		"employee_name",
		"designation",
		"department",
		"company",
		"reports_to",
		"leave_approver",
		"expense_approver",
		"user_id",
	]
	if frappe.db.has_column("Employee", "branch"):
		employee_fields.append("branch")
	if frappe.db.has_column("Employee", "is_shift_allocator"):
		employee_fields.append("is_shift_allocator")
	if frappe.db.has_column("Employee", "needs_shift_registration"):
		employee_fields.append("needs_shift_registration")
	if frappe.db.has_column("Employee", "has_rotational_shift"):
		employee_fields.append("has_rotational_shift")
	if frappe.db.has_column("Employee", "variable_shift"):
		employee_fields.append("variable_shift")
	if frappe.db.has_column("Employee", "forbidden_shift_days"):
		employee_fields.append("forbidden_shift_days")

	employee = frappe.db.get_value(
		"Employee",
		{"user_id": current_user, "status": "Active"},
		employee_fields,
		as_dict=True,
	)
	return employee


@frappe.whitelist()
def get_all_employees() -> list[dict]:
	return frappe.get_all(
		"Employee",
		fields=[
			"name",
			"employee_name",
			"designation",
			"department",
			"company",
			"reports_to",
			"user_id",
			"image",
			"status",
		],
		limit=999999,
	)


# HR Settings
@frappe.whitelist()
def get_hr_settings() -> dict:
	settings = frappe.db.get_singles_dict("HR Settings", cast=True)
	return frappe._dict(
		allow_employee_checkin_from_mobile_app=settings.allow_employee_checkin_from_mobile_app,
		allow_geolocation_tracking=settings.allow_geolocation_tracking,
	)


# Notifications
@frappe.whitelist()
def get_unread_notifications_count() -> int:
	return frappe.db.count(
		"PWA Notification",
		{"to_user": frappe.session.user, "read": 0},
	)


@frappe.whitelist()
def mark_all_notifications_as_read() -> None:
	frappe.db.set_value(
		"PWA Notification",
		{"to_user": frappe.session.user, "read": 0},
		"read",
		1,
		update_modified=False,
	)


@frappe.whitelist()
def are_push_notifications_enabled() -> bool:
	try:
		return frappe.db.get_single_value("Push Notification Settings", "enable_push_notification_relay")
	except frappe.DoesNotExistError:
		# push notifications are not supported in the current framework version
		return False


# Attendance
@frappe.whitelist()
def get_attendance_calendar_events(employee: str, from_date: str, to_date: str) -> dict[str, str]:
	holidays = get_holidays_for_calendar(employee, from_date, to_date)
	attendance = get_attendance_for_calendar(employee, from_date, to_date)
	events = {}

	date = getdate(from_date)
	while date_diff(to_date, date) >= 0:
		date_str = date.strftime("%Y-%m-%d")
		if date in attendance:
			events[date_str] = attendance[date]
		elif date in holidays:
			events[date_str] = "Holiday"
		date = add_days(date, 1)

	return events


def get_attendance_for_calendar(employee: str, from_date: str, to_date: str) -> list[dict[str, str]]:
	attendance = frappe.get_all(
		"Attendance",
		{"employee": employee, "attendance_date": ["between", [from_date, to_date]], "docstatus": 1},
		["attendance_date", "status"],
	)
	return {d["attendance_date"]: d["status"] for d in attendance}


def get_holidays_for_calendar(employee: str, from_date: str, to_date: str) -> list[str]:
	if holiday_list := get_holiday_list_for_employee(employee, raise_exception=False):
		return frappe.get_all(
			"Holiday",
			filters={"parent": holiday_list, "holiday_date": ["between", [from_date, to_date]]},
			pluck="holiday_date",
		)

	return []


@frappe.whitelist()
def get_shift_requests(
	employee: str,
	approver_id: str | None = None,
	for_approval: bool = False,
	limit: int | None = None,
) -> list[dict]:
	filters = get_filters("Shift Request", employee, approver_id, for_approval)
	fields = [
		"name",
		"employee",
		"employee_name",
		"shift_type",
		"from_date",
		"to_date",
		"status",
		"approver",
		"docstatus",
		"modified",
		"creation",
	]

	if workflow_state_field := get_workflow_state_field("Shift Request"):
		fields.append(workflow_state_field)

	shift_requests = frappe.get_list(
		"Shift Request",
		fields=fields,
		filters=filters,
		order_by="modified desc",
		limit=limit,
	)

	if workflow_state_field:
		for application in shift_requests:
			application["workflow_state_field"] = workflow_state_field

	return shift_requests


@frappe.whitelist()
def get_attendance_requests(
	employee: str,
	for_approval: bool = False,
	limit: int | None = None,
) -> list[dict]:
	approver_id = frappe.session.user if for_approval else None
	filters = get_filters("Attendance Request", employee, approver_id, for_approval)
	fields = [
		"name",
		"request_mode",
		"review_status",
		"requested_log_type",
		"requested_time",
		"reviewed_log_type",
		"reviewed_time",
		"employee_checkin",
		"shift_request_approver",
		"reason",
		"employee",
		"employee_name",
		"from_date",
		"to_date",
		"include_holidays",
		"shift",
		"docstatus",
		"modified",
		"creation",
	]

	if workflow_state_field := get_workflow_state_field("Attendance Request"):
		fields.append(workflow_state_field)

	attendance_requests = frappe.get_list(
		"Attendance Request",
		fields=fields,
		filters=filters,
		order_by="modified desc",
		limit=limit,
	)

	if workflow_state_field:
		for application in attendance_requests:
			application["workflow_state_field"] = workflow_state_field

	return attendance_requests


@frappe.whitelist()
def get_appraisals(
	employee: str | None = None,
	for_approval: bool = False,
	cycle: str | None = None,
	status: str | None = None,
	limit: int | None = None,
) -> list[dict]:
	is_hr_user = _is_hr_appraisal_user()
	current_employee = _get_session_employee(raise_exception=not is_hr_user)
	for_approval = frappe.utils.cint(for_approval)
	limit = frappe.utils.cint(limit) or None

	filters = frappe._dict(docstatus=("!=", 2))
	if cycle:
		filters.appraisal_cycle = cycle

	if status and status in {"Draft", "Submitted", "Cancelled"}:
		filters.docstatus = {"Draft": 0, "Submitted": 1, "Cancelled": 2}[status]

	if for_approval:
		if not is_hr_user:
			return []
		if current_employee:
			filters.employee = ("!=", current_employee.name)
	else:
		if not employee:
			if current_employee:
				employee = current_employee.name
			elif not is_hr_user:
				frappe.throw(_("No active employee linked to your user account."))
		if employee and current_employee and employee != current_employee.name and not is_hr_user:
			frappe.throw(_("You are not allowed to access appraisals for other employees."))
		if employee:
			filters.employee = employee

	fields = [
		"name",
		"employee",
		"employee_name",
		"company",
		"designation",
		"appraisal_cycle",
		"appraisal_template",
		"start_date",
		"end_date",
		"final_score",
		"total_score",
		"self_score",
		"avg_feedback_score",
		"docstatus",
		"modified",
		"creation",
	]

	appraisals = frappe.get_list(
		"Appraisal",
		fields=fields,
		filters=filters,
		order_by="modified desc",
		limit=limit,
	)
	for appraisal in appraisals:
		appraisal["status"] = DOCSTATUS_LABELS.get(appraisal.docstatus, "Draft")

	return appraisals


@frappe.whitelist()
def get_appraisal_detail(name: str) -> dict:
	doc = frappe.get_doc("Appraisal", name)
	_ensure_appraisal_access(doc)

	permissions = _get_appraisal_permissions(doc)
	return {
		"name": doc.name,
		"employee": doc.employee,
		"employee_name": doc.employee_name,
		"company": doc.company,
		"designation": doc.designation,
		"appraisal_cycle": doc.appraisal_cycle,
		"appraisal_template": doc.appraisal_template,
		"start_date": doc.start_date,
		"end_date": doc.end_date,
		"final_score": doc.final_score,
		"total_score": doc.total_score,
		"self_score": doc.self_score,
		"avg_feedback_score": doc.avg_feedback_score,
		"goal_score_percentage": doc.goal_score_percentage,
		"remarks": doc.remarks,
		"reflections": doc.reflections,
		"rate_goals_manually": doc.rate_goals_manually,
		"docstatus": doc.docstatus,
		"status": DOCSTATUS_LABELS.get(doc.docstatus, "Draft"),
		"permissions": permissions,
		"self_ratings": [
			{
				"name": row.name,
				"criteria": row.criteria,
				"per_weightage": row.per_weightage,
				"rating": row.rating,
			}
			for row in doc.self_ratings
		],
		"goals": [
			{
				"name": row.name,
				"kra": row.kra,
				"per_weightage": row.per_weightage,
				"score": row.score,
				"score_earned": row.score_earned,
			}
			for row in doc.goals
		],
		"appraisal_kra": [
			{
				"name": row.name,
				"kra": row.kra,
				"per_weightage": row.per_weightage,
				"goal_completion": row.goal_completion,
				"goal_score": row.goal_score,
			}
			for row in doc.appraisal_kra
		],
	}


@frappe.whitelist()
def create_appraisal(
	employee: str,
	appraisal_cycle: str | None = None,
	appraisal_template: str | None = None,
) -> dict:
	if not _is_hr_appraisal_user():
		frappe.throw(_("Only HR roles can create appraisals."))

	employee_doc = frappe.get_doc("Employee", employee)
	if employee_doc.status != "Active":
		frappe.throw(_("Selected employee is not active."))

	appraisal_cycle = appraisal_cycle or _get_default_appraisal_cycle(employee_doc.company)
	if not appraisal_cycle:
		frappe.throw(_("No active appraisal cycle found for this employee's company."))

	cycle_doc = frappe.get_doc("Appraisal Cycle", appraisal_cycle)
	if cycle_doc.company != employee_doc.company:
		frappe.throw(_("Employee and appraisal cycle must belong to the same company."))

	if not appraisal_template:
		designation = _get_primary_designation(employee_doc.name) or employee_doc.designation
		if designation:
			appraisal_template = frappe.db.get_value("Designation", designation, "appraisal_template")

	if not appraisal_template:
		frappe.throw(_("Appraisal Template is required for this employee."))

	doc = frappe.get_doc(
		{
			"doctype": "Appraisal",
			"employee": employee_doc.name,
			"company": employee_doc.company,
			"appraisal_cycle": cycle_doc.name,
			"appraisal_template": appraisal_template,
			"naming_series": "HR-APR-.YYYY.-",
		}
	)
	doc.set_kras_and_rating_criteria()
	doc.insert(ignore_permissions=True)

	return {"name": doc.name}


@frappe.whitelist()
def get_appraisal_defaults(employee: str) -> dict:
	if not _is_hr_appraisal_user():
		frappe.throw(_("Only HR roles can access appraisal defaults."))
	if not employee:
		frappe.throw(_("Employee is required."))

	employee_doc = frappe.get_doc("Employee", employee)
	designation = _get_primary_designation(employee_doc.name) or employee_doc.designation
	appraisal_template = (
		frappe.db.get_value("Designation", designation, "appraisal_template") if designation else None
	)

	return {
		"employee": employee_doc.name,
		"company": employee_doc.company,
		"designation": designation,
		"appraisal_cycle": _get_default_appraisal_cycle(employee_doc.company),
		"appraisal_template": appraisal_template,
	}


@frappe.whitelist()
def upsert_self_appraisal(payload: str | dict | None = None) -> dict:
	data = _parse_payload(payload)
	doc = frappe.get_doc("Appraisal", data.get("name"))

	permissions = _get_appraisal_permissions(doc)
	if not permissions.get("can_self_edit"):
		frappe.throw(_("You are not allowed to edit this self appraisal."))
	if doc.docstatus != 0:
		frappe.throw(_("Submitted appraisals cannot be edited."))

	if "reflections" in data:
		doc.reflections = data.get("reflections")

	incoming_rows = data.get("self_ratings") or []
	if isinstance(incoming_rows, list):
		rating_map_by_name = {
			entry.get("name"): entry for entry in incoming_rows if isinstance(entry, dict) and entry.get("name")
		}
		rating_map_by_criteria = {
			entry.get("criteria"): entry
			for entry in incoming_rows
			if isinstance(entry, dict) and entry.get("criteria")
		}

		for row in doc.self_ratings:
			entry = rating_map_by_name.get(row.name) or rating_map_by_criteria.get(row.criteria)
			if entry and entry.get("rating") is not None:
				row.rating = _normalize_rating(entry.get("rating"))

	doc.save(ignore_permissions=True)
	return {"name": doc.name, "self_score": doc.self_score, "final_score": doc.final_score}


@frappe.whitelist()
def upsert_team_appraisal(payload: str | dict | None = None) -> dict:
	if not _is_hr_appraisal_user():
		frappe.throw(_("Only HR roles can update team appraisals."))

	data = _parse_payload(payload)
	doc = frappe.get_doc("Appraisal", data.get("name"))
	_ensure_appraisal_access(doc)
	permissions = _get_appraisal_permissions(doc)
	if not permissions.get("can_team_edit"):
		frappe.throw(_("You can only review appraisals for other employees."))
	if doc.docstatus != 0:
		frappe.throw(_("Submitted appraisals cannot be edited."))

	if "remarks" in data:
		doc.remarks = data.get("remarks")

	incoming_goals = data.get("goals") or []
	if doc.rate_goals_manually and isinstance(incoming_goals, list):
		goal_map_by_name = {
			entry.get("name"): entry for entry in incoming_goals if isinstance(entry, dict) and entry.get("name")
		}
		goal_map_by_kra = {
			entry.get("kra"): entry for entry in incoming_goals if isinstance(entry, dict) and entry.get("kra")
		}

		for row in doc.goals:
			entry = goal_map_by_name.get(row.name) or goal_map_by_kra.get(row.kra)
			if entry and entry.get("score") is not None:
				row.score = _normalize_score(entry.get("score"))

	doc.save(ignore_permissions=True)
	return {"name": doc.name, "total_score": doc.total_score, "final_score": doc.final_score}


@frappe.whitelist()
def submit_appraisal(name: str) -> dict:
	if not _is_hr_appraisal_user():
		frappe.throw(_("Only HR roles can submit appraisals."))

	doc = frappe.get_doc("Appraisal", name)
	_ensure_appraisal_access(doc)
	permissions = _get_appraisal_permissions(doc)
	if not permissions.get("can_team_edit"):
		frappe.throw(_("You can only submit appraisals for other employees."))

	if doc.docstatus != 0:
		frappe.throw(_("Only draft appraisals can be submitted."))

	doc.submit()
	return {"name": doc.name, "docstatus": doc.docstatus, "status": DOCSTATUS_LABELS.get(doc.docstatus)}


@frappe.whitelist()
def add_appraisal_feedback(payload: str | dict | None = None) -> dict:
	if not _is_hr_appraisal_user():
		frappe.throw(_("Only HR roles can submit appraisal feedback."))

	data = _parse_payload(payload)
	doc = frappe.get_doc("Appraisal", data.get("name") or data.get("appraisal"))
	_ensure_appraisal_access(doc)
	permissions = _get_appraisal_permissions(doc)
	if not permissions.get("can_team_edit"):
		frappe.throw(_("You can only submit feedback for other employees."))

	feedback = (data.get("feedback") or "").strip()
	if not feedback:
		frappe.throw(_("Feedback is required."))

	ratings = data.get("feedback_ratings") or []
	weightage_map = {row.criteria: row.per_weightage for row in doc.self_ratings}
	formatted_ratings = []
	for row in ratings:
		if not isinstance(row, dict) or not row.get("criteria"):
			continue
		formatted_ratings.append(
			{
				"criteria": row.get("criteria"),
				"rating": _normalize_rating(row.get("rating")),
				"per_weightage": row.get("per_weightage")
				or weightage_map.get(row.get("criteria"))
				or 0,
			}
		)

	if not formatted_ratings:
		frappe.throw(_("At least one feedback rating is required."))

	feedback_doc = doc.add_feedback(feedback=feedback, feedback_ratings=formatted_ratings)
	return {"name": feedback_doc.name, "total_score": feedback_doc.total_score}


def _parse_payload(payload: str | dict | None) -> dict:
	if payload is None:
		return {}
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	if not isinstance(payload, dict):
		frappe.throw(_("Invalid payload."))
	return payload


def _is_hr_appraisal_user() -> bool:
	return bool(set(frappe.get_roles()) & HR_APPRAISAL_ROLES)


def _get_session_employee(raise_exception: bool = True) -> frappe._dict:
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user, "status": "Active"},
		["name", "employee_name", "company", "designation"],
		as_dict=True,
	)
	if not employee and raise_exception:
		frappe.throw(_("No active employee linked to your user account."))
	return employee or frappe._dict()


def _ensure_appraisal_access(appraisal_doc):
	if _is_hr_appraisal_user():
		return

	current_employee = _get_session_employee()
	if appraisal_doc.employee != current_employee.name:
		frappe.throw(_("You are not allowed to access this appraisal."))


def _get_appraisal_permissions(appraisal_doc) -> dict:
	current_employee = _get_session_employee(raise_exception=False)
	is_hr = _is_hr_appraisal_user()
	is_self_owner = bool(current_employee and appraisal_doc.employee == current_employee.name)

	return {
		"is_hr_user": is_hr,
		"is_self_owner": is_self_owner,
		"can_self_edit": appraisal_doc.docstatus == 0 and is_self_owner,
		"can_team_edit": appraisal_doc.docstatus == 0 and is_hr and not is_self_owner,
	}


def _normalize_rating(value) -> float:
	rating = frappe.utils.flt(value)
	if rating > 1:
		rating = rating / 5
	return min(max(rating, 0), 1)


def _normalize_score(value) -> float:
	score = frappe.utils.flt(value)
	return min(max(score, 0), 5)


def _get_primary_designation(employee: str) -> str | None:
	if not frappe.db.exists("DocType", "Employee Designation Assignment"):
		return None

	designation = frappe.db.get_value(
		"Employee Designation Assignment",
		{
			"parent": employee,
			"parenttype": "Employee",
			"parentfield": "employee_designations",
			"is_primary": 1,
		},
		"designation",
	)
	if designation:
		return designation

	return frappe.db.get_value(
		"Employee Designation Assignment",
		{
			"parent": employee,
			"parenttype": "Employee",
			"parentfield": "employee_designations",
		},
		"designation",
	)


def _get_default_appraisal_cycle(company: str) -> str | None:
	today = getdate()

	active_cycles = frappe.get_all(
		"Appraisal Cycle",
		filters={
			"company": company,
			"status": ("!=", "Completed"),
			"start_date": ("<=", today),
			"end_date": (">=", today),
		},
		pluck="name",
		order_by="start_date desc",
		limit=1,
	)
	if active_cycles:
		return active_cycles[0]

	in_progress_cycles = frappe.get_all(
		"Appraisal Cycle",
		filters={"company": company, "status": "In Progress"},
		pluck="name",
		order_by="start_date desc",
		limit=1,
	)
	if in_progress_cycles:
		return in_progress_cycles[0]

	upcoming_cycles = frappe.get_all(
		"Appraisal Cycle",
		filters={
			"company": company,
			"status": "Not Started",
			"start_date": (">=", today),
		},
		pluck="name",
		order_by="start_date asc",
		limit=1,
	)
	if upcoming_cycles:
		return upcoming_cycles[0]

	fallback_cycle = frappe.get_all(
		"Appraisal Cycle",
		filters={"company": company, "status": ("!=", "Completed")},
		pluck="name",
		order_by="start_date desc",
		limit=1,
	)
	return fallback_cycle[0] if fallback_cycle else None


def get_filters(
	doctype: str,
	employee: str,
	approver_id: str | None = None,
	for_approval: bool = False,
) -> dict:
	filters = frappe._dict()
	if for_approval:
		filters.docstatus = 0
		filters.employee = ("!=", employee)

		if doctype == "Attendance Request":
			filters.request_mode = "Checkin Request"
			filters.review_status = "Pending"
			if approver_id:
				filters.shift_request_approver = approver_id
		elif workflow := get_workflow(doctype):
			allowed_states = get_allowed_states_for_workflow(workflow, approver_id)
			filters[workflow.workflow_state_field] = ("in", allowed_states)
		elif doctype != "Attendance Request":
			approver_field_map = {
				"Shift Request": "approver",
				"Leave Application": "leave_approver",
				"Expense Claim": "expense_approver",
			}
			filters.status = "Open" if doctype == "Leave Application" else "Draft"
			if approver_id:
				filters[approver_field_map[doctype]] = approver_id
	else:
		filters.docstatus = ("!=", 2)
		filters.employee = employee

	return filters


@frappe.whitelist()
def get_shift_request_approvers(employee: str) -> str | list[str]:
	shift_request_approver, department = frappe.get_cached_value(
		"Employee",
		employee,
		["shift_request_approver", "department"],
	)

	department_approvers = []
	if department:
		department_approvers = get_department_approvers(department, "shift_request_approver")
		if not shift_request_approver:
			shift_request_approver = frappe.db.get_value(
				"Department Approver",
				{"parent": department, "parentfield": "shift_request_approver", "idx": 1},
				"approver",
			)

	shift_request_approver_name = frappe.db.get_value("User", shift_request_approver, "full_name", cache=True)

	if shift_request_approver and shift_request_approver not in [
		approver.name for approver in department_approvers
	]:
		department_approvers.insert(
			0, {"name": shift_request_approver, "full_name": shift_request_approver_name}
		)

	return department_approvers


@frappe.whitelist()
def review_attendance_checkin_request(
	name: str,
	action: str,
	reviewed_time: str | None = None,
	reviewed_log_type: str | None = None,
	comment: str | None = None,
) -> dict:
	from hrms.hr.doctype.attendance_request.attendance_request import (
		review_attendance_checkin_request as review_request,
	)

	return review_request(
		name=name,
		action=action,
		reviewed_time=reviewed_time,
		reviewed_log_type=reviewed_log_type,
		comment=comment,
	)


@frappe.whitelist()
def sync_daily_attendance_from_checkins(target_date: str | None = None) -> dict:
	from hrms.hr.doctype.employee_checkin.attendance_sync import sync_attendance_from_checkins_daily

	return sync_attendance_from_checkins_daily(target_date=target_date)


@frappe.whitelist()
def localize_default_leave_types_for_iran() -> dict:
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only System Manager can rename default leave types."))

	rename_map = {
		"Leave Without Pay": "مرخصی بدون حقوق",
		"Privilege Leave": "مرخصی استحقاقی",
		"Sick Leave": "مرخصی استعلاجی",
		"Compensatory Off": "مرخصی جبرانی",
		"Casual Leave": "مرخصی اتفاقی",
	}
	renamed = []
	skipped = []

	for old_name, new_name in rename_map.items():
		if not frappe.db.exists("Leave Type", old_name):
			skipped.append(old_name)
			continue

		if frappe.db.exists("Leave Type", new_name):
			skipped.append(old_name)
			continue

		rename_doc("Leave Type", old_name, new_name, force=True, merge=False)
		renamed.append({"from": old_name, "to": new_name})

	return {"renamed": renamed, "skipped": skipped}


@frappe.whitelist()
def get_shifts(employee: str) -> list[dict[str, str]]:
	ShiftAssignment = frappe.qb.DocType("Shift Assignment")
	ShiftType = frappe.qb.DocType("Shift Type")
	return (
		frappe.qb.from_(ShiftAssignment)
		.join(ShiftType)
		.on(ShiftAssignment.shift_type == ShiftType.name)
		.select(
			ShiftAssignment.name,
			ShiftAssignment.shift_type,
			ShiftAssignment.start_date,
			ShiftAssignment.end_date,
			ShiftType.start_time,
			ShiftType.end_time,
		)
		.where(
			(ShiftAssignment.employee == employee)
			& (ShiftAssignment.status == "Active")
			& (ShiftAssignment.docstatus == 1)
		)
		.orderby(ShiftAssignment.start_date, order=Order.asc)
	).run(as_dict=True)


# Weekly Shift Planner
@frappe.whitelist()
def get_weekly_shift_context(
	target_date: str | None = None,
	week_start_date: str | None = None,
	employee: str | None = None,
) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import get_weekly_shift_context

	return get_weekly_shift_context(
		target_date=target_date,
		week_start_date=week_start_date,
		employee=employee,
	)


@frappe.whitelist()
def get_weekly_shift_slot_templates() -> list[dict]:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import get_weekly_shift_slot_templates

	return get_weekly_shift_slot_templates()


@frappe.whitelist()
def upsert_weekly_shift_plan(payload: str | dict | None = None) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import upsert_weekly_shift_plan

	return upsert_weekly_shift_plan(payload=payload)


@frappe.whitelist()
def submit_weekly_shift_plan(plan_name: str) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import submit_weekly_shift_plan

	return submit_weekly_shift_plan(plan_name=plan_name)


@frappe.whitelist()
def list_my_weekly_shift_plans(
	week_start_date: str | None = None,
	status: str | None = None,
) -> list[dict]:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import list_my_weekly_shift_plans

	return list_my_weekly_shift_plans(week_start_date=week_start_date, status=status)


@frappe.whitelist()
def list_team_weekly_shift_plans(
	week_start_date: str | None = None,
	status: str | None = None,
) -> list[dict]:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import list_team_weekly_shift_plans

	return list_team_weekly_shift_plans(week_start_date=week_start_date, status=status)


@frappe.whitelist()
def get_shift_allocator_team_overview(week_start_date: str | None = None) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import get_shift_allocator_team_overview

	return get_shift_allocator_team_overview(week_start_date=week_start_date)


@frappe.whitelist()
def approve_weekly_shift_plan(plan_name: str, note: str | None = None) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import approve_weekly_shift_plan

	return approve_weekly_shift_plan(plan_name=plan_name, note=note)


@frappe.whitelist()
def reject_weekly_shift_plan(plan_name: str, reason: str | None = None) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import reject_weekly_shift_plan

	return reject_weekly_shift_plan(plan_name=plan_name, reason=reason)


@frappe.whitelist()
def create_weekly_shift_plan_amendment(source_plan_name: str) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import (
		create_weekly_shift_plan_amendment,
	)

	return create_weekly_shift_plan_amendment(source_plan_name=source_plan_name)


@frappe.whitelist()
def get_weekly_shift_finalization_context(week_start_date: str | None = None) -> dict:
	from hrms.hr.doctype.weekly_shift_finalization.weekly_shift_finalization import (
		get_weekly_shift_finalization_context,
	)

	return get_weekly_shift_finalization_context(week_start_date=week_start_date)


@frappe.whitelist()
def upsert_weekly_shift_finalization(payload: str | dict | None = None) -> dict:
	from hrms.hr.doctype.weekly_shift_finalization.weekly_shift_finalization import (
		upsert_weekly_shift_finalization,
	)

	return upsert_weekly_shift_finalization(payload=payload)


@frappe.whitelist()
def finalize_weekly_shift_finalization(finalization_name: str) -> dict:
	from hrms.hr.doctype.weekly_shift_finalization.weekly_shift_finalization import (
		finalize_weekly_shift_finalization,
	)

	return finalize_weekly_shift_finalization(finalization_name=finalization_name)


@frappe.whitelist()
def create_weekly_shift_finalization_amendment(source_finalization_name: str) -> dict:
	from hrms.hr.doctype.weekly_shift_finalization.weekly_shift_finalization import (
		create_weekly_shift_finalization_amendment,
	)

	return create_weekly_shift_finalization_amendment(source_finalization_name=source_finalization_name)


@frappe.whitelist()
def get_employee_finalized_shift_slots(
	employee: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
) -> list[dict]:
	from hrms.hr.doctype.weekly_shift_finalization.weekly_shift_finalization import (
		get_employee_finalized_shift_slots,
	)

	return get_employee_finalized_shift_slots(employee=employee, from_date=from_date, to_date=to_date)


# Leaves and Holidays
@frappe.whitelist()
def get_leave_applications(
	employee: str,
	approver_id: str | None = None,
	for_approval: bool = False,
	limit: int | None = None,
) -> list[dict]:
	filters = get_filters("Leave Application", employee, approver_id, for_approval)
	fields = [
		"name",
		"posting_date",
		"employee",
		"employee_name",
		"leave_type",
		"leave_duration_mode",
		"hourly_date",
		"hourly_from_time",
		"hourly_to_time",
		"leave_substitute",
		"status",
		"from_date",
		"to_date",
		"half_day",
		"half_day_date",
		"description",
		"total_leave_days",
		"total_leave_hours",
		"leave_balance",
		"leave_approver",
		"modified",
		"posting_date",
		"creation",
	]

	if workflow_state_field := get_workflow_state_field("Leave Application"):
		fields.append(workflow_state_field)

	applications = frappe.get_list(
		"Leave Application",
		fields=fields,
		filters=filters,
		order_by="modified desc",
		limit=limit,
	)

	if workflow_state_field:
		for application in applications:
			application["workflow_state_field"] = workflow_state_field

	return applications


@frappe.whitelist()
def get_leave_balance_map(employee: str) -> dict[str, dict[str, float]]:
	"""
	Returns a map of leave type and balance details like:
	{
	        'Casual Leave': {'allocated_leaves': 10.0, 'balance_leaves': 5.0},
	        'Earned Leave': {'allocated_leaves': 3.0, 'balance_leaves': 3.0},
	}
	"""
	from hrms.hr.doctype.leave_application.leave_application import get_leave_details

	date = getdate()
	leave_map = {}

	leave_details = get_leave_details(employee, date)
	allocation = leave_details["leave_allocation"]

	for leave_type, details in allocation.items():
		leave_map[leave_type] = {
			"allocated_leaves": details.get("total_leaves"),
			"balance_leaves": details.get("remaining_leaves"),
		}

	return leave_map


@frappe.whitelist()
def get_holidays_for_employee(employee: str) -> list[dict]:
	holiday_list = get_holiday_list_for_employee(employee, raise_exception=False)
	if not holiday_list:
		return []

	Holiday = frappe.qb.DocType("Holiday")
	holidays = (
		frappe.qb.from_(Holiday)
		.select(Holiday.name, Holiday.holiday_date, Holiday.description)
		.where((Holiday.parent == holiday_list) & (Holiday.weekly_off == 0))
		.orderby(Holiday.holiday_date, order=Order.asc)
	).run(as_dict=True)

	for holiday in holidays:
		holiday["description"] = strip_html(holiday["description"] or "").strip()

	return holidays


@frappe.whitelist()
def get_leave_approval_details(employee: str) -> dict:
	leave_approver, department = frappe.get_cached_value(
		"Employee",
		employee,
		["leave_approver", "department"],
	)

	if not leave_approver and department:
		leave_approver = frappe.db.get_value(
			"Department Approver",
			{"parent": department, "parentfield": "leave_approvers", "idx": 1},
			"approver",
		)

	leave_approver_name = frappe.db.get_value("User", leave_approver, "full_name", cache=True)
	department_approvers = get_department_approvers(department, "leave_approvers")

	if leave_approver and leave_approver not in [approver.name for approver in department_approvers]:
		department_approvers.append({"name": leave_approver, "full_name": leave_approver_name})

	return dict(
		leave_approver=leave_approver,
		leave_approver_name=leave_approver_name,
		department_approvers=department_approvers,
		is_mandatory=frappe.db.get_single_value(
			"HR Settings", "leave_approver_mandatory_in_leave_application"
		),
	)


def get_department_approvers(department: str, parentfield: str) -> list[str]:
	if not department:
		return []

	department_details = frappe.db.get_value("Department", department, ["lft", "rgt"], as_dict=True)
	departments = frappe.get_all(
		"Department",
		filters={
			"lft": ("<=", department_details.lft),
			"rgt": (">=", department_details.rgt),
			"disabled": 0,
		},
		pluck="name",
	)

	Approver = frappe.qb.DocType("Department Approver")
	User = frappe.qb.DocType("User")
	department_approvers = (
		frappe.qb.from_(User)
		.join(Approver)
		.on(Approver.approver == User.name)
		.select(User.name.as_("name"), User.full_name.as_("full_name"))
		.where((Approver.parent.isin(departments)) & (Approver.parentfield == parentfield))
	).run(as_dict=True)

	return department_approvers


@frappe.whitelist()
def get_leave_types(employee: str, date: str) -> list:
	from hrms.hr.doctype.leave_application.leave_application import get_leave_details

	date = date or getdate()

	leave_details = get_leave_details(employee, date)
	leave_types = list(leave_details["leave_allocation"].keys()) + leave_details["lwps"]

	return leave_types


# Expense Claims
@frappe.whitelist()
def get_expense_claims(
	employee: str,
	approver_id: str | None = None,
	for_approval: bool = False,
	limit: int | None = None,
) -> list[dict]:
	filters = get_filters("Expense Claim", employee, approver_id, for_approval)
	fields = [
		"`tabExpense Claim`.name",
		"`tabExpense Claim`.posting_date",
		"`tabExpense Claim`.employee",
		"`tabExpense Claim`.employee_name",
		"`tabExpense Claim`.approval_status",
		"`tabExpense Claim`.status",
		"`tabExpense Claim`.expense_approver",
		"`tabExpense Claim`.total_claimed_amount",
		"`tabExpense Claim`.posting_date",
		"`tabExpense Claim`.company",
		"`tabExpense Claim`.modified",
		"`tabExpense Claim`.creation",
		"`tabExpense Claim Detail`.expense_type",
		"count(`tabExpense Claim Detail`.expense_type) as total_expenses",
	]

	if workflow_state_field := get_workflow_state_field("Expense Claim"):
		fields.append(workflow_state_field)

	claims = frappe.get_list(
		"Expense Claim",
		fields=fields,
		filters=filters,
		order_by="`tabExpense Claim`.modified desc",
		group_by="`tabExpense Claim`.name",
		limit=limit,
	)

	if workflow_state_field:
		for claim in claims:
			claim["workflow_state_field"] = workflow_state_field

	return claims


@frappe.whitelist()
def get_expense_claim_summary(employee: str) -> dict:
	from frappe.query_builder.functions import Sum

	Claim = frappe.qb.DocType("Expense Claim")

	pending_claims_case = (
		frappe.qb.terms.Case().when(Claim.approval_status == "Draft", Claim.total_claimed_amount).else_(0)
	)
	sum_pending_claims = Sum(pending_claims_case).as_("total_pending_amount")

	approved_claims_case = (
		frappe.qb.terms.Case()
		.when(Claim.approval_status == "Approved", Claim.total_sanctioned_amount)
		.else_(0)
	)
	sum_approved_claims = Sum(approved_claims_case).as_("total_approved_amount")

	approved_total_claimed_case = (
		frappe.qb.terms.Case().when(Claim.approval_status == "Approved", Claim.total_claimed_amount).else_(0)
	)
	sum_approved_total_claimed = Sum(approved_total_claimed_case).as_("total_claimed_in_approved")

	rejected_claims_case = (
		frappe.qb.terms.Case().when(Claim.approval_status == "Rejected", Claim.total_claimed_amount).else_(0)
	)
	sum_rejected_claims = Sum(rejected_claims_case).as_("total_rejected_amount")

	summary = (
		frappe.qb.from_(Claim)
		.select(
			sum_pending_claims,
			sum_approved_claims,
			sum_rejected_claims,
			sum_approved_total_claimed,
			Claim.company,
		)
		.where((Claim.docstatus != 2) & (Claim.employee == employee))
	).run(as_dict=True)[0]

	currency = frappe.db.get_value("Company", summary.company, "default_currency")
	summary["currency"] = currency

	return summary


@frappe.whitelist()
def get_expense_type_description(expense_type: str) -> str:
	return frappe.db.get_value("Expense Claim Type", expense_type, "description")


@frappe.whitelist()
def get_expense_claim_types() -> list[dict]:
	ClaimType = frappe.qb.DocType("Expense Claim Type")

	return (frappe.qb.from_(ClaimType).select(ClaimType.name, ClaimType.description)).run(as_dict=True)


# Employee Grievance
IRAN_GRIEVANCE_TYPES = [
	{
		"name": "تأخیر یا پرداخت‌نشدن حقوق و مزایا",
		"description": "شکایت درباره تاخیر یا پرداخت ناقص حقوق، مزایا، عیدی یا سنوات.",
	},
	{
		"name": "ساعات کار، اضافه‌کاری و نوبت‌کاری",
		"description": "مسائل مرتبط با ساعات کار، اضافه‌کاری، شیفت و محاسبه حق شیفت.",
	},
	{
		"name": "مرخصی، غیبت و تعطیلات",
		"description": "اختلاف در ثبت یا تایید مرخصی استحقاقی، استعلاجی، ساعتی یا تعطیلات.",
	},
	{
		"name": "ایمنی، بهداشت و شرایط محیط کار",
		"description": "گزارش موارد ناایمن، نبود تجهیزات ایمنی یا شرایط نامطلوب محیط کار.",
	},
	{
		"name": "رفتار نامناسب یا تبعیض در محیط کار",
		"description": "شکایت درباره تبعیض، بی‌احترامی، آزار کلامی یا رفتار غیرحرفه‌ای.",
	},
	{
		"name": "قرارداد، بیمه و مسائل قانونی",
		"description": "مسائل مربوط به قرارداد کار، بیمه تامین اجتماعی و حقوق قانونی کارمند.",
	},
	{
		"name": "سایر موارد",
		"description": "سایر شکایات و انتقادهایی که در دسته‌های بالا قرار نمی‌گیرند.",
	},
]


@frappe.whitelist()
def get_employee_grievances(
	employee: str,
	for_approval: bool = False,
	limit: int | None = None,
) -> list[dict]:
	filters = frappe._dict(docstatus=("!=", 2))
	for_approval = frappe.utils.cint(for_approval)
	limit = frappe.utils.cint(limit) or None

	if for_approval:
		subordinate_employees = frappe.get_all(
			"Employee",
			filters={"reports_to": employee, "status": "Active"},
			pluck="name",
		)
		if not subordinate_employees:
			return []

		filters.raised_by = ("in", subordinate_employees)
	else:
		filters.raised_by = employee

	fields = [
		"name",
		"subject",
		"feedback_type",
		"grievance_type",
		"status",
		"date",
		"raised_by",
		"employee_name",
		"designation",
		"reports_to",
		"grievance_against_party",
		"grievance_against",
		"description",
		"cause_of_grievance",
		"resolution_detail",
		"resolved_by",
		"resolution_date",
		"docstatus",
		"modified",
		"creation",
	]

	if workflow_state_field := get_workflow_state_field("Employee Grievance"):
		fields.append(workflow_state_field)

	grievances = frappe.get_list(
		"Employee Grievance",
		fields=fields,
		filters=filters,
		order_by="modified desc",
		limit=limit,
	)

	if workflow_state_field:
		for grievance in grievances:
			grievance["workflow_state_field"] = workflow_state_field

	return grievances


@frappe.whitelist()
def get_grievance_types() -> list[dict]:
	return frappe.get_all(
		"Grievance Type",
		fields=["name", "description"],
		order_by="name asc",
	)


@frappe.whitelist()
def seed_iran_grievance_types() -> dict:
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only System Manager can create default grievance types."))
	return ensure_iran_grievance_types()


def ensure_iran_grievance_types() -> dict:
	inserted = []
	existing = []

	for grievance_type in IRAN_GRIEVANCE_TYPES:
		name = grievance_type["name"]
		description = grievance_type["description"]

		if frappe.db.exists("Grievance Type", name):
			existing.append(name)
			current_description = frappe.db.get_value("Grievance Type", name, "description")
			if not current_description and description:
				frappe.db.set_value("Grievance Type", name, "description", description, update_modified=False)
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Grievance Type",
				"name": name,
				"description": description,
			}
		)
		doc.insert(ignore_permissions=True)
		inserted.append(name)

	return {"inserted": inserted, "existing": existing}


def ensure_employee_grievance_workflow() -> dict:
	if not frappe.db.exists("DocType", "Workflow"):
		return {"created": False, "reason": "Workflow doctype not found"}

	target_workflow_name = "Employee Grievance Workflow"
	supervisor_condition = (
		'frappe.session.user == "Administrator" or '
		'frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name") == doc.reports_to'
	)
	restricted_actions = {"Start Investigation", "Resolve", "Mark Invalid", "Reopen"}

	active_workflow_name = frappe.db.get_value(
		"Workflow", {"document_type": "Employee Grievance", "is_active": 1}, "name"
	)
	if active_workflow_name and active_workflow_name != target_workflow_name:
		return {"created": False, "reason": f"Active workflow already exists: {active_workflow_name}"}

	if frappe.db.exists("Workflow", target_workflow_name):
		workflow = frappe.get_doc("Workflow", target_workflow_name)
		workflow.is_active = 1
		workflow.override_status = 0
		workflow.workflow_state_field = "status"
		updated = False

		for state_row in workflow.states:
			if state_row.state in {"Resolved", "Invalid"} and str(state_row.doc_status) != "0":
				state_row.doc_status = "0"
				updated = True

		for transition_row in workflow.transitions:
			if transition_row.action in restricted_actions:
				if transition_row.allowed != "Employee":
					transition_row.allowed = "Employee"
					updated = True
				if (transition_row.condition or "").strip() != supervisor_condition:
					transition_row.condition = supervisor_condition
					updated = True
				if transition_row.allow_self_approval:
					transition_row.allow_self_approval = 0
					updated = True

		if not updated:
			return {"created": False, "updated": False, "reason": "Workflow already configured"}

		workflow.save(ignore_permissions=True)
		return {"created": False, "updated": True, "workflow": workflow.name}

	state_styles = {
		"Open": "Warning",
		"Investigated": "Info",
		"Resolved": "Success",
		"Invalid": "Danger",
	}
	for state_name, style in state_styles.items():
		if frappe.db.exists("Workflow State", state_name):
			continue
		state_doc = frappe.get_doc(
			{
				"doctype": "Workflow State",
				"workflow_state_name": state_name,
				"style": style,
			}
		)
		state_doc.insert(ignore_permissions=True)

	action_names = [
		"Start Investigation",
		"Resolve",
		"Mark Invalid",
		"Reopen",
	]
	for action_name in action_names:
		if frappe.db.exists("Workflow Action Master", action_name):
			continue
		action_doc = frappe.get_doc(
			{
				"doctype": "Workflow Action Master",
				"workflow_action_name": action_name,
			}
		)
		action_doc.insert(ignore_permissions=True)

	workflow = frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": target_workflow_name,
			"document_type": "Employee Grievance",
			"is_active": 1,
			"override_status": 0,
			"send_email_alert": 0,
			"workflow_state_field": "status",
			"states": [
				{
					"state": "Open",
					"doc_status": "0",
					"allow_edit": "Employee",
				},
				{
					"state": "Investigated",
					"doc_status": "0",
					"allow_edit": "Employee",
				},
				{
					"state": "Resolved",
					"doc_status": "0",
					"allow_edit": "Employee",
				},
				{
					"state": "Invalid",
					"doc_status": "0",
					"allow_edit": "Employee",
				},
			],
			"transitions": [
				{
					"state": "Open",
					"action": "Start Investigation",
					"next_state": "Investigated",
					"allowed": "Employee",
					"condition": supervisor_condition,
					"allow_self_approval": 0,
				},
				{
					"state": "Open",
					"action": "Mark Invalid",
					"next_state": "Invalid",
					"allowed": "Employee",
					"condition": supervisor_condition,
					"allow_self_approval": 0,
				},
				{
					"state": "Investigated",
					"action": "Resolve",
					"next_state": "Resolved",
					"allowed": "Employee",
					"condition": supervisor_condition,
					"allow_self_approval": 0,
				},
				{
					"state": "Investigated",
					"action": "Mark Invalid",
					"next_state": "Invalid",
					"allowed": "Employee",
					"condition": supervisor_condition,
					"allow_self_approval": 0,
				},
				{
					"state": "Resolved",
					"action": "Reopen",
					"next_state": "Open",
					"allowed": "Employee",
					"condition": supervisor_condition,
					"allow_self_approval": 0,
				},
				{
					"state": "Invalid",
					"action": "Reopen",
					"next_state": "Open",
					"allowed": "Employee",
					"condition": supervisor_condition,
					"allow_self_approval": 0,
				},
			],
		}
	)
	workflow.insert(ignore_permissions=True)
	return {"created": True, "workflow": workflow.name}


def sync_employee_grievance_reports_to() -> dict:
	updated = 0
	skipped = 0

	grievances = frappe.get_all(
		"Employee Grievance",
		fields=["name", "raised_by", "reports_to"],
		limit_page_length=0,
	)
	for grievance in grievances:
		if not grievance.raised_by:
			skipped += 1
			continue

		reports_to = frappe.db.get_value("Employee", grievance.raised_by, "reports_to")
		if not reports_to or reports_to == grievance.reports_to:
			continue

		frappe.db.set_value(
			"Employee Grievance",
			grievance.name,
			"reports_to",
			reports_to,
			update_modified=False,
		)
		updated += 1

	return {"updated": updated, "skipped": skipped}


@frappe.whitelist()
def get_expense_approval_details(employee: str) -> dict:
	expense_approver, department = frappe.get_cached_value(
		"Employee",
		employee,
		["expense_approver", "department"],
	)

	if not expense_approver and department:
		expense_approver = frappe.db.get_value(
			"Department Approver",
			{"parent": department, "parentfield": "expense_approvers", "idx": 1},
			"approver",
		)

	expense_approver_name = frappe.db.get_value("User", expense_approver, "full_name", cache=True)
	department_approvers = get_department_approvers(department, "expense_approvers")

	if expense_approver and expense_approver not in [approver.name for approver in department_approvers]:
		department_approvers.append({"name": expense_approver, "full_name": expense_approver_name})

	return dict(
		expense_approver=expense_approver,
		expense_approver_name=expense_approver_name,
		department_approvers=department_approvers,
		is_mandatory=frappe.db.get_single_value("HR Settings", "expense_approver_mandatory_in_expense_claim"),
	)


# Employee Advance
@frappe.whitelist()
def get_employee_advance_balance(employee: str) -> list[dict]:
	Advance = frappe.qb.DocType("Employee Advance")

	advances = (
		frappe.qb.from_(Advance)
		.select(
			Advance.name,
			Advance.employee,
			Advance.status,
			Advance.purpose,
			Advance.paid_amount,
			(Advance.paid_amount - (Advance.claimed_amount + Advance.return_amount)).as_("balance_amount"),
			Advance.posting_date,
			Advance.currency,
		)
		.where(
			(Advance.docstatus == 1)
			& (Advance.paid_amount)
			& (Advance.employee == employee)
			# don't need claimed & returned advances, only partly or completely paid ones
			& (Advance.status.isin(["Paid", "Unpaid"]))
		)
		.orderby(Advance.posting_date, order=Order.desc)
	).run(as_dict=True)

	return advances


@frappe.whitelist()
def get_advance_account(company: str) -> str | None:
	return frappe.db.get_value("Company", company, "default_employee_advance_account", cache=True)


# Company
@frappe.whitelist()
def get_company_currencies() -> dict:
	Company = frappe.qb.DocType("Company")
	Currency = frappe.qb.DocType("Currency")

	query = (
		frappe.qb.from_(Company)
		.join(Currency)
		.on(Company.default_currency == Currency.name)
		.select(
			Company.name,
			Company.default_currency,
			Currency.name.as_("currency"),
			Currency.symbol.as_("symbol"),
		)
	)

	companies = query.run(as_dict=True)
	return {company.name: (company.default_currency, company.symbol) for company in companies}


@frappe.whitelist()
def get_currency_symbols() -> dict:
	Currency = frappe.qb.DocType("Currency")

	currencies = (frappe.qb.from_(Currency).select(Currency.name, Currency.symbol)).run(as_dict=True)

	return {currency.name: currency.symbol or currency.name for currency in currencies}


@frappe.whitelist()
def get_company_cost_center_and_expense_account(company: str) -> dict:
	return frappe.db.get_value(
		"Company", company, ["cost_center", "default_expense_claim_payable_account"], as_dict=True
	)


# Form View APIs
@frappe.whitelist()
def get_doctype_fields(doctype: str) -> list[dict]:
	fields = frappe.get_meta(doctype).fields
	return [
		field
		for field in fields
		if field.fieldtype in SUPPORTED_FIELD_TYPES and field.fieldname != "amended_from"
	]


@frappe.whitelist()
def get_doctype_states(doctype: str) -> dict:
	states = frappe.get_meta(doctype).states
	return {state.title: state.color.lower() for state in states}


# File
@frappe.whitelist()
def get_attachments(dt: str, dn: str):
	from frappe.desk.form.load import get_attachments

	return get_attachments(dt, dn)


@frappe.whitelist()
def upload_base64_file(content, filename, dt=None, dn=None, fieldname=None):
	import base64
	import io
	from mimetypes import guess_type

	from PIL import Image, ImageOps

	from frappe.handler import ALLOWED_MIMETYPES

	decoded_content = base64.b64decode(content)
	content_type = guess_type(filename)[0]
	if content_type not in ALLOWED_MIMETYPES:
		frappe.throw(_("You can only upload JPG, PNG, PDF, TXT or Microsoft documents."))

	if content_type.startswith("image/jpeg"):
		# transpose the image according to the orientation tag, and remove the orientation data
		with Image.open(io.BytesIO(decoded_content)) as image:
			transpose_img = ImageOps.exif_transpose(image)
			# convert the image back to bytes
			file_content = io.BytesIO()
			transpose_img.save(file_content, format="JPEG")
			file_content = file_content.getvalue()
	else:
		file_content = decoded_content

	return frappe.get_doc(
		{
			"doctype": "File",
			"attached_to_doctype": dt,
			"attached_to_name": dn,
			"attached_to_field": fieldname,
			"folder": "Home",
			"file_name": filename,
			"content": file_content,
			"is_private": 1,
		}
	).insert()


@frappe.whitelist()
def delete_attachment(filename: str):
	frappe.delete_doc("File", filename)


@frappe.whitelist()
def download_salary_slip(name: str):
	import base64

	from frappe.utils.print_format import download_pdf

	default_print_format = frappe.get_meta("Salary Slip").default_print_format or "Standard"

	try:
		download_pdf("Salary Slip", name, format=default_print_format)
	except Exception:
		frappe.throw(_("Failed to download Salary Slip PDF"))

	base64content = base64.b64encode(frappe.local.response.filecontent)
	content_type = frappe.local.response.type

	return f"data:{content_type};base64," + base64content.decode("utf-8")


# Workflow
@frappe.whitelist()
def get_workflow(doctype: str) -> dict:
	workflow = get_workflow_name(doctype)
	if not workflow:
		return frappe._dict()
	return frappe.get_doc("Workflow", workflow)


def get_workflow_state_field(doctype: str) -> str | None:
	workflow_name = get_workflow_name(doctype)
	if not workflow_name:
		return None

	override_status, workflow_state_field = frappe.db.get_value(
		"Workflow",
		workflow_name,
		["override_status", "workflow_state_field"],
	)
	# NOTE: checkbox labelled 'Don't Override Status' is named override_status hence the inverted logic
	if not override_status:
		return workflow_state_field
	return None


def get_allowed_states_for_workflow(workflow: dict, user_id: str) -> list[str]:
	user_roles = frappe.get_roles(user_id)
	return [transition.state for transition in workflow.transitions if transition.allowed in user_roles]


# Permissions
@frappe.whitelist()
def get_permitted_fields_for_write(doctype: str) -> list[str]:
	return get_permitted_fields(doctype, permission_type="write")
