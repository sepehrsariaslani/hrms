# Smart Attendance Shortage Hours Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with verification checkpoints.

**Goal:** Make Smart Attendance and Iranian salary-slip shortage hours agree for approved leave days and overnight check-ins.

**Architecture:** Keep Smart Attendance as the single calculation source. Extend its input window by one day for overnight pairing, mark cross-day pairs as consumed, and apply leave precedence after attendance-shape branches. Make salary-slip shortage lookup call the same report calculation fresh instead of trusting a stale stored value.

**Tech Stack:** Frappe/ERPNext HRMS, Python, Frappe integration tests, MariaDB-backed site `dehati.ir`.

## Global Constraints

- Do not modify raw Employee Checkin, Attendance, Leave Application, or Shift Assignment records.
- Do not hard-code `HR-EMP-00015`; the behavior must be generic.
- Keep draft salary slips unsubmitted.
- Preserve current overtime and ordinary minute-level shortage behavior.

---

### Task 1: Add failing Smart Attendance regression tests

**Files:**
- Modify: `hrms/hr/report/smart_attendance_report/test_smart_attendance_report.py`
- Test helper: `hrms/hr/doctype/employee_checkin/test_employee_checkin.py:make_checkin`

**Interfaces:**
- Consumes: `get_data`, `setup_shift_type`, `make_employee`, `create_leave_allocation`, `make_leave_application`, and `make_checkin`.
- Produces: failing tests proving the desired overnight and leave precedence behavior.

- [ ] **Step 1: Write the failing tests**

Add `datetime` and `make_checkin` imports, then add these tests to `TestSmartAttendanceReport`:

```python
def test_last_period_day_pairs_with_next_day_overnight_exit(self):
    shift = setup_shift_type(
        shift_type="Smart Attendance Overnight Boundary Shift",
        start_time="15:00:00",
        end_time="00:30:00",
        standard_working_hours=7.33,
    )
    employee = make_employee(
        "smart.attendance.overnight.boundary@example.com",
        company="_Test Company",
        default_shift=shift.name,
    )
    make_checkin(employee, datetime(2026, 8, 10, 15, 30), "IN")
    make_checkin(employee, datetime(2026, 8, 11, 0, 3), "OUT")

    rows = get_data(
        {
            "employee": employee,
            "from_date": date(2026, 8, 10),
            "to_date": date(2026, 8, 10),
        }
    )

    self.assertEqual(len(rows), 1)
    self.assertEqual(rows[0]["time_off"], 0)
    self.assertEqual(rows[0]["actual_end"], "00:03(+1)")
    self.assertEqual(rows[0]["log_status"], "✅ کامل")

def test_approved_leave_overrides_single_stray_checkin_shortage(self):
    shift = setup_shift_type(
        shift_type="Smart Attendance Leave Stray Log Shift",
        start_time="08:00:00",
        end_time="16:20:00",
        standard_working_hours=7.33,
    )
    employee = make_employee(
        "smart.attendance.leave.stray@example.com",
        company="_Test Company",
        default_shift=shift.name,
    )
    create_leave_allocation(
        employee=employee,
        leave_type="_Test Leave Type",
        from_date=date(2026, 8, 1),
        to_date=date(2026, 8, 31),
        new_leaves_allocated=15,
    ).insert().submit()
    make_leave_application(employee, date(2026, 8, 12), date(2026, 8, 12), "_Test Leave Type")
    make_checkin(employee, datetime(2026, 8, 12, 0, 1), "OUT")

    rows = get_data(
        {
            "employee": employee,
            "from_date": date(2026, 8, 12),
            "to_date": date(2026, 8, 12),
        }
    )

    self.assertEqual(rows[0]["leave_hours"], 7.33)
    self.assertEqual(rows[0]["time_off"], 0)
    self.assertTrue(rows[0]["has_issue"])
```

- [ ] **Step 2: Run the focused tests and verify they fail for the intended reasons**

Run:

```bash
docker exec den-v16-backend bash -lc 'cd /home/frappe/frappe-bench && bench --site dehati.ir run-tests --app hrms --module hrms.hr.report.smart_attendance_report.test_smart_attendance_report'
```

Expected: the two new tests fail because the report excludes the next-day OUT and leaves the default `time_off` in the single-log branch.

### Task 2: Fix Smart Attendance pairing and leave precedence

**Files:**
- Modify: `hrms/hr/report/smart_attendance_report/smart_attendance_report.py:315-330, 390-460, 880-900`

**Interfaces:**
- Consumes: the existing `get_data(filters)` attendance pipeline.
- Produces: rows whose cross-day pairs and approved leave shortage values are correct.

- [ ] **Step 1: Extend the check-in query by one day**

Create a local `checkin_to_date = add_days(filters.get("to_date"), 1)` and bind it to the SQL upper bound. Keep the report iteration itself bounded by the original `to_date`.

- [ ] **Step 2: Mark a directly paired cross-day OUT as consumed**

In the `if out_log:` branch, after the pair is created, add the OUT name to `used_overnight_logs` when `out_log.work_date != in_log.work_date`. This covers cross-day pairs found by the IN scan, while the existing OUT scan continues to cover an OUT that closes a previously unpaired IN.

- [ ] **Step 3: Apply approved leave precedence after all attendance branches**

Before filtering/appending the row, keep the existing holiday behavior and set `row["time_off"] = 0` whenever `row["leave_hours"]` is positive on a non-holiday. Do not clear `has_issue`, `log_status`, or the raw log display, so incomplete physical attendance remains auditable.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run the same module command from Task 1. Expected: all tests pass, including both new regressions.

### Task 3: Make Salary Slip shortage lookup fresh and consistent

**Files:**
- Modify: `hrms/payroll/doctype/salary_slip/salary_slip.py:2766-2785`
- Test: `hrms/payroll/doctype/salary_slip/test_salary_slip.py`

**Interfaces:**
- Consumes: the corrected `get_data` function.
- Produces: `SalarySlip.get_shortage_hours()` that returns the current Smart Attendance shortage even when the document has an old nonzero `shortage_hours_iran`.

- [ ] **Step 1: Write the failing stale-value test**

Add `datetime`, `make_checkin`, and `setup_shift_type` imports, then add this method to `TestSalarySlip`:

```python
def test_salary_slip_shortage_uses_fresh_smart_attendance(self):
    shift = setup_shift_type(
        shift_type="Salary Slip Fresh Shortage Shift",
        start_time="08:00:00",
        end_time="16:20:00",
        standard_working_hours=7.33,
    )
    employee = make_employee(
        "salary.slip.fresh.shortage@example.com",
        company="_Test Company",
        default_shift=shift.name,
    )
    make_checkin(employee, datetime(2026, 8, 20, 8, 0), "IN")
    make_checkin(employee, datetime(2026, 8, 20, 16, 20), "OUT")

    slip = frappe.new_doc("Salary Slip")
    slip.employee = employee
    slip.start_date = date(2026, 8, 20)
    slip.end_date = date(2026, 8, 20)
    slip.shortage_hours_iran = 99

    self.assertEqual(slip.get_shortage_hours(), 0)
```

- [ ] **Step 2: Run the single test and verify it fails**

Run:

```bash
docker exec den-v16-backend bash -lc 'cd /home/frappe/frappe-bench && bench --site dehati.ir run-tests --app hrms --module hrms.payroll.doctype.salary_slip.test_salary_slip --test TestSalarySlip.test_salary_slip_shortage_uses_fresh_smart_attendance'
```

Expected: FAIL because the current method returns the stored `99` before querying Smart Attendance.

- [ ] **Step 3: Remove the stale-value early return**

Always call `get_data` for the employee and slip dates, sum `time_off`, and return the rounded total. Keep the existing exception fallback of `0`.

- [ ] **Step 4: Run the single test and verify it passes**

Run the same command. Expected: PASS.

### Task 4: Verify the real Khordad draft slip

**Files:**
- No source files; update only the existing draft document in site `dehati.ir`.

**Interfaces:**
- Consumes: corrected report and salary-slip logic.
- Produces: refreshed draft `Sal Slip/HR-EMP-00015/00002` with no submission.

- [ ] **Step 1: Run focused Smart Attendance and Salary Slip tests**

Run both module test commands and confirm no failures.

- [ ] **Step 2: Refresh the target draft slip**

Call the existing `refresh_from_smart_attendance` method for `Sal Slip/HR-EMP-00015/00002` with `ignore_permissions=True` while preserving `docstatus = 0`.

- [ ] **Step 3: Compare the live report and draft slip**

Recompute the Smart Attendance summary for `2026-05-22` through `2026-06-21` and compare `shortage_hours_iran`, `overtime_hours_iran`, `presence_hours_iran`, and `net_worked_hours_iran` on the draft. Confirm the shortage is minute-level rather than approximately 15 hours.

- [ ] **Step 4: Run final repository checks**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors, only the intended source/test changes, and the target slip remains draft.
