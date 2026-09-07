# Salary Slip Attendance Hour Breakdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a readable attendance-hours breakdown to Iranian Salary Slips.

**Architecture:** Introduce four read-only Custom Fields and derive them only from Smart Attendance report rows in the existing salary-slip summary function.

**Tech Stack:** Frappe v16, HRMS Python, Custom Fields, unittest.

## Global Constraints

- Smart Attendance is the only source of attendance numbers.
- `regular_worked_hours_iran = max(net_worked_hours_iran - overtime_hours_iran, 0)`.
- Existing fields and monetary payroll calculations remain unchanged.

---

### Task 1: Add the attendance breakdown fields

**Files:**
- Modify: `hrms/regional/iran/setup.py`

- [ ] **Step 1: Add four read-only Float fields with descriptions**

```python
{"fieldname": "presence_hours_iran", "fieldtype": "Float", "label": "ساعات حضور", "read_only": 1}
{"fieldname": "break_hours_iran", "fieldtype": "Float", "label": "ساعات استراحت", "read_only": 1}
{"fieldname": "net_worked_hours_iran", "fieldtype": "Float", "label": "ساعات کارکرد خالص", "read_only": 1}
{"fieldname": "regular_worked_hours_iran", "fieldtype": "Float", "label": "ساعات کارکرد عادی", "read_only": 1}
```

### Task 2: Derive and store the breakdown

**Files:**
- Modify: `hrms/regional/iran/utils.py`
- Create: `hrms/tests/test_smart_attendance_hour_breakdown.py`

- [ ] **Step 1: Write failing calculation test**

```python
summary = get_smart_attendance_hours_summary([
	{"employee": "EMP-1", "presence_hours": 10, "break_hours": 1, "working_hours": 9, "overtime": 2},
], "EMP-1")
self.assertEqual(summary.regular_worked_hours, 7)
```

- [ ] **Step 2: Add the helper and use it in `apply_smart_attendance_summary()`**

```python
regular_worked_hours = max(net_worked_hours - overtime_hours, 0)
```

- [ ] **Step 3: Apply Custom Fields and run targeted tests**

Run: `bench --site dehati.ir execute hrms.regional.iran.setup.make_custom_fields && bench --site dehati.ir run-tests --app hrms --module hrms.tests.test_smart_attendance_hour_breakdown`

Expected: PASS.
