# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, format_date, get_link_to_form, get_time, getdate

from erpnext.setup.doctype.employee.employee import is_holiday

import hrms
from hrms.hr.utils import validate_active_employee, validate_dates


class OverlappingAttendanceRequestError(frappe.ValidationError):
        pass


LEGACY_REQUEST_MODE = "Legacy Attendance"
CHECKIN_REQUEST_MODE = "Checkin Request"
REVIEW_PENDING = "Pending"
REVIEW_APPROVED = "Approved"
REVIEW_REJECTED = "Rejected"


class AttendanceRequest(Document):
        def validate(self):
                validate_active_employee(self.employee)
                if self.is_checkin_request():
                        self.validate_checkin_request()
                else:
                        validate_dates(self, self.from_date, self.to_date, False)
                        self.validate_half_day()
                        # Overlap is intentionally ignored for attendance requests so users can
                        # submit multiple requests on the same date window.
                        self.validate_no_attendance_to_create()

        def is_checkin_request(self) -> bool:
                request_mode = self.request_mode or LEGACY_REQUEST_MODE
                if request_mode == CHECKIN_REQUEST_MODE:
                        return True
                # Backward-compatible fallback: treat payloads with time/log fields
                # as checkin requests even if request_mode was not persisted yet.
                return bool(self.get("requested_time") or self.get("requested_log_type"))

        def validate_checkin_request(self):
                self.request_mode = CHECKIN_REQUEST_MODE
                self.reason = self.reason or "On Duty"
                self.include_holidays = 0
                self.half_day = 0
                self.half_day_date = None

                validate_dates(self, self.from_date, self.to_date or self.from_date, False)
                self.to_date = self.from_date

                if self.requested_log_type:
                        self.requested_log_type = self.requested_log_type.upper().strip()

                if self.reviewed_log_type:
                        self.reviewed_log_type = self.reviewed_log_type.upper().strip()

                if self.requested_log_type not in ("IN", "OUT"):
                        frappe.throw(_("Log Type must be either IN or OUT."))

                if self.reviewed_log_type and self.reviewed_log_type not in ("IN", "OUT"):
                        frappe.throw(_("Reviewed Log Type must be either IN or OUT."))

                if not self.requested_time:
                        frappe.throw(_("Request Time is mandatory for checkin requests."))

                self.requested_time = normalize_time_string(self.requested_time)
                if self.reviewed_time:
                        self.reviewed_time = normalize_time_string(self.reviewed_time)

                if not self.shift_request_approver:
                        self.shift_request_approver = get_shift_request_approver(self.employee)

                if not self.shift_request_approver:
                        frappe.throw(_("Please set Shift Request Approver for this employee before sending requests."))

                if not self.review_status:
                        self.review_status = REVIEW_PENDING

                if not self.can_review():
                        if self.review_status != REVIEW_PENDING:
                                frappe.throw(_("Only the assigned shift approver can change review status."))
                        if self.reviewed_log_type or self.reviewed_time or self.review_comment:
                                if self.is_new():
                                        # silently clear reviewer-only fields for new submissions by regular employees
                                        self.reviewed_log_type = None
                                        self.reviewed_time = None
                                        self.review_comment = None
                                else:
                                        frappe.throw(_("Only the assigned shift approver can edit reviewed values."))

                self.validate_duplicate_checkin_request()

        def validate_duplicate_checkin_request(self):
                existing = frappe.db.exists(
                        "Attendance Request",
                        {
                                "name": ("!=", self.name),
                                "employee": self.employee,
                                "request_mode": CHECKIN_REQUEST_MODE,
                                "from_date": self.from_date,
                                "requested_log_type": self.requested_log_type,
                                "requested_time": self.requested_time,
                                "docstatus": ("!=", 2),
                        },
                )
                if existing:
                        frappe.throw(
                                _("A checkin request with the same employee, date, log type and time already exists: {0}").format(
                                        get_link_to_form("Attendance Request", existing)
                                )
                        )

        def validate_half_day(self):
                if self.half_day:
                        if not getdate(self.from_date) <= getdate(self.half_day_date) <= getdate(self.to_date):
                                frappe.throw(_("Half day date should be in between from date and to date"))

        def validate_no_attendance_to_create(self):
                attendance_warnings = self.get_attendance_warnings()
                attendance_request_days = date_diff(self.to_date, self.from_date) + 1
                if len(attendance_warnings) == attendance_request_days and not any(
                        warning["action"] == "Overwrite" for warning in attendance_warnings
                ):
                        frappe.throw(
                                title=_("No attendance records to create"),
                                msg=_(
                                        "Please check if employee is on leave or attendance with the same status exists for selected day(s)."
                                ),
                        )

        def validate_request_overlap(self):
                if not self.name:
                        self.name = "New Attendance Request"

                Request = frappe.qb.DocType("Attendance Request")
                overlapping_request = (
                        frappe.qb.from_(Request)
                        .select(Request.name)
                        .where(
                                (Request.employee == self.employee)
                                & (Request.docstatus < 2)
                                & (Request.name != self.name)
                                & (self.to_date >= Request.from_date)
                                & (self.from_date <= Request.to_date)
                        )
                ).run(as_dict=True)

                if overlapping_request:
                        self.throw_overlap_error(overlapping_request[0].name)

        def throw_overlap_error(self, overlapping_request: str):
                msg = _("Employee {0} already has an Attendance Request {1} that overlaps with this period").format(
                        frappe.bold(self.employee),
                        get_link_to_form("Attendance Request", overlapping_request),
                )

                frappe.throw(msg, title=_("Overlapping Attendance Request"), exc=OverlappingAttendanceRequestError)

        def on_submit(self):
                if self.is_checkin_request():
                        self.process_checkin_request_submission()
                else:
                        self.create_attendance_records()

        def on_cancel(self):
                if self.is_checkin_request():
                        self.cancel_employee_checkin()
                        return

                attendance_list = frappe.get_all(
                        "Attendance", {"employee": self.employee, "attendance_request": self.name, "docstatus": 1}
                )
                if attendance_list:
                        for attendance in attendance_list:
                                attendance_obj = frappe.get_doc("Attendance", attendance["name"])
                                attendance_obj.cancel()

        def process_checkin_request_submission(self):
                if self.review_status == REVIEW_PENDING:
                        frappe.throw(_("This checkin request must be approved or rejected before submission."))

                if self.review_status == REVIEW_REJECTED:
                        return

                if self.employee_checkin and frappe.db.exists("Employee Checkin", self.employee_checkin):
                        return

                checkin = self.create_employee_checkin()
                self.employee_checkin = checkin.name
                self.db_set("employee_checkin", checkin.name, update_modified=False)

        def create_employee_checkin(self):
                log_type = (self.reviewed_log_type or self.requested_log_type or "").upper().strip()
                if log_type not in ("IN", "OUT"):
                        frappe.throw(_("Approved requests must have a valid log type."))

                time_value = self.reviewed_time or self.requested_time
                if not time_value:
                        frappe.throw(_("Approved requests must have a valid time."))

                checkin_time = combine_date_and_time(self.from_date, time_value)
                existing = frappe.db.exists(
                        "Employee Checkin",
                        {
                                "employee": self.employee,
                                "log_type": log_type,
                                "time": checkin_time,
                        },
                )
                if existing:
                        return frappe.get_doc("Employee Checkin", existing)

                checkin = frappe.new_doc("Employee Checkin")
                checkin.employee = self.employee
                checkin.time = checkin_time
                checkin.log_type = log_type
                checkin.insert(ignore_permissions=True)
                return checkin

        def cancel_employee_checkin(self):
                if not self.employee_checkin or not frappe.db.exists("Employee Checkin", self.employee_checkin):
                        return

                checkin = frappe.get_doc("Employee Checkin", self.employee_checkin)
                if checkin.attendance:
                        frappe.throw(_("Cancel the linked attendance before removing this checkin request."))

                checkin.delete(ignore_permissions=True)

        def create_attendance_records(self):
                request_days = date_diff(self.to_date, self.from_date) + 1
                for day in range(request_days):
                        attendance_date = add_days(self.from_date, day)
                        if self.should_mark_attendance(attendance_date):
                                self.create_or_update_attendance(attendance_date)

        def create_or_update_attendance(self, date: str):
                doc = self.get_attendance_doc(date)
                status = self.get_attendance_status(date)

                if doc:
                        # update existing attendance, change the status
                        old_status = doc.status

                        if old_status != status:
                                doc.db_set({"status": status, "attendance_request": self.name})
                                if status == "Half Day":
                                        doc.db_set("half_day_status", "Absent")
                                        text = _(
                                                "Changed the status from {0} to {1} and Status for Other Half to {2} via Attendance Request"
                                        ).format(frappe.bold(old_status), frappe.bold(status), frappe.bold("Absent"))
                                else:
                                        text = _("Changed the status from {0} to {1} via Attendance Request").format(
                                                frappe.bold(old_status), frappe.bold(status)
                                        )
                                doc.add_comment(comment_type="Info", text=text)

                                frappe.msgprint(
                                        _("Updated status from {0} to {1} for date {2} in the attendance record {3}").format(
                                                frappe.bold(old_status),
                                                frappe.bold(status),
                                                frappe.bold(format_date(date)),
                                                get_link_to_form("Attendance", doc.name),
                                        ),
                                        title=_("Attendance Updated"),
                                )
                else:
                        # submit a new attendance record
                        doc = frappe.new_doc("Attendance")
                        doc.employee = self.employee
                        doc.attendance_date = date
                        doc.shift = self.shift
                        doc.company = self.company
                        doc.attendance_request = self.name
                        doc.status = status
                        doc.half_day_status = "Absent" if status == "Half Day" else None
                        doc.insert(ignore_permissions=True)
                        doc.submit()

        def should_mark_attendance(self, attendance_date: str) -> bool:
                # Check if attendance_date is a holiday
                if not self.include_holidays and is_holiday(self.employee, attendance_date):
                        frappe.msgprint(
                                _("Attendance not submitted for {0} as it is a Holiday.").format(
                                        frappe.bold(format_date(attendance_date))
                                )
                        )
                        return False

                # Check if employee is on leave
                if self.has_leave_record(attendance_date):
                        frappe.msgprint(
                                _("Attendance not submitted for {0} as {1} is on leave.").format(
                                        frappe.bold(format_date(attendance_date)), frappe.bold(self.employee)
                                )
                        )
                        return False

                return True

        def has_leave_record(self, attendance_date: str) -> str | None:
                return frappe.db.exists(
                        "Leave Application",
                        {
                                "employee": self.employee,
                                "docstatus": 1,
                                "from_date": ("<=", attendance_date),
                                "to_date": (">=", attendance_date),
                                "status": "Approved",
                        },
                )

        def get_attendance_doc(self, attendance_date: str) -> str | None:
                attendance = frappe.db.exists(
                        "Attendance",
                        {
                                "employee": self.employee,
                                "attendance_date": attendance_date,
                                "docstatus": ("!=", 2),
                        },
                )
                return frappe.get_doc("Attendance", attendance) if attendance else None

        def get_attendance_status(self, attendance_date: str) -> str:
                if self.half_day and date_diff(getdate(self.half_day_date), getdate(attendance_date)) == 0:
                        return "Half Day"
                elif self.reason == "Work From Home":
                        return "Work From Home"
                else:
                        return "Present"

        def status_unchanged(self, attendance_date):
                new_status = self.get_attendance_status(attendance_date)
                attendance_doc = self.get_attendance_doc(attendance_date)
                if attendance_doc and attendance_doc.status == new_status:
                        return True
                return False

        def on_update(self):
                self.publish_update()

        def after_delete(self):
                self.publish_update()

        def publish_update(self):
                employee_user = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
                hrms.refetch_resource("hrms:my_attendance_requests", employee_user)
                hrms.refetch_resource("hrms:team_attendance_requests")

        @frappe.whitelist()
        def get_attendance_warnings(self) -> list:
                if self.is_checkin_request():
                        return []

                attendance_warnings = []
                request_days = date_diff(self.to_date, self.from_date) + 1

                for day in range(request_days):
                        attendance_date = add_days(self.from_date, day)

                        if not self.include_holidays and is_holiday(self.employee, attendance_date):
                                attendance_warnings.append({"date": attendance_date, "reason": "Holiday", "action": "Skip"})
                        elif self.has_leave_record(attendance_date):
                                attendance_warnings.append({"date": attendance_date, "reason": "On Leave", "action": "Skip"})
                        elif self.status_unchanged(attendance_date):
                                attendance_warnings.append(
                                        {"date": attendance_date, "reason": "Attendance status unchanged", "action": "Skip"}
                                )
                        else:
                                attendance = self.get_attendance_doc(attendance_date)
                                if attendance:
                                        attendance_warnings.append(
                                                {
                                                        "date": attendance_date,
                                                        "reason": "Attendance already marked",
                                                        "record": attendance.name,
                                                        "action": "Overwrite",
                                                }
                                        )

                return attendance_warnings

        def can_review(self, user: str | None = None) -> bool:
                user = user or frappe.session.user
                if user == "Administrator":
                        return True
                if user and user == self.shift_request_approver:
                        return True
                user_roles = set(frappe.get_roles(user))
                return bool({"HR Manager", "System Manager"} & user_roles)


def normalize_time_string(value) -> str:
        if value is None:
                return ""

        if hasattr(value, "strftime"):
                return value.strftime("%H:%M:%S")

        text = str(value).strip()
        translated = text.translate(
                str.maketrans(
                        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
                        "01234567890123456789",
                )
        )
        translated = translated.replace("：", ":").replace("٫", ":")

        try:
                return get_time(translated).strftime("%H:%M:%S")
        except Exception as error:
                frappe.throw(_("Invalid time format: {0}").format(frappe.bold(text)))
                raise error


def combine_date_and_time(work_date, time_value) -> datetime:
        date_part = getdate(work_date)
        time_part = get_time(normalize_time_string(time_value))
        return datetime.combine(date_part, time_part)


def get_shift_request_approver(employee: str) -> str | None:
        approver, department = frappe.get_cached_value(
                "Employee", employee, ["shift_request_approver", "department"]
        )
        if approver:
                return approver

        if department:
                return frappe.db.get_value(
                        "Department Approver",
                        {"parent": department, "parentfield": "shift_request_approver", "idx": 1},
                        "approver",
                )
        return None


@frappe.whitelist()
def review_attendance_checkin_request(
        name: str,
        action: str,
        reviewed_time: str | None = None,
        reviewed_log_type: str | None = None,
        comment: str | None = None,
) -> dict:
        doc = frappe.get_doc("Attendance Request", name)
        if not doc.is_checkin_request():
                frappe.throw(_("This action is only allowed for checkin-based attendance requests."))

        if not doc.can_review():
                frappe.throw(_("Only the assigned shift approver can review this request."))

        action_value = (action or "").strip().lower()
        if action_value not in {"approve", "reject"}:
                frappe.throw(_("Action must be either approve or reject."))

        if doc.docstatus == 2:
                frappe.throw(_("Cancelled requests cannot be reviewed."))

        if action_value == "approve":
                if reviewed_log_type:
                        doc.reviewed_log_type = reviewed_log_type.upper().strip()
                elif not doc.reviewed_log_type:
                        doc.reviewed_log_type = doc.requested_log_type

                if reviewed_time:
                        doc.reviewed_time = normalize_time_string(reviewed_time)
                elif not doc.reviewed_time:
                        doc.reviewed_time = doc.requested_time

                doc.review_status = REVIEW_APPROVED
        else:
                doc.review_status = REVIEW_REJECTED

        if comment:
                doc.review_comment = comment

        doc.flags.ignore_permissions = True
        doc.save(ignore_permissions=True)
        if doc.docstatus == 0:
                doc.submit()

        return {
                "name": doc.name,
                "review_status": doc.review_status,
                "docstatus": doc.docstatus,
                "employee_checkin": doc.employee_checkin,
        }
