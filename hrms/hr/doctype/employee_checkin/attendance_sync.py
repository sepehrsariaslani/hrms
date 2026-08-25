from __future__ import annotations

from datetime import datetime, time

import frappe
from frappe import _
from frappe.utils import add_days, flt, get_datetime, getdate, nowdate


def _get_checkin_windows(target_date) -> tuple[datetime, datetime]:
	date_value = getdate(target_date)
	start_dt = datetime.combine(date_value, time(0, 0, 0))
	end_dt = datetime.combine(date_value, time(23, 59, 59))
	return start_dt, end_dt


def _get_daily_checkin_summary(target_date) -> list[frappe._dict]:
	start_dt, end_dt = _get_checkin_windows(target_date)
	return frappe.db.sql(
		"""
		select
			employee,
			min(time) as in_time,
			max(time) as out_time,
			count(*) as log_count
		from `tabEmployee Checkin`
		where
			employee is not null
			and time between %(start)s and %(end)s
		group by employee
		""",
		{"start": start_dt, "end": end_dt},
		as_dict=True,
	)


def _upsert_attendance_for_employee(target_date, checkin_summary: frappe._dict) -> str | None:
	employee = checkin_summary.employee
	if not employee:
		return None

	employee_status, company = frappe.get_cached_value("Employee", employee, ["status", "company"])
	if employee_status != "Active" or not company:
		return None

	in_time = get_datetime(checkin_summary.in_time) if checkin_summary.in_time else None
	out_time = get_datetime(checkin_summary.out_time) if checkin_summary.out_time else None
	working_hours = 0.0
	if in_time and out_time and out_time >= in_time:
		working_hours = flt((out_time - in_time).total_seconds() / 3600, precision=2)

	attendance_name = frappe.db.exists(
		"Attendance",
		{
			"employee": employee,
			"attendance_date": target_date,
			"docstatus": ("!=", 2),
		},
	)

	if attendance_name:
		attendance = frappe.get_doc("Attendance", attendance_name)
		if attendance.docstatus == 0:
			attendance.update(
				{
					"status": "Present",
					"in_time": in_time,
					"out_time": out_time,
					"working_hours": working_hours,
					"company": company,
				}
			)
			attendance.flags.ignore_validate = True
			attendance.save(ignore_permissions=True)
			attendance.submit()
			return attendance.name

		attendance.db_set(
			{
				"status": "Present",
				"in_time": in_time,
				"out_time": out_time,
				"working_hours": working_hours,
			},
			update_modified=False,
		)
		return attendance.name

	attendance = frappe.get_doc(
		{
			"doctype": "Attendance",
			"employee": employee,
			"attendance_date": target_date,
			"status": "Present",
			"company": company,
			"in_time": in_time,
			"out_time": out_time,
			"working_hours": working_hours,
		}
	)
	attendance.insert(ignore_permissions=True)
	attendance.submit()
	return attendance.name


def _link_checkins_with_attendance(target_date, employee: str, attendance_name: str) -> None:
	start_dt, end_dt = _get_checkin_windows(target_date)
	frappe.db.sql(
		"""
		update `tabEmployee Checkin`
		set attendance = %(attendance)s
		where employee = %(employee)s and time between %(start)s and %(end)s
		""",
		{
			"attendance": attendance_name,
			"employee": employee,
			"start": start_dt,
			"end": end_dt,
		},
	)


def sync_attendance_from_checkins(target_date: str | None = None) -> dict[str, int | str]:
	target_date = getdate(target_date) if target_date else add_days(getdate(nowdate()), -1)
	summaries = _get_daily_checkin_summary(target_date)
	created_or_updated = 0

	for summary in summaries:
		attendance_name = _upsert_attendance_for_employee(target_date, summary)
		if not attendance_name:
			continue
		created_or_updated += 1
		_link_checkins_with_attendance(target_date, summary.employee, attendance_name)

	return {
		"target_date": str(target_date),
		"processed_employees": len(summaries),
		"attendance_upserted": created_or_updated,
	}


@frappe.whitelist()
def sync_attendance_from_checkins_daily(target_date: str | None = None) -> dict[str, int | str]:
	if not frappe.has_permission("Attendance", "write"):
		frappe.throw(_("You do not have permission to sync attendance."))
	return sync_attendance_from_checkins(target_date=target_date)

