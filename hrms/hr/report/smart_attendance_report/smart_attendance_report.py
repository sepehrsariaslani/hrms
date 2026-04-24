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


def execute(filters=None):
    filters = filters or {}
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
            "fieldname": "time_off",
            "label": _("کسری"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 60
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
    
    # Extend date range by 1 day back to catch overnight shifts
    extended_from = add_days(filters.get("from_date"), -1)
    
    # Build employee filter for multiple employees
    employee_filter = ""
    employee_list = []
    employee_params = {}
    if filters.get("employee"):
        employee_filter = "AND employee = %(employee)s"
    elif filters.get("employees"):
        employee_list = [e.strip() for e in filters.get("employees").split(",") if e.strip()]
        if employee_list:
            placeholders = []
            for idx, emp in enumerate(employee_list):
                key = f"employee_{idx}"
                placeholders.append(f"%({key})s")
                employee_params[key] = emp
            employee_filter = f"AND employee IN ({', '.join(placeholders)})"
    
    # Get raw checkin data ordered by employee and time
    checkin_query = """
        SELECT 
            name,
            employee,
            DATE(time) AS work_date,
            TIME(time) AS log_time,
            time AS full_time,
            log_type
        FROM `tabEmployee Checkin`
        WHERE DATE(time) >= %(extended_from)s
          AND DATE(time) <= %(to_date)s
          {employee_filter}
        ORDER BY employee, time
    """
    
    checkin_query = checkin_query.format(employee_filter=employee_filter)
    
    params = {
        "extended_from": extended_from,
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "employee": filters.get("employee"),
        **employee_params,
    }
    
    raw_checkins = frappe.db.sql(checkin_query, params, as_dict=True)
    
    # Group checkins by employee first
    employee_checkins_raw = {}
    for c in raw_checkins:
        if c.employee not in employee_checkins_raw:
            employee_checkins_raw[c.employee] = []
        employee_checkins_raw[c.employee].append(c)

    # Normalize obvious duplicate/noise logs before pairing and display.
    employee_checkins = {}
    all_logs_lookup = {}
    for employee, checkins in employee_checkins_raw.items():
        cleaned_logs = normalize_noisy_checkins(checkins)
        employee_checkins[employee] = cleaned_logs

        for c in cleaned_logs:
            key = (c.employee, c.work_date)
            if key not in all_logs_lookup:
                all_logs_lookup[key] = []
            all_logs_lookup[key].append({
                "name": c.name,
                "log_type": c.log_type,
                "log_time": c.log_time
            })
    
    # Track logs that are used in overnight sessions (to avoid duplication)
    used_overnight_logs = set()
    
    # Process each employee's checkins to pair IN/OUT across days
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
                        
                        # Mark this OUT log as used for overnight
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
    
    # Get employee names and break settings
    employee_names = {}
    employee_break_settings = {}
    employees_in_checkins = list(set([c.employee for c in raw_checkins]))
    
    for emp in employees_in_checkins:
        emp_data = frappe.db.get_value("Employee", emp, 
            ["employee_name", 
             "deduct_morning_break", "morning_break_start", "morning_break_end",
             "deduct_lunch_break", "lunch_break_start", "lunch_break_end",
             "deduct_afternoon_break", "afternoon_break_start", "afternoon_break_end",
             "deduct_evening_break", "evening_break_start", "evening_break_end"
            ], as_dict=True)
        
        if emp_data:
            employee_names[emp] = emp_data.get("employee_name") or emp
            # Handle None values - default to 1 (enabled) if not set
            employee_break_settings[emp] = {
                "morning": {
                    "enabled": 1 if emp_data.get("deduct_morning_break") in [1, None] else 0,
                    "start": time_to_seconds(emp_data.get("morning_break_start")) or (9 * 3600 + 40 * 60),
                    "end": time_to_seconds(emp_data.get("morning_break_end")) or (10 * 3600)
                },
                "lunch": {
                    "enabled": 1 if emp_data.get("deduct_lunch_break") in [1, None] else 0,
                    "start": time_to_seconds(emp_data.get("lunch_break_start")) or (13 * 3600),
                    "end": time_to_seconds(emp_data.get("lunch_break_end")) or (14 * 3600)
                },
                "afternoon": {
                    "enabled": 1 if emp_data.get("deduct_afternoon_break") in [1, None] else 0,
                    "start": time_to_seconds(emp_data.get("afternoon_break_start")) or (17 * 3600 + 15 * 60),
                    "end": time_to_seconds(emp_data.get("afternoon_break_end")) or (17 * 3600 + 35 * 60)
                },
                "evening": {
                    "enabled": 1 if emp_data.get("deduct_evening_break") in [1, None] else 0,
                    "start": time_to_seconds(emp_data.get("evening_break_start")) or (20 * 3600 + 40 * 60),
                    "end": time_to_seconds(emp_data.get("evening_break_end")) or (21 * 3600)
                }
            }
        else:
            employee_names[emp] = emp
            employee_break_settings[emp] = get_default_break_settings()
    
    # Get shift assignments
    shifts = get_employee_shifts(filters)
    
    # Get holidays
    holidays = get_holidays(filters)
    
    # Existing attendance (used to classify no-log days as absence/leave, not log issues)
    attendance_lookup = get_attendance_map(filters)
    
    # Build report data
    data = []
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))
    
    # Get list of employees to report on
    employees_to_report = []
    if filters.get("employee"):
        employees_to_report = [filters.get("employee")]
    else:
        employees_to_report = list(set(employees_in_checkins))
        for emp in shifts.keys():
            if emp not in employees_to_report:
                employees_to_report.append(emp)
    
    # Generate rows for each employee and date
    for employee in sorted(employees_to_report):
        current_date = from_date
        while current_date <= to_date:
            key = (employee, current_date)
            session = work_sessions.get(key)
            all_logs = all_logs_lookup.get(key, [])
            shift = shifts.get(employee, {})
            is_holiday = (employee, current_date) in holidays
            weekday = current_date.weekday()
            is_friday = weekday == 4
            is_thursday = weekday == 3
            
            # Calculate standard hours
            if is_holiday or is_friday:
                standard_hours = 0
            elif is_thursday:
                standard_hours = 4
            elif shift.get("standard_hours"):
                standard_hours = flt(shift.get("standard_hours"))
            else:
                standard_hours = 7.67
            
            # Format all logs for display with edit capability
            all_logs_str = ""
            all_logs_json = []  # For JS to parse
            log_issues = []
            
            if all_logs:
                log_parts = []
                in_count = 0
                out_count = 0
                
                for log in all_logs:
                    # Skip logs that were used in overnight pairing to previous day
                    if log["name"] in used_overnight_logs:
                        continue

                    time_text = safe_time_text(log.get("log_time"))
                    log_type_icon = "⬇️" if log["log_type"] == "IN" else "⬆️"
                    log_parts.append({
                        "display": f"{log_type_icon}{time_text}",
                        "name": log["name"],
                        "log_type": log["log_type"],
                        "time": time_text
                    })
                    all_logs_json.append({
                        "name": log["name"],
                        "log_type": log["log_type"],
                        "time": time_text
                    })
                    
                    if log["log_type"] == "IN":
                        in_count += 1
                    else:
                        out_count += 1
                
                # Format as display string (JS will enhance with edit icons)
                all_logs_str = " | ".join([p["display"] for p in log_parts])
                
                # Detect issues
                if in_count != out_count:
                    log_issues.append(f"{in_count} ورود، {out_count} خروج")
            
            row = {
                "employee": employee,
                "employee_name": employee_names.get(employee, employee),
                "work_date": current_date,
                "work_date_shamsi": gregorian_to_jalali(current_date, "jYYYY/jMM/jDD"),
                "day_name": get_day_name_persian(weekday),
                "shift_type": shift.get("shift_type", ""),
                "standard_hours": standard_hours,
                "all_logs": all_logs_str,
                "all_logs_json": all_logs_json,  # For JS to parse and add edit icons
                "log_status": "",
                "actual_start": None,
                "actual_end": None,
                "first_in_name": None,
                "last_out_name": None,
                "presence_hours": 0,
                "break_hours": 0,
                "working_hours": 0,
                "time_off": 0 if (is_holiday or is_friday) else standard_hours,
                "overtime": 0,
                "issue_flag": "",
                "has_issue": False,  # For filtering
                "can_mark_attendance": False,
                "attendance_status": None,
                "attendance_name": None,
            }
            
            if session:
                pairs = session["pairs"]
                unpaired_ins = session["unpaired_ins"]
                unpaired_outs = session["unpaired_outs"]
                
                # Calculate total presence from pairs
                total_presence_seconds = sum(p["duration_seconds"] for p in pairs)
                
                # Format times for display
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
                
                # Determine log status with detailed issue description
                if pairs and not unpaired_ins and not unpaired_outs:
                    row["log_status"] = "✅ کامل"
                    row["issue_flag"] = "✅"
                elif unpaired_ins and not unpaired_outs:
                    # Show which logs are unpaired
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
                
                # Calculate hours
                presence_hours = total_presence_seconds / 3600
                
                # Calculate breaks (using per-employee settings with correct time values)
                break_hours = 0
                if pairs:
                    first_in_seconds = time_to_seconds(session["first_in"])
                    last_out_seconds = time_to_seconds(session["last_out"])
                    if session.get("last_out_date") and session["last_out_date"] != current_date:
                        last_out_seconds += 24 * 3600
                    break_settings = employee_break_settings.get(employee, get_default_break_settings())
                    break_hours = calculate_break_hours(first_in_seconds, last_out_seconds, break_settings)
                
                working_hours = max(0, presence_hours - break_hours)
                
                row["presence_hours"] = flt(presence_hours, 2)
                row["break_hours"] = flt(break_hours, 2)
                row["working_hours"] = flt(working_hours, 2)
                
                # Calculate time off and overtime
                if is_holiday or is_friday:
                    row["time_off"] = 0
                    row["overtime"] = flt(working_hours, 2)
                else:
                    if working_hours >= standard_hours:
                        row["time_off"] = 0
                        row["overtime"] = flt(working_hours - standard_hours, 2)
                    else:
                        row["time_off"] = flt(standard_hours - working_hours, 2)
                        row["overtime"] = 0
                        
            elif all_logs and len(all_logs) == 1:
                # Single log - detect if it's likely IN or OUT
                single_log = all_logs[0]
                log_hour = time_to_seconds(single_log["log_time"]) // 3600
                log_time_text = safe_time_text(single_log.get("log_time"))
                
                if single_log["log_type"] == "IN":
                    # System says it's IN
                    if log_hour >= 15:
                        # After 3 PM, probably meant to be OUT
                        row["log_status"] = f"🟠 احتمالاً خروج ({log_time_text})"
                        row["actual_end"] = log_time_text
                        row["last_out_name"] = single_log["name"]
                    else:
                        row["log_status"] = f"🟡 خروج ندارد ({log_time_text})"
                        row["actual_start"] = log_time_text
                        row["first_in_name"] = single_log["name"]
                else:
                    # System says it's OUT
                    if log_hour < 12:
                        # Before noon, probably meant to be IN
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
                # No session for this day
                if not is_holiday and not is_friday:
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

                    # No-log days are not counted as log quality issues.
                    row["issue_flag"] = ""
                    row["has_issue"] = False
                else:
                    row["log_status"] = "تعطیل"
                    row["issue_flag"] = ""
            
            # Apply issue filter
            if filters.get("only_issues"):
                if row["has_issue"]:
                    data.append(row)
            else:
                data.append(row)
                
            current_date = add_days(current_date, 1)
    
    return data


def get_default_break_settings():
    """Return default break settings in seconds"""
    return {
        "morning": {"enabled": 1, "start": 9 * 3600 + 40 * 60, "end": 10 * 3600},
        "lunch": {"enabled": 1, "start": 13 * 3600, "end": 14 * 3600},
        "afternoon": {"enabled": 1, "start": 17 * 3600 + 15 * 60, "end": 17 * 3600 + 35 * 60},
        "evening": {"enabled": 1, "start": 20 * 3600 + 40 * 60, "end": 21 * 3600}
    }


def calculate_break_hours(start_seconds, end_seconds, break_settings=None):
    """Calculate break hours based on employee-specific settings"""
    if start_seconds is None or end_seconds is None:
        return 0
    
    if break_settings is None:
        break_settings = get_default_break_settings()
    
    break_seconds = 0
    
    for break_type in ["morning", "lunch", "afternoon", "evening"]:
        settings = break_settings.get(break_type, {})
        if settings.get("enabled", 1):
            break_start = settings.get("start", 0)
            break_end = settings.get("end", 0)
            
            # Check if the work span covers this break
            if break_start and break_end and start_seconds < break_start and end_seconds > break_end:
                break_seconds += (break_end - break_start)
    
    return break_seconds / 3600


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
        }
    ]


def get_employee_shifts(filters):
    """Get shift assignments for employees"""
    shifts = {}
    
    shift_query = """
        SELECT 
            sa.employee,
            st.name AS shift_type,
            st.start_time,
            st.end_time,
            TIME_TO_SEC(TIMEDIFF(st.end_time, st.start_time)) / 3600 AS shift_duration,
            (TIME_TO_SEC(TIMEDIFF(st.end_time, st.start_time)) / 3600) - 
            (
                CASE WHEN TIME(st.start_time) < '09:40:00' AND TIME(st.end_time) > '10:00:00' THEN 20/60 ELSE 0 END +
                CASE WHEN TIME(st.start_time) < '13:00:00' AND TIME(st.end_time) > '14:00:00' THEN 1.0 ELSE 0 END +
                CASE WHEN TIME(st.start_time) < '17:15:00' AND TIME(st.end_time) > '17:35:00' THEN 20/60 ELSE 0 END +
                CASE WHEN TIME(st.start_time) < '20:40:00' AND TIME(st.end_time) > '21:00:00' THEN 20/60 ELSE 0 END
            ) AS standard_hours
        FROM `tabShift Assignment` sa
        JOIN `tabShift Type` st ON sa.shift_type = st.name
        WHERE sa.docstatus = 1
            AND sa.start_date <= %(to_date)s
            AND (sa.end_date IS NULL OR sa.end_date >= %(from_date)s)
            {employee_filter}
    """
    
    employee_filter = ""
    if filters.get("employee"):
        employee_filter = "AND sa.employee = %(employee)s"
    
    shift_query = shift_query.format(employee_filter=employee_filter)
    
    shift_data = frappe.db.sql(shift_query, {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "employee": filters.get("employee")
    }, as_dict=True)
    
    for s in shift_data:
        shifts[s.employee] = {
            "shift_type": s.shift_type,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "shift_duration": s.shift_duration,
            "standard_hours": s.standard_hours
        }
    
    return shifts


def get_holidays(filters):
    """Get holidays for employees"""
    holidays = set()
    
    holiday_query = """
        SELECT
            h.holiday_date,
            e.name AS employee
        FROM `tabHoliday` h
        JOIN `tabHoliday List` hl ON hl.name = h.parent
        JOIN `tabEmployee` e ON e.holiday_list = hl.name
        WHERE h.holiday_date >= %(from_date)s
          AND h.holiday_date <= %(to_date)s
          {employee_filter}
    """
    
    employee_filter = ""
    if filters.get("employee"):
        employee_filter = "AND e.name = %(employee)s"
    
    holiday_query = holiday_query.format(employee_filter=employee_filter)
    
    holiday_data = frappe.db.sql(holiday_query, {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "employee": filters.get("employee")
    }, as_dict=True)
    
    for h in holiday_data:
        holidays.add((h.employee, h.holiday_date))
    
    return holidays


def get_attendance_map(filters):
    """Get existing attendance records for the selected period."""
    attendance_map = {}

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
    """

    employee_filter = ""
    params = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "employee": filters.get("employee"),
    }

    if filters.get("employee"):
        employee_filter = "AND employee = %(employee)s"
    elif filters.get("employees"):
        employee_list = [e.strip() for e in (filters.get("employees") or "").split(",") if e.strip()]
        if employee_list:
            placeholders = []
            for idx, emp in enumerate(employee_list):
                key = f"employee_{idx}"
                placeholders.append(f"%({key})s")
                params[key] = emp
            employee_filter = f"AND employee IN ({', '.join(placeholders)})"

    attendance_query = attendance_query.format(employee_filter=employee_filter)
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
def normalize_midnight_checkout_logs(from_date, to_date, employee=None, employees=None):
    """Shift exactly 00:00:00 checkout logs to 00:00:01 to avoid midnight ambiguity."""
    frappe.has_permission("Employee Checkin", "write", throw=True)

    employee_filter = ""
    params = {
        "from_date": getdate(from_date),
        "to_date": getdate(to_date),
    }

    if employee:
        employee_filter = "AND employee = %(employee)s"
        params["employee"] = employee
    elif employees:
        employee_list = [e.strip() for e in employees.split(",") if e.strip()]
        if employee_list:
            placeholders = []
            for idx, emp in enumerate(employee_list):
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
    logs = frappe.db.sql(
        """
        SELECT name, log_type, time
        FROM `tabEmployee Checkin`
        WHERE employee = %(employee)s
          AND DATE(time) = %(work_date)s
        ORDER BY time, creation
        """,
        {"employee": employee, "work_date": target_date},
        as_dict=True,
    )

    to_delete = []
    kept = []
    for log in logs:
        if kept:
            prev = kept[-1]
            same_timestamp = prev.time == log.time
            if same_timestamp:
                if prev.log_type == log.log_type:
                    to_delete.append(log.name)
                    continue

                # IN/OUT with identical timestamp: drop the latter noisy punch.
                to_delete.append(log.name)
                continue
        kept.append(log)

    for name in to_delete:
        frappe.delete_doc("Employee Checkin", name, ignore_permissions=True)

    repair_result = auto_repair_day_checkins(employee=employee, work_date=target_date)

    return {
        "deleted_count": len(to_delete),
        "deleted_logs": to_delete,
        "repaired_count": repair_result.get("updated_count", 0),
        "message": _("تعداد {0} لاگ نویزی حذف شد").format(len(to_delete)),
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
def cleanup_noisy_logs_bulk(from_date, to_date, employee=None, employees=None):
    """Bulk cleanup duplicate/noisy logs for selected date range and employees."""
    frappe.has_permission("Employee Checkin", "write", throw=True)

    employee_filter = ""
    params = {
        "from_date": getdate(from_date),
        "to_date": getdate(to_date),
    }

    if employee:
        employee_filter = "AND employee = %(employee)s"
        params["employee"] = employee
    elif employees:
        employee_list = [e.strip() for e in (employees or "").split(",") if e.strip()]
        if employee_list:
            placeholders = []
            for idx, emp in enumerate(employee_list):
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

    logs = frappe.db.sql(
        """
        SELECT name, log_type
        FROM `tabEmployee Checkin`
        WHERE employee = %(employee)s
          AND DATE(time) = %(work_date)s
        ORDER BY time, creation
        """,
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

        attendance.status = status
        attendance.company = company
        attendance.save(ignore_permissions=True)
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


@frappe.whitelist()
def add_manual_checkin(employee, log_type, time):
    """Add a manual employee checkin entry"""
    frappe.has_permission("Employee Checkin", "create", throw=True)
    
    checkin = frappe.new_doc("Employee Checkin")
    checkin.employee = employee
    checkin.log_type = log_type
    checkin.time = time
    checkin.insert()
    
    return {
        "success": True,
        "name": checkin.name,
        "message": _("ثبت لاگ با موفقیت انجام شد")
    }
