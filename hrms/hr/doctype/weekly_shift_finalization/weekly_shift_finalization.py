from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, get_date_str, getdate, now_datetime, nowdate

from hrms.hr.doctype.shift_assignment.shift_assignment import OverlappingShiftError
from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import (
        calculate_slot_hours,
        can_manage_employee,
        get_employee_for_user,
        get_default_duty_role_for_employee,
        get_employee_forbidden_weekdays,
        get_shift_allocator_team_overview,
        get_shift_type_for_slot,
        get_slot_templates,
        get_week_start_date,
        is_hr_user,
        is_shift_allocator,
        normalize_calendar_date,
        parse_payload,
)


class WeeklyShiftFinalization(Document):
        def before_validate(self):
                self._normalize_week()
                self._set_defaults()
                self._apply_slot_defaults()
                if not self.status:
                        self.status = "Draft"

        def validate(self):
                self._validate_permissions()
                self._validate_slot_dates()
                self._validate_duplicates()

        def before_submit(self):
                self._validate_submission()
                self.status = "Finalized"
                self.finalized_by = frappe.session.user
                self.finalized_on = now_datetime()

        def on_submit(self):
                if self.amended_from:
                        cancel_generated_assignments_for_finalization(self.amended_from)
                created = generate_shift_assignments_for_finalization(self)
                self.db_set("generated_assignments_count", len(created), update_modified=False)
                if self.amended_from:
                        frappe.db.set_value("Weekly Shift Finalization", self.amended_from, "status", "Replaced")

        def on_cancel(self):
                self.db_set("status", "Cancelled", update_modified=False)

        def _normalize_week(self):
                self.week_start_date = get_week_start_date(self.week_start_date or nowdate())
                self.week_end_date = add_days(self.week_start_date, 6)

        def _set_defaults(self):
                if not self.allocator_user:
                        self.allocator_user = frappe.session.user
                if not self.company:
                        employee = frappe.db.get_value("Employee", {"user_id": self.allocator_user, "status": "Active"}, "company")
                        if employee:
                                self.company = employee

        def _apply_slot_defaults(self):
                shift_cache = {}
                total_hours = 0.0
                for slot in self.final_slots or []:
                        if slot.slot_code and not slot.shift_type:
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
                                slot.duty_role = get_default_duty_role_for_employee(slot.employee)

                        slot.hours = calculate_slot_hours(slot.start_time, slot.end_time)
                        total_hours += flt(slot.hours)

                self.generated_assignments_count = self.generated_assignments_count or 0
                self.total_hours = round(total_hours, 2)
                self.total_slots = len(self.final_slots or [])

        def _validate_permissions(self):
                if (
                        self.docstatus == 1
                        and self._action != "submit"
                        and not self.flags.ignore_validate_update_after_submit
                ):
                        frappe.throw(_("Submitted finalizations cannot be edited."))

                if not (is_hr_user(frappe.session.user) or is_shift_allocator(frappe.session.user)):
                        frappe.throw(_("You are not allowed to manage final shift allocations."), frappe.PermissionError)

                for slot in self.final_slots or []:
                        if not can_manage_employee(frappe.session.user, slot.employee):
                                frappe.throw(_("You are not allowed to finalize shifts for employee {0}.").format(slot.employee), frappe.PermissionError)

        def _validate_slot_dates(self):
                start = getdate(self.week_start_date)
                end = getdate(self.week_end_date)
                for slot in self.final_slots or []:
                        if not slot.work_date:
                                continue
                        date = getdate(slot.work_date)
                        if date < start or date > end:
                                frappe.throw(_("Row #{0}: Work Date must be inside this week.").format(slot.idx))

        def _validate_duplicates(self):
                seen = set()
                for slot in self.final_slots or []:
                        if not (slot.employee and slot.work_date and slot.slot_code):
                                continue
                        key = (slot.employee, get_date_str(slot.work_date), slot.slot_code)
                        if key in seen:
                                frappe.throw(_("Row #{0}: Duplicate final slot for employee/date/slot.").format(slot.idx))
                        seen.add(key)

        def _validate_submission(self):
                if not self.final_slots:
                        frappe.throw(_("Please add at least one final slot before submission."))

                for slot in self.final_slots or []:
                        if not slot.employee:
                                frappe.throw(_("Row #{0}: Employee is mandatory.").format(slot.idx))
                        if not slot.work_date:
                                frappe.throw(_("Row #{0}: Work Date is mandatory.").format(slot.idx))
                        if not slot.slot_code:
                                frappe.throw(_("Row #{0}: Slot is mandatory.").format(slot.idx))
                        if not slot.shift_type:
                                frappe.throw(_("Row #{0}: Shift Type is mandatory.").format(slot.idx))
                        if not slot.duty_role:
                                frappe.throw(_("Row #{0}: Final Duty Role is mandatory.").format(slot.idx))
                        if not slot.start_time or not slot.end_time:
                                frappe.throw(_("Row #{0}: Start/End Time is mandatory.").format(slot.idx))

                        forbidden_days = get_employee_forbidden_weekdays(slot.employee)
                        if getdate(slot.work_date).weekday() in forbidden_days:
                                frappe.throw(_("Row #{0}: This date is forbidden for selected employee.").format(slot.idx))


@frappe.whitelist()
def get_weekly_shift_finalization_context(week_start_date: str | None = None) -> dict:
        user = frappe.session.user
        if not (is_hr_user(user) or is_shift_allocator(user)):
                frappe.throw(_("You are not allowed to access weekly shift finalization."), frappe.PermissionError)

        week_start = get_week_start_date(week_start_date or nowdate())
        overview = get_shift_allocator_team_overview(week_start)

        finalization_name = frappe.db.get_value(
                "Weekly Shift Finalization",
                {
                        "allocator_user": user,
                        "week_start_date": week_start,
                        "docstatus": ("!=", 2),
                },
                "name",
                order_by="modified desc",
        )
        finalization_doc = frappe.get_doc("Weekly Shift Finalization", finalization_name) if finalization_name else None

        return {
                "week_start_date": week_start,
                "week_end_date": add_days(week_start, 6),
                "team_employees": overview.get("employees") or [],
                "finalization": serialize_finalization(finalization_doc) if finalization_doc else None,
                "slot_templates": get_slot_templates(),
        }


@frappe.whitelist()
def upsert_weekly_shift_finalization(payload: str | dict | None = None) -> dict:
        data = parse_payload(payload)
        user = frappe.session.user
        week_start = get_week_start_date(data.get("week_start_date") or nowdate())
        rows = data.get("final_slots") or []
        name = data.get("name")

        if not (is_hr_user(user) or is_shift_allocator(user)):
                frappe.throw(_("You are not allowed to edit weekly shift finalization."), frappe.PermissionError)

        if name:
                doc = frappe.get_doc("Weekly Shift Finalization", name)
                if doc.docstatus != 0:
                        frappe.throw(_("Only draft finalizations can be edited."))
                if doc.allocator_user != user and not is_hr_user(user):
                        frappe.throw(_("You are not allowed to edit this finalization."), frappe.PermissionError)
        else:
                doc = frappe.new_doc("Weekly Shift Finalization")
                doc.allocator_user = user

        if not doc.company:
                company = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "company")
                doc.company = company

        doc.week_start_date = week_start
        doc.week_end_date = add_days(week_start, 6)
        doc.status = "Draft"
        doc.final_slots = []

        for row in rows:
                doc.append(
                        "final_slots",
                        {
                                "employee": row.get("employee"),
                                "work_date": normalize_calendar_date(row.get("work_date")),
                                "slot_code": row.get("slot_code"),
                                "shift_type": row.get("shift_type"),
                                "start_time": row.get("start_time"),
                                "end_time": row.get("end_time"),
                                "duty_role": row.get("duty_role"),
                                "is_manual": row.get("is_manual", 0),
                                "source_plan": row.get("source_plan"),
                                "source_slot": row.get("source_slot"),
                                "was_requested": row.get("was_requested", 0),
                        },
                )

        doc.flags.ignore_permissions = True
        doc.save(ignore_permissions=True)
        return serialize_finalization(doc)


@frappe.whitelist()
def finalize_weekly_shift_finalization(finalization_name: str) -> dict:
        doc = frappe.get_doc("Weekly Shift Finalization", finalization_name)
        if doc.docstatus != 0:
                frappe.throw(_("Only draft finalizations can be submitted."))
        if doc.allocator_user != frappe.session.user and not is_hr_user(frappe.session.user):
                frappe.throw(_("You are not allowed to finalize this document."), frappe.PermissionError)

        doc.flags.ignore_permissions = True
        doc.submit()
        doc.add_comment("Info", _("Final weekly allocation submitted and applied."))
        return serialize_finalization(doc)


@frappe.whitelist()
def create_weekly_shift_finalization_amendment(source_finalization_name: str) -> dict:
        source_doc = frappe.get_doc("Weekly Shift Finalization", source_finalization_name)
        if source_doc.docstatus != 1:
                frappe.throw(_("Only submitted finalizations can be amended."))
        if source_doc.allocator_user != frappe.session.user and not is_hr_user(frappe.session.user):
                frappe.throw(_("You are not allowed to create an amendment for this finalization."), frappe.PermissionError)

        amendment = frappe.copy_doc(source_doc)
        amendment.docstatus = 0
        amendment.status = "Draft"
        amendment.finalized_by = ""
        amendment.finalized_on = None
        amendment.generated_assignments_count = 0
        amendment.amended_from = ""

        amendment.flags.ignore_permissions = True
        amendment.insert(ignore_permissions=True)
        amendment.db_set("amended_from", source_doc.name, update_modified=False)
        amendment.amended_from = source_doc.name
        amendment.add_comment("Info", _("Amendment created from {0}.").format(frappe.bold(source_doc.name)))
        return serialize_finalization(amendment)


@frappe.whitelist()
def get_employee_finalized_shift_slots(
        employee: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
) -> list[dict]:
        user = frappe.session.user
        current_employee = get_employee_for_user(user)
        target_employee = employee or current_employee
        if not target_employee:
                return []

        if (
                target_employee != current_employee
                and not is_hr_user(user)
                and not can_manage_employee(user, target_employee)
        ):
                frappe.throw(_("You are not allowed to access this employee's finalized shifts."), frappe.PermissionError)

        filters: dict = {
                "parenttype": "Weekly Shift Finalization",
                "employee": target_employee,
        }
        if from_date:
                filters["work_date"] = [">=", normalize_calendar_date(from_date)]
        if to_date:
                work_date_filter = filters.get("work_date")
                if work_date_filter:
                        filters["work_date"] = ["between", [work_date_filter[1], normalize_calendar_date(to_date)]]
                else:
                        filters["work_date"] = ["<=", normalize_calendar_date(to_date)]

        slot_rows = frappe.get_all(
                "Weekly Shift Finalization Slot",
                filters=filters,
                fields=[
                        "name",
                        "parent",
                        "employee",
                        "work_date",
                        "slot_code",
                        "shift_type",
                        "start_time",
                        "end_time",
                        "duty_role",
                ],
                order_by="work_date asc, slot_code asc",
        )
        if not slot_rows:
                return []

        parent_names = sorted({row.parent for row in slot_rows if row.get("parent")})
        if not parent_names:
                return []

        finalized_names = set(
                frappe.get_all(
                        "Weekly Shift Finalization",
                        filters={"name": ["in", parent_names], "docstatus": 1},
                        pluck="name",
                )
        )
        if not finalized_names:
                return []

        result = []
        for row in slot_rows:
                if row.parent not in finalized_names:
                        continue
                result.append(
                        {
                                "name": row.name,
                                "employee": row.employee,
                                "work_date": get_date_str(row.work_date) if row.work_date else None,
                                "slot_code": row.slot_code,
                                "shift_type": row.shift_type,
                                "start_time": str(row.start_time) if row.start_time else None,
                                "end_time": str(row.end_time) if row.end_time else None,
                                "duty_role": row.duty_role,
                                "weekly_shift_finalization": row.parent,
                        }
                )

        return result


def serialize_finalization(doc: WeeklyShiftFinalization | None) -> dict | None:
        if not doc:
                return None

        payload = doc.as_dict()
        payload["final_slots"] = sorted(
                [
                        {
                                "name": d.name,
                                "employee": d.employee,
                                "employee_name": d.employee_name,
                                "work_date": get_date_str(d.work_date) if d.work_date else None,
                                "slot_code": d.slot_code,
                                "shift_type": d.shift_type,
                                "start_time": str(d.start_time) if d.start_time else None,
                                "end_time": str(d.end_time) if d.end_time else None,
                                "hours": flt(d.hours),
                                "duty_role": d.duty_role,
                                "is_manual": d.is_manual,
                                "source_plan": d.source_plan,
                                "source_slot": d.source_slot,
                                "was_requested": d.was_requested,
                        }
                        for d in doc.final_slots or []
                ],
                key=lambda d: ((d.get("employee") or ""), (d.get("work_date") or ""), (d.get("slot_code") or "")),
        )
        return payload


def cancel_generated_assignments_for_finalization(finalization_name: str) -> None:
        if not frappe.db.has_column("Shift Assignment", "weekly_shift_finalization"):
                return

        assignments = frappe.get_all(
                "Shift Assignment",
                filters={"weekly_shift_finalization": finalization_name, "docstatus": 1},
                pluck="name",
        )
        for assignment_name in assignments:
                try:
                        assignment_doc = frappe.get_doc("Shift Assignment", assignment_name)
                        assignment_doc.flags.ignore_permissions = True
                        assignment_doc.flags.ignore_links = True
                        assignment_doc.cancel()
                except Exception:
                        pass


def generate_shift_assignments_for_finalization(doc: WeeklyShiftFinalization) -> list[str]:
        created = []
        for row in sorted(
                doc.final_slots or [], key=lambda d: ((d.employee or ""), get_date_str(d.work_date), d.slot_code or "")
        ):
                assignment = frappe.new_doc("Shift Assignment")
                assignment.employee = row.employee
                assignment.company = doc.company
                assignment.shift_type = row.shift_type
                assignment.start_date = row.work_date
                assignment.end_date = row.work_date
                assignment.status = "Active"

                if frappe.db.has_column("Shift Assignment", "weekly_shift_finalization"):
                        assignment.weekly_shift_finalization = doc.name
                if frappe.db.has_column("Shift Assignment", "weekly_shift_finalization_slot"):
                        assignment.weekly_shift_finalization_slot = row.name
                if frappe.db.has_column("Shift Assignment", "generated_from_finalization"):
                        assignment.generated_from_finalization = 1

                assignment.flags.ignore_permissions = True
                try:
                        assignment.insert(ignore_permissions=True)
                        assignment.submit()
                except OverlappingShiftError as error:
                        frappe.throw(
                                _("Shift overlap for employee {0} on {1}: {2}").format(
                                        frappe.bold(row.employee),
                                        frappe.bold(get_date_str(row.work_date)),
                                        frappe.bold(str(error)),
                                )
                        )
                created.append(assignment.name)

        return created
