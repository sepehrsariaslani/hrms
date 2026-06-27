"""
HRMS Attendance QR Checkin API
Endpoints for QR-based attendance (In/Out) using the Attendance DocType.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, nowdate, get_datetime


# ──────────────────────────────────────────────
# API: QR Checkin — toggle In/Out attendance
# ──────────────────────────────────────────────

@frappe.whitelist()
def qr_checkin(employee_id: str = None, scanned_by: str = None):
    """Toggle attendance (In/Out) for an employee via QR scan.

    Input:
        employee_id: Employee ID (name field) from QR code payload
        scanned_by:  User who performed the scan (optional, defaults to session user)

    Logic:
        1. Look up employee by employee_id.
        2. Find the last Attendance record for this employee today.
        3. If no record today OR last record has status = 'Out',
           create new Attendance with status = 'In', in_time = now().
        4. If last record has status = 'In',
           update it with status = 'Out', out_time = now().

    Returns:
        { success, action, employee_name, time, attendance_name }
    """

    # ── Permission check ──
    if frappe.session.user == "Guest":
        frappe.throw(
            _("لطفاً ابتدا وارد سیستم شوید"),
            frappe.AuthenticationError,
        )

    # ── Validate input ──
    if not employee_id:
        frappe.throw(_("پارامتر employee_id الزامی است"), frappe.MandatoryError)

    employee_id = employee_id.strip()

    # ── Look up employee ──
    if not frappe.db.exists("Employee", employee_id):
        frappe.throw(
            _("کارمند با شناسه {0} یافت نشد").format(employee_id),
            frappe.DoesNotExistError,
        )

    employee = frappe.db.get_value(
        "Employee",
        employee_id,
        ["name", "employee_name", "company", "status"],
        as_dict=True,
    )

    if employee.status != "Active":
        frappe.throw(
            _("کارمند {0} غیرفعال است").format(employee.employee_name or employee.name),
            frappe.ValidationError,
        )

    # ── Permission check: write on Attendance DocType ──
    if not frappe.has_permission("Attendance", "write"):
        frappe.throw(
            _("Insufficient permissions to mark attendance"),
            frappe.PermissionError,
        )

    # ── Determine scanner ──
    scanner = scanned_by or frappe.session.user

    # ── Find last attendance record for today ──
    today = nowdate()
    last_attendance = frappe.db.get_value(
        "Attendance",
        {
            "employee": employee.name,
            "attendance_date": today,
            "docstatus": ("!=", 2),  # not cancelled
        },
        ["name", "status", "docstatus"],
        order_by="creation desc",
        as_dict=True,
    )

    # ── Toggle logic ──
    action = None
    attendance_name = None

    if not last_attendance or last_attendance.status in ("Out", "Absent", "On Leave"):
        # → Check IN
        action = "In"

        if last_attendance and last_attendance.docstatus == 0:
            # Draft record exists — submit it as Present
            attendance = frappe.get_doc("Attendance", last_attendance.name)
            attendance.status = "Present"
            attendance.in_time = now_datetime()
            attendance.save()
            attendance.submit()
        elif last_attendance and last_attendance.docstatus == 1:
            # Already submitted — create a new one
            attendance = _create_attendance(employee, "In")
            attendance.submit()
        else:
            # No record — create new
            attendance = _create_attendance(employee, "In")
            attendance.submit()

        attendance_name = attendance.name

    elif last_attendance.status in ("Present", "Half Day", "Work From Home"):
        # → Check OUT
        action = "Out"

        attendance = frappe.get_doc("Attendance", last_attendance.name)
        if attendance.docstatus == 0:
            attendance.status = "Present"
            attendance.out_time = now_datetime()
            attendance.save()
            attendance.submit()
        elif attendance.docstatus == 1:
            # Already submitted — update out_time
            frappe.db.set_value(
                "Attendance",
                attendance.name,
                "out_time",
                now_datetime(),
                update_modified=True,
            )
            frappe.db.commit()

        attendance_name = attendance.name

    else:
        frappe.throw(
            _("وضعیت حضور نامعتبر: {0}").format(last_attendance.status),
            frappe.ValidationError,
        )

    now = now_datetime()

    frappe.db.commit()

    # ── Log the scan ──
    frappe.logger().info(
        f"QR Attendance: {employee.employee_name} ({employee.name}) — {action} "
        f"by {scanner} at {now} — Attendance: {attendance_name}"
    )

    return {
        "success": True,
        "action": action,
        "employee_name": employee.employee_name,
        "employee_id": employee.name,
        "time": str(now),
        "attendance_name": attendance_name,
        "message": _("{0} — {1} ثبت شد").format(
            employee.employee_name,
            _("ورود") if action == "In" else _("خروج"),
        ),
    }


# ──────────────────────────────────────────────
# API: Get QR payload for current employee
# ──────────────────────────────────────────────

@frappe.whitelist()
def get_qr_payload():
    """Get QR code content for the currently logged-in employee.

    Returns:
        { employee_id, employee_name, qr_url }
    """

    if frappe.session.user == "Guest":
        frappe.throw(
            _("لطفاً ابتدا وارد سیستم شوید"),
            frappe.AuthenticationError,
        )

    employee = _get_employee_from_session()
    if not employee:
        frappe.throw(
            _("کارمند فعالی برای این حساب کاربری یافت نشد"),
            frappe.DoesNotExistError,
        )

    base_url = frappe.utils.get_url()
    qr_url = f"{base_url}/app/attendance/scan?employee_id={employee.name}"

    return {
        "employee_id": employee.name,
        "employee_name": employee.employee_name,
        "qr_url": qr_url,
    }


# ──────────────────────────────────────────────
# API: Get today's attendance status
# ──────────────────────────────────────────────

@frappe.whitelist()
def get_today_status(employee_id: str = None):
    """Get today's attendance status for an employee.

    If employee_id is not provided, uses the logged-in employee.
    Returns:
        { has_checkin, last_action, attendance_name, employee_name }
    """

    if frappe.session.user == "Guest":
        frappe.throw(
            _("لطفاً ابتدا وارد سیستم شوید"),
            frappe.AuthenticationError,
        )

    if not employee_id:
        employee = _get_employee_from_session()
        if not employee:
            frappe.throw(_("کارمند فعال یافت نشد"), frappe.DoesNotExistError)
        employee_id = employee.name

    today = nowdate()
    last_attendance = frappe.db.get_value(
        "Attendance",
        {
            "employee": employee_id,
            "attendance_date": today,
            "docstatus": ("!=", 2),
        },
        ["name", "status", "employee_name"],
        order_by="creation desc",
        as_dict=True,
    )

    if not last_attendance:
        return {
            "has_checkin": False,
            "last_action": None,
            "attendance_name": None,
            "employee_name": None,
        }

    return {
        "has_checkin": True,
        "last_action": last_attendance.status,
        "attendance_name": last_attendance.name,
        "employee_name": last_attendance.employee_name,
    }


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────

def _get_employee_from_session():
    """Get the Employee document linked to the current session user."""
    user = frappe.session.user
    if user in ("Guest", "Administrator"):
        return None

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user, "status": "Active"},
        ["name", "employee_name", "company"],
        as_dict=True,
    )
    return employee


def _create_attendance(employee, action: str):
    """Create a new Attendance doc (draft) for the given employee."""
    attendance = frappe.new_doc("Attendance")
    attendance.employee = employee.name
    attendance.attendance_date = nowdate()
    attendance.company = employee.company
    attendance.status = "Present"
    attendance.in_time = now_datetime() if action == "In" else None
    attendance.out_time = now_datetime() if action == "Out" else None
    attendance.insert(ignore_permissions=True)
    return attendance
