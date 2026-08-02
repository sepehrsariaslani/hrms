# Copyright (c) 2024, Iran Utilities
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, nowdate, flt
from datetime import datetime, date, timedelta

# Import Jalali helper
try:
    from hrms.utils.jalali_helper import gregorian_to_jalali, jalali_to_gregorian, JDATETIME_AVAILABLE
except ImportError:
    JDATETIME_AVAILABLE = False
    def gregorian_to_jalali(d, format_string=None):
        return str(d) if d else ""
    def jalali_to_gregorian(d, format_string=None):
        return str(d) if d else ""


def ensure_excluded_field_exists():
    """Auto-create custom_is_excluded Check field on Employee Checkin if it doesn't exist."""
    try:
        if not frappe.db.has_column("Employee Checkin", "custom_is_excluded"):
            if not frappe.db.exists("Custom Field", {"dt": "Employee Checkin", "fieldname": "custom_is_excluded"}):
                frappe.get_doc({
                    "doctype": "Custom Field",
                    "dt": "Employee Checkin",
                    "label": "حساب نشود",
                    "fieldname": "custom_is_excluded",
                    "fieldtype": "Check",
                    "default": "0",
                    "insert_after": "log_type",
                }).insert(ignore_permissions=True)
                frappe.db.commit()
    except Exception:
        pass


def execute(filters=None):
    filters = filters or {}
    ensure_excluded_field_exists()
    columns = get_columns()
    data = get_data(filters)
    
    # Add chart
    chart = get_chart_data(data, filters)
    
    # Add summary
    summary = get_summary(data)
    
    return columns, data, None, chart, summary


def get_columns():
    """Return columns for the report"""
    return [
        {
            "fieldname": "employee",
            "label": _("کارمند"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150
        },
        {
            "fieldname": "employee_name",
            "label": _("نام کارمند"),
            "fieldtype": "Data",
            "width": 130
        },
        {
            "fieldname": "work_date_shamsi",
            "label": _("تاریخ شمسی"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "work_date",
            "label": _("تاریخ میلادی"),
            "fieldtype": "Date",
            "width": 90
        },
        {
            "fieldname": "day_name",
            "label": _("روز"),
            "fieldtype": "Data",
            "width": 70
        },
        {
            "fieldname": "shift_type",
            "label": _("شیفت"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "standard_hours",
            "label": _("استاندارد"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 70
        },
        {
            "fieldname": "is_holiday",
            "label": _("تعطیل"),
            "fieldtype": "Check",
            "width": 60
        },
        {
            "fieldname": "holiday_description",
            "label": _("مناسبت تعطیلی"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "all_logs",
            "label": _("تمام لاگ‌ها"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "log_status",
            "label": _("وضعیت"),
            "fieldtype": "Data",
            "width": 140
        },
        {
            "fieldname": "actual_start",
            "label": _("ورود"),
            "fieldtype": "Data",
            "width": 70
        },
        {
            "fieldname": "actual_end",
            "label": _("خروج"),
            "fieldtype": "Data",
            "width": 70
        },
        {
            "fieldname": "presence_hours",
            "label": _("حضور"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 60
        },
        {
            "fieldname": "gross_working_hours",
            "label": _("ناخالص"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 60
        },
        {
            "fieldname": "break_hours",
            "label": _("استراحت"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 60
        },
        {
            "fieldname": "working_hours",
            "label": _("کارکرد"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 60
        },
        {
            "fieldname": "break_details",
            "label": _("جزئیات استراحت"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "time_off",
            "label": _("کسری"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 60
        },
        {
            "fieldname": "leave_hours",
            "label": _("مرخصی (ساعت)"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 80
        },
        {
            "fieldname": "leave_type",
            "label": _("نوع مرخصی"),
            "fieldtype": "Data",
            "width": 140
        },
        {
            "fieldname": "overtime",
            "label": _("اضافه‌کار"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 70
        },
        {
            "fieldname": "issue_flag",
            "label": _("✓"),
            "fieldtype": "Data",
            "width": 40
        }
    ]


def get_day_name_persian(weekday):
    """Convert weekday number to Persian day name"""
    days = {
        0: "دوشنبه",
        1: "سه‌شنبه",
        2: "چهارشنبه",
        3: "پنج‌شنبه",
        4: "جمعه",
        5: "شنبه",
        6: "یکشنبه"
    }
    return days.get(weekday, "")


def format_time(time_value):
    """Format time value to HH:MM string"""
    if time_value is None or str(time_value).strip() == "":
        return None
    
    try:
        # Handle timedelta objects
        if isinstance(time_value, timedelta):
            total_seconds = int(time_value.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours:02d}:{minutes:02d}"
        
        # Handle string
        time_str = str(time_value)
        
        # Remove microseconds if present
        if "." in time_str:
            time_str = time_str.split(".")[0]
        
        # Take only HH:MM
        parts = time_str.split(":")
        if len(parts) >= 2:
            return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
        
        return time_str[:5]
    except:
        return str(time_value)[:5] if time_value else None


def safe_time_text(time_value, fallback="-"):
    """Always return a printable time string."""
    return format_time(time_value) or fallback


def time_to_seconds(time_value):
    """Convert time value to seconds from midnight"""
    if time_value is None or str(time_value).strip() == "":
        return 0
    
    try:
        # Handle timedelta objects
        if isinstance(time_value, timedelta):
            return int(time_value.total_seconds())
        
        # Handle string
        time_str = str(time_value)
        
        # Remove microseconds if present
        if "." in time_str:
            time_str = time_str.split(".")[0]
        
        parts = time_str.split(":")
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
        seconds = int(parts[2]) if len(parts) > 2 else 0
        
        return hours * 3600 + minutes * 60 + seconds
    except:
        return 0


def normalize_noisy_checkins(checkins):
    """Remove obvious duplicate/noise logs from an ordered checkin list (in-memory only)."""
    cleaned = []
    for log in checkins or []:
        if cleaned:
            prev = cleaned[-1]
            same_timestamp = prev.get("full_time") == log.get("full_time")
            if same_timestamp:
                # Same second duplicate: keep first log, drop the duplicate tap.
                if prev.get("log_type") == log.get("log_type"):
                    continue

                # IN/OUT at the exact same time is usually a noisy double-tap.
                continue
        cleaned.append(log)

    return cleaned


def get_data(filters):
    """Get smart attendance data with proper handling of overnight shifts"""
    filters = filters or {}

    if not filters.get("from_date"):
        filters["from_date"] = add_days(nowdate(), -30)

    if not filters.get("to_date"):
        filters["to_date"] = nowdate()

    extended_from = add_days(filters.get("from_date"), -1)

    employees_to_include = get_employees_to_include(filters)

    if filters.get("employee") and not employees_to_include:
        return []

    employee_filter = ""
    employee_params = {}

    if employees_to_include:
        placeholders = []
        for idx, emp in enumerate(employees_to_include):
            key = f"employee_{idx}"
            employee_params[key] = emp
            placeholders.append(f"%({key})s")
        employee_filter = f"AND employee IN ({', '.join(placeholders)})"
    elif filters.get("company"):
        # اگر company انتخاب شده ولی کارمندی پیدا نشده
        return []

    has_excluded_col = frappe.db.has_column("Employee Checkin", "custom_is_excluded")
    excl_col = ",\n            IFNULL(custom_is_excluded, 0) AS is_excluded" if has_excluded_col else ",\n            0 AS is_excluded"

    checkin_query = """
        SELECT 
            name,
            employee,
            DATE(time) AS work_date,
            TIME(time) AS log_time,
            time AS full_time,
            log_type{excl_col}
        FROM `tabEmployee Checkin`
        WHERE DATE(time) >= %(extended_from)s
          AND DATE(time) <= %(to_date)s
          {employee_filter}
        ORDER BY employee, time
    """.format(excl_col=excl_col, employee_filter=employee_filter)

    params = {
        "extended_from": extended_from,
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        **employee_params,
    }

    raw_checkins = frappe.db.sql(checkin_query, params, as_dict=True)

    employee_checkins_raw = {}
    for c in raw_checkins:
        if c.employee not in employee_checkins_raw:
            employee_checkins_raw[c.employee] = []
        employee_checkins_raw[c.employee].append(c)

    employee_checkins = {}
    all_logs_lookup = {}
    for employee, checkins in employee_checkins_raw.items():
        # برای محاسبات فقط لاگ‌های غیر-مستثنی استفاده می‌شود
        non_excluded = [c for c in checkins if not c.get("is_excluded")]
        cleaned_logs = normalize_noisy_checkins(non_excluded)
        employee_checkins[employee] = cleaned_logs

        # برای نمایش همه لاگ‌ها (شامل مستثنی‌شده‌ها) نشان داده می‌شود
        for c in sorted(checkins, key=lambda x: str(x.get("full_time") or "")):
            key = (c.employee, c.work_date)
            if key not in all_logs_lookup:
                all_logs_lookup[key] = []
            all_logs_lookup[key].append({
                "name": c.name,
                "log_type": c.log_type,
                "log_time": c.log_time,
                "is_excluded": bool(c.get("is_excluded", 0))
            })

    used_overnight_logs = set()
    work_sessions = {}

    for employee, checkins in employee_checkins.items():
        i = 0
        while i < len(checkins):
            log = checkins[i]

            if log.log_type == "IN":
                in_log = log
                out_log = None

                j = i + 1
                while j < len(checkins):
                    if checkins[j].log_type == "OUT":
                        out_log = checkins[j]
                        break
                    elif checkins[j].log_type == "IN":
                        break
                    j += 1

                work_date = in_log.work_date
                key = (employee, work_date)

                if key not in work_sessions:
                    work_sessions[key] = {
                        "pairs": [],
                        "unpaired_ins": [],
                        "unpaired_outs": [],
                        "first_in": None,
                        "first_in_name": None,
                        "last_out": None,
                        "last_out_name": None
                    }

                if out_log:
                    in_datetime = in_log.full_time
                    out_datetime = out_log.full_time

                    if isinstance(in_datetime, str):
                        in_datetime = datetime.strptime(in_datetime, "%Y-%m-%d %H:%M:%S")
                    if isinstance(out_datetime, str):
                        out_datetime = datetime.strptime(out_datetime, "%Y-%m-%d %H:%M:%S")

                    duration_seconds = (out_datetime - in_datetime).total_seconds()

                    work_sessions[key]["pairs"].append({
                        "in_time": in_log.log_time,
                        "in_name": in_log.name,
                        "in_datetime": in_datetime,
                        "out_time": out_log.log_time,
                        "out_name": out_log.name,
                        "out_datetime": out_datetime,
                        "out_date": out_log.work_date,
                        "duration_seconds": max(0, duration_seconds)
                    })

                    if not work_sessions[key]["first_in"]:
                        work_sessions[key]["first_in"] = in_log.log_time
                        work_sessions[key]["first_in_name"] = in_log.name
                    work_sessions[key]["last_out"] = out_log.log_time
                    work_sessions[key]["last_out_name"] = out_log.name
                    work_sessions[key]["last_out_date"] = out_log.work_date

                    i = j + 1
                else:
                    work_sessions[key]["unpaired_ins"].append({
                        "time": in_log.log_time,
                        "name": in_log.name
                    })
                    if not work_sessions[key]["first_in"]:
                        work_sessions[key]["first_in"] = in_log.log_time
                        work_sessions[key]["first_in_name"] = in_log.name
                    i += 1

            elif log.log_type == "OUT":
                work_date = log.work_date
                key = (employee, work_date)

                out_hour = time_to_seconds(log.log_time) // 3600

                if out_hour < 8:
                    prev_date = add_days(work_date, -1)
                    prev_key = (employee, prev_date)

                    if prev_key in work_sessions and work_sessions[prev_key]["unpaired_ins"]:
                        unpaired_in = work_sessions[prev_key]["unpaired_ins"].pop(0)

                        in_datetime = datetime.combine(prev_date, datetime.min.time())
                        in_seconds = time_to_seconds(unpaired_in["time"])
                        in_datetime = in_datetime + timedelta(seconds=in_seconds)

                        out_datetime = datetime.combine(work_date, datetime.min.time())
                        out_seconds = time_to_seconds(log.log_time)
                        out_datetime = out_datetime + timedelta(seconds=out_seconds)

                        duration_seconds = (out_datetime - in_datetime).total_seconds()

                        work_sessions[prev_key]["pairs"].append({
                            "in_time": unpaired_in["time"],
                            "in_name": unpaired_in["name"],
                            "in_datetime": in_datetime,
                            "out_time": log.log_time,
                            "out_name": log.name,
                            "out_datetime": out_datetime,
                            "out_date": work_date,
                            "duration_seconds": max(0, duration_seconds)
                        })

                        used_overnight_logs.add(log.name)

                        work_sessions[prev_key]["last_out"] = log.log_time
                        work_sessions[prev_key]["last_out_name"] = log.name
                        work_sessions[prev_key]["last_out_date"] = work_date

                        i += 1
                        continue

                if key not in work_sessions:
                    work_sessions[key] = {
                        "pairs": [],
                        "unpaired_ins": [],
                        "unpaired_outs": [],
                        "first_in": None,
                        "first_in_name": None,
                        "last_out": None,
                        "last_out_name": None
                    }
                work_sessions[key]["unpaired_outs"].append({
                    "time": log.log_time,
                    "name": log.name
                })
                i += 1
            else:
                i += 1

    # ساعت کاری استاندارد را از HR Settings می‌خوانیم
    hr_standard_hours = flt(frappe.db.get_single_value("HR Settings", "standard_working_hours") or 7.67)

    employee_names = {}
    employees_in_checkins = list(set([c.employee for c in raw_checkins]))

    source_employees = list(set((employees_to_include or []) + employees_in_checkins))
    if source_employees:
        employee_rows = frappe.get_all(
            "Employee",
            filters={"name": ["in", source_employees]},
            fields=["name", "employee_name"],
        )
        employee_names = {row.name: row.employee_name or row.name for row in employee_rows}

    employee_break_assignments = get_employee_break_assignments(filters)
    shifts = get_employee_shifts(filters)
    holidays = get_holidays(filters)
    attendance_lookup = get_attendance_map(filters)
    leave_lookup = get_leave_map(filters)

    data = []
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))

    if filters.get("employee"):
        employees_to_report = [filters.get("employee")]
    elif employees_to_include:
        employees_to_report = list(employees_to_include)
    else:
        employees_to_report = list(set(employees_in_checkins))
        for emp in shifts.keys():
            if emp not in employees_to_report:
                employees_to_report.append(emp)

    missing_names = [emp for emp in employees_to_report if emp not in employee_names]
    if missing_names:
        extra_rows = frappe.get_all(
            "Employee",
            filters={"name": ["in", missing_names]},
            fields=["name", "employee_name"],
        )
        for row in extra_rows:
            employee_names[row.name] = row.employee_name or row.name

    for employee in sorted(employees_to_report):
        current_date = from_date
        while current_date <= to_date:
            key = (employee, current_date)
            session = work_sessions.get(key)
            all_logs = all_logs_lookup.get(key, [])
            shift = shifts.get(employee, {})
            break_windows_for_day = get_break_windows_for_date(employee_break_assignments, employee, current_date)
            holiday_info = holidays.get((employee, current_date), {})
            # A day is a holiday only if it is present in the employee's assigned
            # Holiday List. Do NOT hardcode Friday/Thursday — the assigned list is
            # the single source of truth for what counts as a holiday.
            is_holiday = bool(holiday_info)
            weekday = current_date.weekday()

            # Standard working hours for a normal working day always come from the
            # "standard_working_hours" field in HR Settings. Holidays are 0.
            standard_hours = 0 if is_holiday else hr_standard_hours

            all_logs_str = ""
            all_logs_json = []
            log_issues = []

            if all_logs:
                log_parts = []
                in_count = 0
                out_count = 0

                for log in all_logs:
                    if log["name"] in used_overnight_logs:
                        continue

                    is_excl = log.get("is_excluded", False)
                    time_text = safe_time_text(log.get("log_time"))
                    log_type_icon = "⬇️" if log["log_type"] == "IN" else "⬆️"
                    display_text = f"🚫{time_text}" if is_excl else f"{log_type_icon}{time_text}"
                    log_parts.append({
                        "display": display_text,
                        "name": log["name"],
                        "log_type": log["log_type"],
                        "time": time_text,
                        "is_excluded": is_excl
                    })
                    all_logs_json.append({
                        "name": log["name"],
                        "log_type": log["log_type"],
                        "time": time_text,
                        "is_excluded": is_excl
                    })

                    if not is_excl:
                        if log["log_type"] == "IN":
                            in_count += 1
                        else:
                            out_count += 1

                all_logs_str = " | ".join([p["display"] for p in log_parts])

                if in_count != out_count:
                    log_issues.append(f"{in_count} ورود، {out_count} خروج")

            # approved leave for this employee/day (if any)
            leave_info = leave_lookup.get((employee, current_date))

            row = {
                "employee": employee,
                "employee_name": employee_names.get(employee, employee),
                "work_date": current_date,
                "work_date_shamsi": gregorian_to_jalali(current_date, "jYYYY/jMM/jDD"),
                "day_name": get_day_name_persian(weekday),
                "shift_type": shift.get("shift_type", ""),
                "standard_hours": standard_hours,
                "is_holiday": 1 if is_holiday else 0,
                "holiday_description": holiday_info.get("description") or "",
                "all_logs": all_logs_str,
                "all_logs_json": all_logs_json,
                "log_status": "",
                "actual_start": None,
                "actual_end": None,
                "first_in_name": None,
                "last_out_name": None,
                "presence_hours": 0,
                "gross_working_hours": 0,
                "break_hours": 0,
                "working_hours": 0,
                "break_details": "",
                "time_off": 0 if is_holiday else standard_hours,
                "leave_hours": flt(leave_info["hours"], 2) if leave_info else 0,
                "leave_type": leave_info["leave_type"] if leave_info else "",
                "is_compensatory_leave": bool(leave_info and leave_info.get("is_compensatory")),
                "leave_application_names": leave_info["names"] if leave_info else [],
                "leave_application_name": (leave_info["names"] or [None])[0] if leave_info else None,
                "overtime": 0,
                "holiday_work": 0,
                "late_minutes": 0,
                "early_exit_minutes": 0,
                "night_hours": 0,
                "issue_flag": "",
                "has_issue": False,
                "can_mark_attendance": False,
                "attendance_status": None,
                "attendance_name": None,
            }

            if session:
                pairs = session["pairs"]
                unpaired_ins = session["unpaired_ins"]
                unpaired_outs = session["unpaired_outs"]

                total_presence_seconds = sum(p["duration_seconds"] for p in pairs)

                if session["first_in"]:
                    row["actual_start"] = format_time(session["first_in"])
                    row["first_in_name"] = session["first_in_name"]

                if session["last_out"]:
                    last_out_date = session.get("last_out_date")
                    last_out_text = safe_time_text(session["last_out"])
                    if last_out_date and last_out_date != current_date:
                        row["actual_end"] = f"{last_out_text}(+1)" if last_out_text != "-" else "-"
                    else:
                        row["actual_end"] = last_out_text
                    row["last_out_name"] = session["last_out_name"]

                if pairs and not unpaired_ins and not unpaired_outs:
                    row["log_status"] = "✅ کامل"
                    row["issue_flag"] = "✅"
                elif unpaired_ins and not unpaired_outs:
                    unpaired_times = ", ".join([safe_time_text(u.get("time")) for u in unpaired_ins])
                    row["log_status"] = f"🟡 خروج ندارد ({unpaired_times})"
                    row["issue_flag"] = "🟡"
                    row["has_issue"] = True
                elif unpaired_outs and not unpaired_ins:
                    unpaired_times = ", ".join([safe_time_text(u.get("time")) for u in unpaired_outs])
                    row["log_status"] = f"🟡 ورود ندارد ({unpaired_times})"
                    row["issue_flag"] = "🟡"
                    row["has_issue"] = True
                elif unpaired_ins and unpaired_outs:
                    row["log_status"] = f"🟡 ناقص (ورود {len(unpaired_ins)}, خروج {len(unpaired_outs)})"
                    row["issue_flag"] = "🟡"
                    row["has_issue"] = True
                else:
                    row["log_status"] = "🟡 ناقص"
                    row["issue_flag"] = "🟡"
                    row["has_issue"] = True

                presence_hours = total_presence_seconds / 3600

                break_hours = 0
                break_details_parts = []
                if pairs:
                    first_in_seconds = time_to_seconds(session["first_in"])
                    last_out_seconds = time_to_seconds(session["last_out"])
                    if session.get("last_out_date") and session["last_out_date"] != current_date:
                        last_out_seconds += 24 * 3600
                    break_hours = calculate_break_hours(
                        first_in_seconds, last_out_seconds, break_windows_for_day
                    )

                    # Build per-break detail strings for display
                    for bw in break_windows_for_day:
                        bs = bw.get("start", 0)
                        be = bw.get("end", 0)
                        if be <= bs:
                            be += 24 * 3600
                        overlap = max(0, min(last_out_seconds, be) - max(first_in_seconds, bs))
                        if overlap <= 0:
                            overlap = max(0, min(last_out_seconds, be + 24 * 3600) - max(first_in_seconds, bs + 24 * 3600))
                        if overlap > 0:
                            ded_sec = max(0, int(bw.get("deduction_seconds") or 0))
                            effective = min(overlap, ded_sec or overlap)
                            break_details_parts.append(
                                f"{bw.get('name', '?')}: {int(bs//3600):02d}:{int((bs%3600)//60):02d}-{int(be//3600):02d}:{int((be%3600)//60):02d} → {flt(effective/3600, 1)}h"
                            )

                working_hours = max(0, presence_hours - break_hours)

                row["presence_hours"] = flt(presence_hours, 2)
                row["gross_working_hours"] = flt(presence_hours, 2)
                row["break_hours"] = flt(break_hours, 2)
                row["working_hours"] = flt(working_hours, 2)
                row["break_details"] = " | ".join(break_details_parts) if break_details_parts else ""

                # Late entry / early exit based on the assigned shift.
                if session["first_in"] and shift.get("start_time"):
                    late_min = (
                        time_to_seconds(session["first_in"]) - time_to_seconds(shift.get("start_time"))
                    ) / 60
                    row["late_minutes"] = flt(max(late_min, 0), 2)

                if session["last_out"] and shift.get("end_time"):
                    last_out_seconds = time_to_seconds(session["last_out"])
                    if session.get("last_out_date") and session["last_out_date"] != current_date:
                        last_out_seconds += 24 * 3600
                    shift_end_seconds = time_to_seconds(shift.get("end_time"))
                    if shift_end_seconds <= time_to_seconds(shift.get("start_time")):
                        shift_end_seconds += 24 * 3600
                    early_min = (shift_end_seconds - last_out_seconds) / 60
                    row["early_exit_minutes"] = flt(max(early_min, 0), 2)

                # Night hours = intersection of the presence span with the night window.
                if session["first_in"] and session["last_out"]:
                    first_in_seconds = time_to_seconds(session["first_in"])
                    last_out_seconds = time_to_seconds(session["last_out"])
                    if session.get("last_out_date") and session["last_out_date"] != current_date:
                        last_out_seconds += 24 * 3600
                    row["night_hours"] = flt(
                        calculate_night_hours(first_in_seconds, last_out_seconds), 2
                    )

                if is_holiday:
                    row["time_off"] = 0
                    row["overtime"] = flt(working_hours, 2)
                    row["holiday_work"] = flt(working_hours, 2)
                elif row.get("is_compensatory_leave") and row.get("leave_hours"):
                    # Compensatory (جبرانی) leave special semantics:
                    # the leave hours replace the required working hours for that day,
                    # so any presence beyond the *remaining* shift is overtime.
                    #  - full-day comp leave (>= standard) -> all presence is overtime
                    #  - partial comp leave -> presence fills remaining shift as normal
                    #    work, and anything beyond it is overtime.
                    effective_standard = max(standard_hours - flt(row.get("leave_hours")), 0)
                    row["time_off"] = 0
                    row["overtime"] = flt(max(working_hours - effective_standard, 0), 2)
                else:
                    if working_hours >= standard_hours:
                        row["time_off"] = 0
                        row["overtime"] = flt(working_hours - standard_hours, 2)
                    else:
                        row["time_off"] = flt(standard_hours - working_hours, 2)
                        row["overtime"] = 0

                # if the employee has an approved leave for this day, that day is
                # no longer counted as shortage (کسر کار) — it is a leave day.
                if row.get("leave_hours"):
                    row["time_off"] = 0

            elif all_logs and len(all_logs) == 1:
                single_log = all_logs[0]
                log_hour = time_to_seconds(single_log["log_time"]) // 3600
                log_time_text = safe_time_text(single_log.get("log_time"))

                if single_log["log_type"] == "IN":
                    if log_hour >= 15:
                        row["log_status"] = f"🟠 احتمالاً خروج ({log_time_text})"
                        row["actual_end"] = log_time_text
                        row["last_out_name"] = single_log["name"]
                    else:
                        row["log_status"] = f"🟡 خروج ندارد ({log_time_text})"
                        row["actual_start"] = log_time_text
                        row["first_in_name"] = single_log["name"]
                else:
                    if log_hour < 12:
                        row["log_status"] = f"🟠 احتمالاً ورود ({log_time_text})"
                        row["actual_start"] = log_time_text
                        row["first_in_name"] = single_log["name"]
                    else:
                        row["log_status"] = f"🟡 ورود ندارد ({log_time_text})"
                        row["actual_end"] = log_time_text
                        row["last_out_name"] = single_log["name"]

                row["issue_flag"] = "🟡"
                row["has_issue"] = True

            else:
                if not is_holiday:
                    # if the employee has an approved leave for this day, treat the
                    # whole day as leave (no shortage) and show the leave type
                    if row.get("leave_hours"):
                        row["time_off"] = 0
                        row["log_status"] = f"🟣 مرخصی ثبت شده ({row['leave_type']})" if row.get("leave_type") else "🟣 مرخصی ثبت شده"
                        row["issue_flag"] = ""
                        row["has_issue"] = False
                    else:
                        row["can_mark_attendance"] = True
                        existing_attendance = attendance_lookup.get((employee, current_date))
                        if existing_attendance:
                            row["attendance_status"] = existing_attendance.get("status")
                            row["attendance_name"] = existing_attendance.get("name")

                            if row["attendance_status"] == "On Leave":
                                row["log_status"] = "🟣 مرخصی ثبت شده"
                            elif row["attendance_status"] == "Absent":
                                row["log_status"] = "⚫ غیبت ثبت شده"
                            else:
                                row["log_status"] = f"ℹ️ {row['attendance_status']}"
                        else:
                            row["log_status"] = "🔴 غیبت / بدون لاگ"

                        row["issue_flag"] = ""
                        row["has_issue"] = False
                else:
                    row["log_status"] = "تعطیل"
                    row["issue_flag"] = ""

            if filters.get("only_issues"):
                if row["has_issue"]:
                    data.append(row)
            else:
                data.append(row)

            current_date = add_days(current_date, 1)

    return data

def get_employee_condition(filters, table_alias=None, fieldname="employee"):
    """
    Build reusable employee/company SQL condition.
    If table_alias is provided, field becomes `alias.fieldname`.
    Company filter is applied through tabEmployee join-compatible condition.
    """
    conditions = []
    params = {}

    field_ref = f"{table_alias}.{fieldname}" if table_alias else fieldname

    if filters.get("employee"):
        conditions.append(f"{field_ref} = %(employee)s")
        params["employee"] = filters.get("employee")

    elif filters.get("employees"):
        employee_list = [e.strip() for e in (filters.get("employees") or "").split(",") if e.strip()]
        if employee_list:
            placeholders = []
            for idx, emp in enumerate(employee_list):
                key = f"employee_{idx}"
                params[key] = emp
                placeholders.append(f"%({key})s")
            conditions.append(f"{field_ref} IN ({', '.join(placeholders)})")

    return conditions, params

def get_employees_to_include(filters):

    employee_filters = {
        "status": "Active"
    }

    if filters.get("employee"):
        employee_filters["name"] = filters.get("employee")

    if filters.get("company"):
        employee_filters["company"] = filters.get("company")

    frappe.errprint(employee_filters)

    employees = frappe.get_all(
        "Employee",
        filters=employee_filters,
        pluck="name"
    )

    frappe.errprint(employees)

    return employees

def get_employee_break_assignments(filters):
    """Get active break assignments for selected employee scope."""
    assignment_map = {}
    employees_to_include = get_employees_to_include(filters)

    if filters.get("company") and not employees_to_include:
        return assignment_map

    employee_filter = ""
    params = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
    }

    if employees_to_include:
        placeholders = []
        for idx, emp in enumerate(employees_to_include):
            key = f"employee_{idx}"
            params[key] = emp
            placeholders.append(f"%({key})s")
        employee_filter = f"AND ba.employee IN ({', '.join(placeholders)})"

    has_calculation_type = frappe.db.has_column("Break Hours", "calculation_type")
    has_fixed_rules = frappe.db.exists("DocType", "Break Deduction Rule")
    calculation_type_select = "bh.calculation_type" if has_calculation_type else "'Time Window' AS calculation_type"

    rows = frappe.db.sql(
        f"""
        SELECT
            bh.name AS break_hours_name,
            ba.employee,
            ba.from_date,
            ba.to_date,
            bh.break_start,
            bh.break_end,
            bh.deduction_hours,
            {calculation_type_select}
        FROM `tabBreak Assignment` ba
        JOIN `tabBreak Hours` bh ON bh.name = ba.break_hours
        WHERE ba.docstatus = 1
          AND ba.status = 'Active'
          AND bh.is_active = 1
          AND ba.from_date <= %(to_date)s
          AND (ba.to_date IS NULL OR ba.to_date >= %(from_date)s)
          {employee_filter}
        ORDER BY ba.employee, ba.from_date
        """.format(employee_filter=employee_filter),
        params,
        as_dict=True,
    )

    break_names = [row.break_hours_name for row in rows if row.get("break_hours_name")]
    fixed_rules = {}
    if has_fixed_rules and break_names:
        rule_rows = frappe.get_all(
            "Break Deduction Rule",
            filters={"parent": ["in", break_names], "parenttype": "Break Hours"},
            fields=["parent", "minimum_work_hours", "deduction_hours", "description"],
            order_by="parent asc, minimum_work_hours asc",
            limit_page_length=0,
        )
        for rule in rule_rows:
            fixed_rules.setdefault(rule.parent, []).append(
                {
                    "minimum_work_hours": flt(rule.minimum_work_hours),
                    "deduction_hours": flt(rule.deduction_hours),
                    "description": rule.description or "",
                }
            )

    for row in rows:
        calculation_type = row.get("calculation_type") or "Time Window"
        if calculation_type == "Fixed by Worked Hours":
            thresholds = fixed_rules.get(row.break_hours_name, [])
            if not thresholds:
                continue
            assignment_map.setdefault(row.employee, []).append(
                {
                    "from_date": getdate(row.from_date),
                    "to_date": getdate(row.to_date) if row.to_date else None,
                    "calculation_type": calculation_type,
                    "thresholds": thresholds,
                }
            )
            continue

        assignment_map.setdefault(row.employee, []).append(
            {
                "from_date": getdate(row.from_date),
                "to_date": getdate(row.to_date) if row.to_date else None,
                "calculation_type": "Time Window",
                "start": time_to_seconds(row.break_start),
                "end": time_to_seconds(row.break_end),
                "deduction_seconds": int(flt(row.deduction_hours) * 3600),
            }
        )

    return assignment_map

def get_break_windows_for_date(assignment_map, employee, work_date):
    """Return break windows that are active for employee on a specific date."""
    windows = []
    for row in assignment_map.get(employee, []):
        if row["from_date"] <= work_date and (row["to_date"] is None or row["to_date"] >= work_date):
            if row.get("calculation_type") == "Fixed by Worked Hours":
                windows.append(
                    {
                        "calculation_type": "Fixed by Worked Hours",
                        "thresholds": row.get("thresholds") or [],
                    }
                )
            else:
                windows.append(
                    {
                        "calculation_type": "Time Window",
                        "start": row["start"],
                        "end": row["end"],
                        "deduction_seconds": row["deduction_seconds"],
                    }
                )
    return windows


def calculate_break_hours(start_seconds, end_seconds, break_windows=None):
    """
    Calculate deducted break hours using partial overlap.

    Deduction for each break = min(overlap_with_work_span, configured_deduction_seconds).
    """
    if start_seconds is None or end_seconds is None or not break_windows:
        return 0

    if end_seconds <= start_seconds:
        end_seconds += 24 * 3600

    break_seconds = 0
    span_seconds = max(0, end_seconds - start_seconds)

    for window in break_windows:
        if window.get("calculation_type") == "Fixed by Worked Hours":
            span_hours = span_seconds / 3600
            matching_rules = [
                rule for rule in window.get("thresholds", [])
                if span_hours >= flt(rule.get("minimum_work_hours"))
            ]
            if not matching_rules:
                continue
            selected = max(matching_rules, key=lambda rule: flt(rule.get("minimum_work_hours")))
            break_seconds += int(flt(selected.get("deduction_hours")) * 3600)
            continue

        break_start = window.get("start")
        break_end = window.get("end")
        deduction_seconds = max(0, int(window.get("deduction_seconds") or 0))

        if break_start is None or break_end is None:
            continue

        if break_end <= break_start:
            break_end += 24 * 3600

        # Evaluate base day window and, when needed, its next-day projection.
        for offset in (0, 24 * 3600):
            shifted_start = break_start + offset
            shifted_end = break_end + offset
            overlap = max(0, min(end_seconds, shifted_end) - max(start_seconds, shifted_start))
            if overlap <= 0:
                continue

            effective_deduction = min(overlap, deduction_seconds or overlap)
            break_seconds += effective_deduction
            break

    break_seconds = min(break_seconds, span_seconds)
    return break_seconds / 3600


NIGHT_WINDOW_START = 22 * 3600  # 22:00
NIGHT_WINDOW_END = 6 * 3600  # 06:00


def calculate_night_hours(start_seconds, end_seconds, night_start=NIGHT_WINDOW_START, night_end=NIGHT_WINDOW_END):
    """Return the hours of the presence span that fall inside the night window.

    The night window may wrap past midnight (e.g. 22:00 -> 06:00), so the span
    is evaluated against both the base day window and its next-day projection.
    """
    if start_seconds is None or end_seconds is None:
        return 0

    if end_seconds <= start_seconds:
        end_seconds += 24 * 3600

    night_seconds = 0
    span_seconds = max(0, end_seconds - start_seconds)

    for offset in (0, 24 * 3600):
        window_start = night_start + offset
        window_end = night_end + offset
        overlap = max(0, min(end_seconds, window_end) - max(start_seconds, window_start))
        if overlap > 0:
            night_seconds += overlap

    return min(night_seconds, span_seconds) / 3600


def get_chart_data(data, filters):
    """Generate chart data for the report"""
    if not data:
        return None
    
    # Group by date
    date_totals = {}
    for row in data:
        work_date = str(row.get("work_date"))
        if work_date not in date_totals:
            date_totals[work_date] = {
                "working_hours": 0,
                "time_off": 0,
                "overtime": 0
            }
        date_totals[work_date]["working_hours"] += flt(row.get("working_hours", 0))
        date_totals[work_date]["time_off"] += flt(row.get("time_off", 0))
        date_totals[work_date]["overtime"] += flt(row.get("overtime", 0))
    
    # Sort by date
    sorted_dates = sorted(date_totals.keys())
    
    # Prepare chart data
    labels = []
    working_data = []
    overtime_data = []
    
    for d in sorted_dates[-14:]:
        labels.append(d[-5:])
        working_data.append(round(date_totals[d]["working_hours"], 1))
        overtime_data.append(round(date_totals[d]["overtime"], 1))
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("ساعت کاری"),
                    "values": working_data
                },
                {
                    "name": _("اضافه‌کار"),
                    "values": overtime_data
                }
            ]
        },
        "type": "bar",
        "colors": ["#4299e1", "#48bb78"]
    }


def get_summary(data):
    """Generate summary data for the report"""
    if not data:
        return []

    total_working = sum(flt(row.get("working_hours", 0)) for row in data)
    total_presence = sum(flt(row.get("presence_hours", 0)) for row in data)
    total_break = sum(flt(row.get("break_hours", 0)) for row in data)
    total_time_off = sum(flt(row.get("time_off", 0)) for row in data)
    total_leave = sum(flt(row.get("leave_hours", 0)) for row in data)
    total_overtime = sum(flt(row.get("overtime", 0)) for row in data)
    total_standard = sum(flt(row.get("standard_hours", 0)) for row in data)

    days_worked = len([r for r in data if flt(r.get("working_hours", 0)) > 0])
    days_with_issues = len([r for r in data if r.get("has_issue", False)])
    total_days = len(data)

    return [
        {
            "value": days_worked,
            "label": _("روز کارکرد"),
            "datatype": "Int"
        },
        {
            "value": total_days,
            "label": _("کل روز"),
            "datatype": "Int"
        },
        {
            "value": days_with_issues,
            "label": _("روز مشکل‌دار"),
            "datatype": "Int",
            "indicator": "red" if days_with_issues > 0 else ""
        },
        {
            "value": round(total_working, 1),
            "label": _("ساعت کاری"),
            "datatype": "Float"
        },
        {
            "value": round(total_overtime, 1),
            "label": _("اضافه‌کار"),
            "datatype": "Float",
            "indicator": "green"
        },
        {
            "value": round(total_time_off, 1),
            "label": _("کسری"),
            "datatype": "Float",
            "indicator": "red"
        },
        {
            "value": round(total_leave, 1),
            "label": _("مرخصی (ساعت)"),
            "datatype": "Float",
            "indicator": "purple"
        }
    ]


def get_employee_shifts(filters):
    """Get shift assignments for employees"""
    shifts = {}
    employees_to_include = get_employees_to_include(filters)

    if filters.get("company") and not employees_to_include:
        return shifts

    employee_filter = ""
    params = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
    }

    if employees_to_include:
        placeholders = []
        for idx, emp in enumerate(employees_to_include):
            key = f"employee_{idx}"
            params[key] = emp
            placeholders.append(f"%({key})s")
        employee_filter = f"AND sa.employee IN ({', '.join(placeholders)})"

    shift_query = """
        SELECT 
            sa.employee,
            st.name AS shift_type,
            st.start_time,
            st.end_time,
            (
                CASE
                    WHEN TIME(st.end_time) > TIME(st.start_time)
                        THEN TIME_TO_SEC(TIMEDIFF(st.end_time, st.start_time))
                    ELSE (86400 - TIME_TO_SEC(st.start_time) + TIME_TO_SEC(st.end_time))
                END
            ) / 3600 AS shift_duration
        FROM `tabShift Assignment` sa
        JOIN `tabShift Type` st ON sa.shift_type = st.name
        WHERE sa.docstatus = 1
          AND sa.start_date <= %(to_date)s
          AND (sa.end_date IS NULL OR sa.end_date >= %(from_date)s)
          {employee_filter}
    """.format(employee_filter=employee_filter)

    shift_data = frappe.db.sql(shift_query, params, as_dict=True)

    for s in shift_data:
        shifts[s.employee] = {
            "shift_type": s.shift_type,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "shift_duration": s.shift_duration,
        }

    return shifts

def get_holidays(filters):
    """Get holidays for employees"""
    holidays = {}
    employees_to_include = get_employees_to_include(filters)

    if filters.get("company") and not employees_to_include:
        return holidays

    employee_filter = ""
    params = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
    }

    if employees_to_include:
        placeholders = []
        for idx, emp in enumerate(employees_to_include):
            key = f"employee_{idx}"
            params[key] = emp
            placeholders.append(f"%({key})s")
        employee_filter = f"AND e.name IN ({', '.join(placeholders)})"

    holiday_query = """
        SELECT
            h.holiday_date,
            h.description,
            h.weekly_off,
            e.name AS employee
        FROM `tabHoliday` h
        JOIN `tabHoliday List` hl ON hl.name = h.parent
        JOIN `tabEmployee` e ON e.holiday_list = hl.name
        WHERE h.holiday_date >= %(from_date)s
          AND h.holiday_date <= %(to_date)s
          {employee_filter}
    """.format(employee_filter=employee_filter)

    holiday_data = frappe.db.sql(holiday_query, params, as_dict=True)

    for h in holiday_data:
        holidays[(h.employee, h.holiday_date)] = {
            "description": h.description or "",
            "weekly_off": int(h.weekly_off or 0),
        }

    return holidays

def get_leave_map(filters):
    """Get approved Leave Applications for the period keyed by (employee, leave_date).

    Returns { (employee, date): {"hours": float, "leave_type": str, "names": [..]} }.
    Hourly leaves contribute their hours; daily leaves contribute standard_working_hours.
    """
    leave_map = {}
    employees_to_include = get_employees_to_include(filters)

    if filters.get("company") and not employees_to_include:
        return leave_map

    employee_filter = ""
    params = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
    }

    if employees_to_include:
        placeholders = []
        for idx, emp in enumerate(employees_to_include):
            key = f"employee_{idx}"
            params[key] = emp
            placeholders.append(f"%({key})s")
        employee_filter = f"AND employee IN ({', '.join(placeholders)})"

    standard_hours = flt(frappe.db.get_single_value("HR Settings", "standard_working_hours")) or 8

    rows = frappe.db.sql(
        f"""
        SELECT
            name, employee, leave_type, from_date, to_date,
            leave_duration_mode, total_leave_days, total_leave_hours
        FROM `tabLeave Application`
        WHERE docstatus = 1
          AND status = 'Approved'
          AND from_date <= %(to_date)s
          AND to_date >= %(from_date)s
          {employee_filter}
        """,
        params,
        as_dict=True,
    )

    for app in rows:
        leave_type = app["leave_type"]
        # check whether this leave type is compensatory (جبرانی) — it has special
        # overtime semantics (presence on a comp-leave day counts as overtime)
        is_compensatory = 0
        lt_doc = frappe.db.get_value(
            "Leave Type", leave_type, "is_compensatory", cache=True
        )
        if lt_doc:
            is_compensatory = 1

        if app.get("leave_duration_mode") == "ساعتی":
            hours = flt(app.get("total_leave_hours"))
            dates = [app["from_date"]]
        else:
            hours = flt(app.get("total_leave_days")) * standard_hours
            # spread across the leave days (from_date .. to_date)
            dates = [
                getdate(app["from_date"]) + timedelta(days=i)
                for i in range((getdate(app["to_date"]) - getdate(app["from_date"])).days + 1)
            ]

        per_day = hours / len(dates) if dates else 0
        for d in dates:
            key = (app["employee"], getdate(d))
            entry = leave_map.setdefault(
                key,
                {"hours": 0, "leave_type": leave_type, "names": [], "is_compensatory": is_compensatory},
            )
            entry["hours"] = flt(entry["hours"], 2) + flt(per_day, 2)
            entry["names"].append(app["name"])

    return leave_map

def get_attendance_map(filters):
    """Get existing attendance records for the selected period."""
    attendance_map = {}
    employees_to_include = get_employees_to_include(filters)

    if filters.get("company") and not employees_to_include:
        return attendance_map

    employee_filter = ""
    params = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
    }

    if employees_to_include:
        placeholders = []
        for idx, emp in enumerate(employees_to_include):
            key = f"employee_{idx}"
            params[key] = emp
            placeholders.append(f"%({key})s")
        employee_filter = f"AND employee IN ({', '.join(placeholders)})"

    attendance_query = """
        SELECT
            name,
            employee,
            attendance_date,
            status
        FROM `tabAttendance`
        WHERE attendance_date >= %(from_date)s
          AND attendance_date <= %(to_date)s
          AND docstatus < 2
          {employee_filter}
        ORDER BY employee, attendance_date, modified DESC
    """.format(employee_filter=employee_filter)

    rows = frappe.db.sql(attendance_query, params, as_dict=True)

    for row in rows:
        attendance_map[(row.employee, row.attendance_date)] = {
            "name": row.name,
            "status": row.status,
        }

    return attendance_map

def set_checkin_time(checkin_name, timestamp):
    frappe.db.set_value("Employee Checkin", checkin_name, "time", timestamp, update_modified=False)


@frappe.whitelist()
def update_checkin_log(checkin_name, work_date, log_time, log_type):
    """Safely update checkin datetime and type without unintended date shifts."""
    frappe.has_permission("Employee Checkin", "write", throw=True)

    if not checkin_name:
        frappe.throw(_("نام لاگ اجباری است"))

    if not work_date or not log_time:
        frappe.throw(_("تاریخ و ساعت اجباری است"))

    if log_type not in ("IN", "OUT"):
        frappe.throw(_("نوع لاگ نامعتبر است"))

    dt_string = f"{work_date} {log_time}"

    doc = frappe.get_doc("Employee Checkin", checkin_name)
    doc.time = dt_string
    doc.log_type = log_type
    doc.save(ignore_permissions=True)

    return {
        "success": True,
        "name": doc.name,
        "time": doc.time,
        "log_type": doc.log_type,
        "message": _("لاگ با موفقیت ویرایش شد")
    }


@frappe.whitelist()
def normalize_midnight_checkout_logs(from_date, to_date, employee=None, employees=None, company=None):
    """Shift exactly 00:00:00 checkout logs to 00:00:01 to avoid midnight ambiguity."""
    frappe.has_permission("Employee Checkin", "write", throw=True)

    filters = {
        "from_date": from_date,
        "to_date": to_date,
        "employee": employee,
        "employees": employees,
        "company": company,
    }

    employees_to_include = get_employees_to_include(filters)

    if company and not employees_to_include:
        return {
            "success": True,
            "updated_count": 0,
            "message": _("برای این شرکت کارمندی پیدا نشد"),
        }

    employee_filter = ""
    params = {
        "from_date": getdate(from_date),
        "to_date": getdate(to_date),
    }

    if employees_to_include:
        placeholders = []
        for idx, emp in enumerate(employees_to_include):
            key = f"employee_{idx}"
            params[key] = emp
            placeholders.append(f"%({key})s")
        employee_filter = f"AND employee IN ({', '.join(placeholders)})"

    query = """
        SELECT name, time
        FROM `tabEmployee Checkin`
        WHERE DATE(time) >= %(from_date)s
          AND DATE(time) <= %(to_date)s
          AND TIME(time) = '00:00:00'
          AND log_type = 'OUT'
          {employee_filter}
    """.format(employee_filter=employee_filter)

    logs = frappe.db.sql(query, params, as_dict=True)
    updated = 0

    for log in logs:
        set_checkin_time(log.name, log.time + timedelta(seconds=1))
        updated += 1

    return {
        "success": True,
        "updated_count": updated,
        "message": _("تعداد {0} لاگ نیمه‌شب اصلاح شد").format(updated),
    }

def _cleanup_noisy_day_logs(employee, work_date):
    target_date = getdate(work_date)
    has_excl = frappe.db.has_column("Employee Checkin", "custom_is_excluded")
    excl_filter = "AND IFNULL(custom_is_excluded, 0) = 0" if has_excl else ""

    logs = frappe.db.sql(
        """
        SELECT name, log_type, time
        FROM `tabEmployee Checkin`
        WHERE employee = %(employee)s
          AND DATE(time) = %(work_date)s
          {excl_filter}
        ORDER BY time, creation
        """.format(excl_filter=excl_filter),
        {"employee": employee, "work_date": target_date},
        as_dict=True,
    )

    to_flag = []
    kept = []
    for log in logs:
        if kept:
            prev = kept[-1]
            same_timestamp = prev.time == log.time
            if same_timestamp:
                if prev.log_type == log.log_type:
                    to_flag.append(log.name)
                    continue

                # IN/OUT با timestamp یکسان: لاگ بعدی نویزی است.
                to_flag.append(log.name)
                continue
        kept.append(log)

    # به‌جای حذف، لاگ‌های نویزی را علامت‌گذاری می‌کنیم (حساب نشود)
    if has_excl:
        for name in to_flag:
            frappe.db.set_value("Employee Checkin", name, "custom_is_excluded", 1, update_modified=False)
    else:
        # اگر فیلد هنوز ایجاد نشده، حذف می‌کنیم (fallback)
        for name in to_flag:
            frappe.delete_doc("Employee Checkin", name, ignore_permissions=True)

    repair_result = auto_repair_day_checkins(employee=employee, work_date=target_date)

    return {
        "flagged_count": len(to_flag),
        "deleted_count": len(to_flag),  # backward compat
        "flagged_logs": to_flag,
        "repaired_count": repair_result.get("updated_count", 0),
        "message": _("تعداد {0} لاگ نویزی علامت‌گذاری شد (حساب نشود)").format(len(to_flag)),
        "work_date": target_date,
        "employee": employee,
    }


@frappe.whitelist()
def cleanup_noisy_day_logs(employee, work_date):
    """Delete obvious duplicate/noise logs for a single employee-day."""
    frappe.has_permission("Employee Checkin", "write", throw=True)
    result = _cleanup_noisy_day_logs(employee=employee, work_date=work_date)
    result["success"] = True
    return result


@frappe.whitelist()
def cleanup_noisy_logs_bulk(from_date, to_date, employee=None, employees=None, company=None):
    """Bulk cleanup duplicate/noisy logs for selected date range and employees."""
    frappe.has_permission("Employee Checkin", "write", throw=True)

    filters = {
        "from_date": from_date,
        "to_date": to_date,
        "employee": employee,
        "employees": employees,
        "company": company,
    }

    employees_to_include = get_employees_to_include(filters)

    if company and not employees_to_include:
        return {
            "success": True,
            "processed_days": 0,
            "affected_days": 0,
            "deleted_count": 0,
            "repaired_count": 0,
            "message": _("برای این شرکت کارمندی پیدا نشد"),
            "details": [],
        }

    employee_filter = ""
    params = {
        "from_date": getdate(from_date),
        "to_date": getdate(to_date),
    }

    if employees_to_include:
        placeholders = []
        for idx, emp in enumerate(employees_to_include):
            key = f"employee_{idx}"
            params[key] = emp
            placeholders.append(f"%({key})s")
        employee_filter = f"AND employee IN ({', '.join(placeholders)})"

    candidate_rows = frappe.db.sql(
        """
        SELECT employee, DATE(time) AS work_date
        FROM `tabEmployee Checkin`
        WHERE DATE(time) >= %(from_date)s
          AND DATE(time) <= %(to_date)s
          {employee_filter}
        GROUP BY employee, DATE(time), TIME(time)
        HAVING COUNT(*) > 1
        """.format(employee_filter=employee_filter),
        params,
        as_dict=True,
    )

    candidate_days = sorted({(row.employee, row.work_date) for row in candidate_rows})
    if not candidate_days:
        return {
            "success": True,
            "processed_days": 0,
            "affected_days": 0,
            "deleted_count": 0,
            "repaired_count": 0,
            "message": _("روز دارای لاگ تکراری در این بازه پیدا نشد"),
            "details": [],
        }

    details = []
    total_deleted = 0
    total_repaired = 0
    affected_days = 0

    for emp, work_date_value in candidate_days:
        result = _cleanup_noisy_day_logs(employee=emp, work_date=work_date_value)
        total_deleted += result.get("deleted_count", 0)
        total_repaired += result.get("repaired_count", 0)
        if result.get("deleted_count", 0) or result.get("repaired_count", 0):
            affected_days += 1
        details.append(result)

    return {
        "success": True,
        "processed_days": len(candidate_days),
        "affected_days": affected_days,
        "deleted_count": total_deleted,
        "repaired_count": total_repaired,
        "details": details,
        "message": _("پاکسازی خودکار انجام شد"),
    }


@frappe.whitelist()
def auto_repair_day_checkins(employee, work_date):
    """Reorder daily checkins as alternating IN/OUT by timestamp."""
    frappe.has_permission("Employee Checkin", "write", throw=True)
    target_date = getdate(work_date)

    has_excl = frappe.db.has_column("Employee Checkin", "custom_is_excluded")
    excl_filter = "AND IFNULL(custom_is_excluded, 0) = 0" if has_excl else ""

    logs = frappe.db.sql(
        """
        SELECT name, log_type
        FROM `tabEmployee Checkin`
        WHERE employee = %(employee)s
          AND DATE(time) = %(work_date)s
          {excl_filter}
        ORDER BY time, creation
        """.format(excl_filter=excl_filter),
        {"employee": employee, "work_date": target_date},
        as_dict=True,
    )

    updated = 0
    for idx, log in enumerate(logs):
        desired_type = "IN" if idx % 2 == 0 else "OUT"
        if log.log_type != desired_type:
            frappe.db.set_value(
                "Employee Checkin", log.name, "log_type", desired_type, update_modified=False
            )
            updated += 1

    return {
        "success": True,
        "updated_count": updated,
        "total_logs": len(logs),
        "message": _("چیدمان ورود/خروج برای {0} لاگ بازسازی شد").format(len(logs)),
    }


@frappe.whitelist()
def upsert_attendance_from_report(employee, work_date, status, leave_type=None):
    """Create or update Attendance for no-log days directly from report."""
    frappe.has_permission("Attendance", "write", throw=True)

    allowed_status = {"Absent", "On Leave"}
    if status not in allowed_status:
        frappe.throw(_("وضعیت نامعتبر است"))

    attendance_date = getdate(work_date)
    company = frappe.db.get_value("Employee", employee, "company")
    if not company:
        frappe.throw(_("شرکت برای این کارمند تنظیم نشده است"))

    attendance_name = frappe.db.get_value(
        "Attendance",
        {"employee": employee, "attendance_date": attendance_date, "docstatus": ("<", 2)},
        "name",
    )

    if attendance_name:
        attendance = frappe.get_doc("Attendance", attendance_name)
        if attendance.docstatus == 1:
            attendance.cancel()
        # delete the (now cancelled/old) record and create a fresh one so we never
        # try to edit a cancelled document
        frappe.delete_doc("Attendance", attendance_name, force=1, ignore_permissions=True)
        attendance = frappe.new_doc("Attendance")
        attendance.employee = employee
        attendance.attendance_date = attendance_date
        attendance.status = status
        attendance.company = company
        attendance.insert(ignore_permissions=True)
        attendance.submit()
    else:
        attendance = frappe.new_doc("Attendance")
        attendance.employee = employee
        attendance.attendance_date = attendance_date
        attendance.status = status
        attendance.company = company
        attendance.insert(ignore_permissions=True)
        attendance.submit()

    # Best-effort leave application creation for "On Leave".
    leave_application_name = None
    leave_error = None
    if status == "On Leave" and leave_type:
        leave_application_name, leave_error = ensure_single_day_leave_application(
            employee=employee,
            company=company,
            leave_type=leave_type,
            leave_date=attendance_date,
        )

    return {
        "success": True,
        "attendance": attendance.name,
        "leave_application": leave_application_name,
        "leave_error": leave_error,
    }


@frappe.whitelist()
def get_break_deduction_details(employee, from_date, to_date=None):
    """
    Calculate break deduction details for an employee on a specific date.

    Uses Break Assignment + Break Hours doctypes (NOT per-employee custom fields).
    Returns gross_hours, total_break_hours, net_working_hours, and per-break details.

    Handles edge cases:
    - Overlapping breaks: each break window is evaluated independently, capped by span
    - Breaks outside check-in/check-out window: only overlapping portion is deducted
    - Multiple breaks in one day: all applicable breaks are summed
    """
    from_date = getdate(from_date)
    to_date = getdate(to_date) if to_date else from_date

    # 1. Get check-in/out pairs for the employee on the given date(s)
    checkin_query = """
        SELECT
            name, employee, DATE(time) AS work_date, TIME(time) AS log_time,
            time AS full_time, log_type
        FROM `tabEmployee Checkin`
        WHERE employee = %(employee)s
          AND DATE(time) >= %(from_date)s
          AND DATE(time) <= %(to_date)s
          AND IFNULL(custom_is_excluded, 0) = 0
        ORDER BY time
    """
    raw_checkins = frappe.db.sql(
        checkin_query,
        {"employee": employee, "from_date": from_date, "to_date": to_date},
        as_dict=True,
    )

    if not raw_checkins:
        return {
            "employee": employee,
            "from_date": str(from_date),
            "to_date": str(to_date),
            "gross_hours": 0,
            "total_break_hours": 0,
            "net_working_hours": 0,
            "break_details": [],
            "checkin_pairs": [],
            "has_checkins": False,
        }

    # 2. Build IN/OUT pairs per day — optimized: pre-sort and pair sequentially
    from datetime import datetime, timedelta

    def _time_to_seconds(tv):
        if tv is None:
            return 0
        if isinstance(tv, timedelta):
            return int(tv.total_seconds())
        s = str(tv).split(".")[0]
        parts = s.split(":")
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + (int(parts[2]) if len(parts) > 2 else 0)

    # Group checkins by day and sort by time
    checkins_by_day = {}
    for c in raw_checkins:
        wd = c.work_date
        if wd not in checkins_by_day:
            checkins_by_day[wd] = []
        checkins_by_day[wd].append(c)
    for wd in checkins_by_day:
        checkins_by_day[wd].sort(key=lambda x: str(x.full_time))

    daily_sessions = {}
    for wd, day_checkins in checkins_by_day.items():
        session = {"pairs": [], "unpaired_ins": [], "first_in": None, "last_out": None}
        daily_sessions[wd] = session

        i = 0
        while i < len(day_checkins):
            c = day_checkins[i]
            if c.log_type == "IN":
                # Find next OUT after this IN
                next_out = None
                for j in range(i + 1, len(day_checkins)):
                    if day_checkins[j].log_type == "OUT":
                        next_out = day_checkins[j]
                        break
                if next_out:
                    in_dt = c.full_time if isinstance(c.full_time, datetime) else datetime.strptime(str(c.full_time), "%Y-%m-%d %H:%M:%S")
                    out_dt = next_out.full_time if isinstance(next_out.full_time, datetime) else datetime.strptime(str(next_out.full_time), "%Y-%m-%d %H:%M:%S")
                    dur = max(0, (out_dt - in_dt).total_seconds())
                    session["pairs"].append({
                        "in_time": c.log_time,
                        "out_time": next_out.log_time,
                        "in_seconds": _time_to_seconds(c.log_time),
                        "out_seconds": _time_to_seconds(next_out.log_time),
                        "duration_seconds": dur,
                    })
                    if not session["first_in"]:
                        session["first_in"] = c.log_time
                    session["last_out"] = next_out.log_time
                    # Skip the OUT we just paired
                    i = day_checkins.index(next_out) + 1
                else:
                    session["unpaired_ins"].append(c.log_time)
                    if not session["first_in"]:
                        session["first_in"] = c.log_time
                    i += 1
            elif c.log_type == "OUT":
                # Unpaired OUT — skip (handled by overnight logic in report)
                i += 1
            else:
                i += 1

    # 3. Get Break Assignment records for this employee
    has_calculation_type = frappe.db.has_column("Break Hours", "calculation_type")
    has_fixed_rules = frappe.db.exists("DocType", "Break Deduction Rule")
    calculation_type_select = "bh.calculation_type" if has_calculation_type else "'Time Window' AS calculation_type"

    break_rows = frappe.db.sql(
        f"""
        SELECT
            bh.name AS break_hours_name,
            ba.from_date, ba.to_date,
            bh.break_name, bh.break_start, bh.break_end, bh.deduction_hours,
            {calculation_type_select}
        FROM `tabBreak Assignment` ba
        JOIN `tabBreak Hours` bh ON bh.name = ba.break_hours
        WHERE ba.employee = %(employee)s
          AND ba.docstatus = 1
          AND ba.status = 'Active'
          AND bh.is_active = 1
          AND ba.from_date <= %(to_date)s
          AND (ba.to_date IS NULL OR ba.to_date >= %(from_date)s)
        ORDER BY bh.break_start
        """,
        {"employee": employee, "from_date": from_date, "to_date": to_date},
        as_dict=True,
    )

    break_names = [row.break_hours_name for row in break_rows if row.get("break_hours_name")]
    fixed_rules = {}
    if has_fixed_rules and break_names:
        rule_rows = frappe.get_all(
            "Break Deduction Rule",
            filters={"parent": ["in", break_names], "parenttype": "Break Hours"},
            fields=["parent", "minimum_work_hours", "deduction_hours", "description"],
            order_by="parent asc, minimum_work_hours asc",
            limit_page_length=0,
        )
        for rule in rule_rows:
            fixed_rules.setdefault(rule.parent, []).append(
                {
                    "minimum_work_hours": flt(rule.minimum_work_hours),
                    "deduction_hours": flt(rule.deduction_hours),
                    "description": rule.description or "",
                }
            )

    break_windows = []
    for row in break_rows:
        calculation_type = row.get("calculation_type") or "Time Window"
        if calculation_type == "Fixed by Worked Hours":
            thresholds = fixed_rules.get(row.break_hours_name, [])
            if not thresholds:
                continue
            break_windows.append({
                "name": row.break_name,
                "calculation_type": calculation_type,
                "thresholds": thresholds,
                "from_date": getdate(row.from_date),
                "to_date": getdate(row.to_date) if row.to_date else None,
            })
            continue

        br_start = _time_to_seconds(row.break_start)
        br_end = _time_to_seconds(row.break_end)
        ded = flt(row.deduction_hours)
        break_windows.append({
            "name": row.break_name,
            "calculation_type": "Time Window",
            "start": br_start,
            "end": br_end,
            "deduction_seconds": int(ded * 3600),
            "from_date": getdate(row.from_date),
            "to_date": getdate(row.to_date) if row.to_date else None,
        })

    # 4. Calculate per-day break deductions
    total_gross = 0
    total_break = 0
    all_break_details = []
    all_pairs = []

    for wd in sorted(daily_sessions.keys()):
        session = daily_sessions[wd]
        pairs = session["pairs"]

        if not pairs:
            all_pairs.append({
                "work_date": str(wd),
                "gross_hours": 0,
                "break_hours": 0,
                "net_hours": 0,
                "first_in": session.get("first_in"),
                "last_out": session.get("last_out"),
                "break_details": [],
            })
            continue

        first_in_sec = _time_to_seconds(session["first_in"])
        last_out_sec = _time_to_seconds(session["last_out"])

        # Handle overnight: if last out < first in, add 24h
        if last_out_sec <= first_in_sec and pairs:
            last_pair_out = pairs[-1]["out_seconds"]
            first_pair_in = pairs[0]["in_seconds"]
            if last_pair_out < first_pair_in:
                last_out_sec += 24 * 3600

        gross_seconds = sum(p["duration_seconds"] for p in pairs)
        gross_hours = gross_seconds / 3600

        # Calculate break deduction using the existing function
        break_hours = calculate_break_hours(first_in_sec, last_out_sec, break_windows)
        net_hours = max(0, gross_hours - break_hours)

        # Build per-break detail
        day_break_details = []
        for bw in break_windows:
            # Check if this window applies to this date
            if bw["from_date"] > wd or (bw["to_date"] and bw["to_date"] < wd):
                continue

            if bw.get("calculation_type") == "Fixed by Worked Hours":
                matching_rules = [
                    rule for rule in bw.get("thresholds", [])
                    if gross_hours >= flt(rule.get("minimum_work_hours"))
                ]
                if not matching_rules:
                    continue
                selected = max(matching_rules, key=lambda rule: flt(rule.get("minimum_work_hours")))
                day_break_details.append({
                    "break_name": bw["name"],
                    "break_start": "",
                    "break_end": "",
                    "deduction_hours": flt(selected.get("deduction_hours"), 2),
                    "overlap_minutes": 0,
                    "minimum_work_hours": flt(selected.get("minimum_work_hours"), 2),
                })
                continue

            bs = bw["start"]
            be = bw["end"]
            if be <= bs:
                be += 24 * 3600

            # Check overlap with work span
            overlap = max(0, min(last_out_sec, be) - max(first_in_sec, bs))
            if overlap <= 0:
                # Try next-day projection
                overlap = max(0, min(last_out_sec, be + 24 * 3600) - max(first_in_sec, bs + 24 * 3600))
                if overlap <= 0:
                    continue

            effective = min(overlap, bw["deduction_seconds"] or overlap)
            day_break_details.append({
                "break_name": bw["name"],
                "break_start": f"{bw['start'] // 3600:02d}:{(bw['start'] % 3600) // 60:02d}",
                "break_end": f"{bw['end'] // 3600:02d}:{(bw['end'] % 3600) // 60:02d}",
                "deduction_hours": flt(effective / 3600, 2),
                "overlap_minutes": flt(overlap / 60, 1),
            })

        total_gross += gross_hours
        total_break += break_hours

        all_break_details.extend(day_break_details)
        all_pairs.append({
            "work_date": str(wd),
            "gross_hours": flt(gross_hours, 2),
            "break_hours": flt(break_hours, 2),
            "net_hours": flt(net_hours, 2),
            "first_in": session.get("first_in"),
            "last_out": session.get("last_out"),
            "break_details": day_break_details,
        })

    return {
        "employee": employee,
        "from_date": str(from_date),
        "to_date": str(to_date),
        "gross_hours": flt(total_gross, 2),
        "total_break_hours": flt(total_break, 2),
        "net_working_hours": flt(max(0, total_gross - total_break), 2),
        "break_details": all_break_details,
        "checkin_pairs": all_pairs,
        "has_checkins": True,
    }


def ensure_single_day_leave_application(employee, company, leave_type, leave_date):
    existing_leave = frappe.db.get_value(
        "Leave Application",
        {
            "employee": employee,
            "from_date": ("<=", leave_date),
            "to_date": (">=", leave_date),
            "docstatus": 1,
            "status": "Approved",
        },
        "name",
    )
    if existing_leave:
        return existing_leave, None

    try:
        leave_app = frappe.new_doc("Leave Application")
        leave_app.employee = employee
        leave_app.company = company
        leave_app.leave_type = leave_type
        leave_app.from_date = leave_date
        leave_app.to_date = leave_date
        leave_app.posting_date = nowdate()
        leave_app.status = "Approved"
        leave_app.description = _("ثبت خودکار از گزارش حضور و غیاب هوشمند")
        leave_app.insert(ignore_permissions=True)
        leave_app.submit()
        return leave_app.name, None
    except Exception:
        return None, frappe.get_traceback()

def get_earned_leave_type_for_employee(employee, date):
    """Return an earned/paid (non-LWP) leave type the employee has balance for.

    Prefers "استحقاقی" but falls back to any paid leave type with available balance.
    Returns None if the employee has no usable paid leave.
    """
    target_date = getdate(date)
    leave_allocations = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "docstatus": 1,
            "from_date": ("<=", target_date),
            "to_date": (">=", target_date),
        },
        fields=["name", "leave_type", "from_date", "to_date"],
    )

    preferred = None
    fallback = None
    for alloc in leave_allocations:
        leave_type = alloc["leave_type"]
        leave_type_doc = frappe.get_doc("Leave Type", leave_type)
        if leave_type_doc.is_lwp or leave_type_doc.is_compensatory:
            continue

        try:
            from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

            balance = get_leave_balance_on(
                employee, leave_type, alloc["from_date"], target_date, consider_all_leaves_in_the_allocation_period=True
            )
        except Exception:
            balance = 0

        if flt(balance) <= 0:
            continue

        if leave_type == "استحقاقی":
            return leave_type

        if preferred is None and fallback is None:
            fallback = leave_type

    return preferred or fallback


@frappe.whitelist()
def create_hourly_leave_from_shortage(employee, work_date, hours, leave_type=None):
    """Create an approved hourly Leave Application to cover a partial-day shortage.

    Deducts the given hours from the employee's paid (استحقاقی) leave balance.
    """
    frappe.has_permission("Leave Application", "write", throw=True)

    if not employee or not work_date:
        frappe.throw(_("کارمند و تاریخ الزامی است"))

    hours = flt(hours)
    if hours <= 0:
        frappe.throw(_("تعداد ساعت باید بزرگتر از صفر باشد"))

    leave_date = getdate(work_date)
    company = frappe.db.get_value("Employee", employee, "company")

    if not leave_type:
        leave_type = get_earned_leave_type_for_employee(employee, leave_date)

    if not leave_type:
        return {
            "success": False,
            "message": _("مرخصی استحقاقی (با حقوق) با موجودی برای این کارمند پیدا نشد"),
        }

    existing = frappe.db.get_value(
        "Leave Application",
        {
            "employee": employee,
            "leave_type": leave_type,
            "hourly_date": leave_date,
            "leave_duration_mode": "ساعتی",
            "docstatus": 1,
        },
        "name",
    )
    if existing:
        return {"success": True, "message": _("مرخصی ساعتی برای این روز قبلاً ثبت شده است"), "leave_application": existing}

    # Hourly leave must span at least 1 minute so that to_time is strictly after
    # from_time (a tiny shortage like 0.04h would otherwise round to equal times
    # and trigger "To Time should be after From Time").
    from_time = "09:00:00"
    min_hours = 1.0 / 60  # 1 minute
    hours = max(flt(hours), min_hours)

    start_dt = datetime.combine(leave_date, datetime.min.time()) + timedelta(hours=9)
    to_dt = start_dt + timedelta(hours=hours)
    # never allow the span to spill past midnight
    end_of_day = datetime.combine(leave_date, datetime.min.time()) + timedelta(hours=24)
    if to_dt >= end_of_day:
        to_dt = end_of_day - timedelta(minutes=1)

    to_time = to_dt.strftime("%H:%M:%S")

    try:
        leave_app = frappe.new_doc("Leave Application")
        leave_app.employee = employee
        leave_app.company = company
        leave_app.leave_type = leave_type
        leave_app.leave_duration_mode = "ساعتی"
        leave_app.hourly_date = leave_date
        leave_app.from_date = leave_date
        leave_app.to_date = leave_date
        leave_app.hourly_from_time = from_time
        leave_app.hourly_to_time = to_time
        leave_app.posting_date = nowdate()
        leave_app.status = "Approved"
        leave_app.description = _("ثبت مرخصی ساعتی از گزارش حضور و غیاب هوشمند")
        leave_app.insert(ignore_permissions=True)
        leave_app.submit()
        return {
            "success": True,
            "leave_application": leave_app.name,
            "hours": hours,
            "message": _("مرخصی ساعتی {0} ثبت شد").format(leave_app.name),
        }
    except Exception:
        return {"success": False, "message": frappe.get_traceback()}


@frappe.whitelist()
def delete_leave_application_from_report(leave_application):
    """Cancel + delete an approved Leave Application from the smart attendance report.

    A leave application for a full day creates a linked Attendance record. That
    attendance must be cancelled/deleted first, otherwise deleting the leave fails
    with LinkExistsError.
    """
    frappe.has_permission("Leave Application", "write", throw=True)
    if not leave_application:
        return {"success": False, "message": _("مرخصی مشخص نشده است")}

    doc = frappe.get_doc("Leave Application", leave_application)

    # cancel + delete linked attendance records first
    linked_attendance = frappe.get_all(
        "Attendance",
        filters={"leave_application": leave_application, "docstatus": ("<", 2)},
        pluck="name",
    )
    for att_name in linked_attendance:
        att = frappe.get_doc("Attendance", att_name)
        if att.docstatus == 1:
            att.cancel()
        frappe.delete_doc("Attendance", att_name, force=1, ignore_permissions=True)

    # also clean up any attendance on the leave days regardless of the link,
    # matching the behaviour of LeaveApplication.cancel_attendance()
    leave_days = (getdate(doc.to_date) - getdate(doc.from_date)).days + 1
    for i in range(leave_days):
        att_date = getdate(doc.from_date) + timedelta(days=i)
        att_name = frappe.db.exists(
            "Attendance",
            {
                "employee": doc.employee,
                "attendance_date": att_date,
                "status": ["in", ["On Leave", "Half Day"]],
                "docstatus": ("<", 2),
            },
        )
        if att_name:
            att = frappe.get_doc("Attendance", att_name)
            if att.docstatus == 1:
                att.cancel()
            frappe.delete_doc("Attendance", att_name, force=1, ignore_permissions=True)

    if doc.docstatus == 1:
        doc.cancel()
    frappe.delete_doc("Leave Application", leave_application, force=1, ignore_permissions=True)
    frappe.db.commit()

    return {"success": True, "message": _("مرخصی {0} و حضور و غیاب مرتبط حذف شد").format(leave_application)}


@frappe.whitelist()
def update_leave_application_from_report(leave_application, leave_type, hours, work_date):
    """Edit the leave type / hours of an approved Leave Application.

    For hourly leaves, updates the time span. For daily leaves, only the type is
    changed (a full day stays a full day).
    """
    frappe.has_permission("Leave Application", "write", throw=True)
    if not leave_application or not leave_type:
        return {"success": False, "message": _("نوع مرخصی الزامی است")}

    doc = frappe.get_doc("Leave Application", leave_application)
    if doc.leave_duration_mode == "ساعتی":
        hours = flt(hours)
        if hours <= 0:
            return {"success": False, "message": _("تعداد ساعت باید بزرگتر از صفر باشد")}

        min_hours = 1.0 / 60
        hours = max(hours, min_hours)
        leave_date = getdate(work_date or doc.hourly_date or doc.from_date)
        start_dt = datetime.combine(leave_date, datetime.min.time()) + timedelta(hours=9)
        to_dt = start_dt + timedelta(hours=hours)
        end_of_day = datetime.combine(leave_date, datetime.min.time()) + timedelta(hours=24)
        if to_dt >= end_of_day:
            to_dt = end_of_day - timedelta(minutes=1)

        doc.leave_type = leave_type
        doc.hourly_date = leave_date
        doc.from_date = leave_date
        doc.to_date = leave_date
        doc.hourly_from_time = "09:00:00"
        doc.hourly_to_time = to_dt.strftime("%H:%M:%S")
    else:
        doc.leave_type = leave_type

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"success": True, "message": _("مرخصی {0} ویرایش شد").format(leave_application)}


@frappe.whitelist()
def add_manual_checkin(employee, log_type, time):
    """Create a manual Employee Checkin record."""
    frappe.has_permission("Employee Checkin", "create", throw=True)

    if not employee:
        frappe.throw(_("کارمند اجباری است"))

    if not time:
        frappe.throw(_("زمان اجباری است"))

    if log_type not in ("IN", "OUT"):
        frappe.throw(_("نوع لاگ نامعتبر است"))

    doc = frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": employee,
        "time": time,
        "log_type": log_type,
        "skip_auto_attendance": 1
    })
    doc.insert(ignore_permissions=True)

    return {
        "success": True,
        "name": doc.name,
        "message": _("لاگ با موفقیت ثبت شد")
    }


@frappe.whitelist()
def toggle_checkin_excluded(checkin_name, is_excluded):
    """Toggle the custom_is_excluded flag on an Employee Checkin record."""
    frappe.has_permission("Employee Checkin", "write", throw=True)

    if not checkin_name:
        frappe.throw(_("نام لاگ اجباری است"))

    ensure_excluded_field_exists()

    frappe.db.set_value(
        "Employee Checkin",
        checkin_name,
        "custom_is_excluded",
        int(flt(is_excluded)),
        update_modified=False
    )
    frappe.db.commit()

    return {
        "success": True,
        "checkin_name": checkin_name,
        "is_excluded": bool(int(flt(is_excluded))),
        "message": _("لاگ حساب نشود علامت‌گذاری شد") if int(flt(is_excluded)) else _("علامت‌گذاری برداشته شد")
    }
