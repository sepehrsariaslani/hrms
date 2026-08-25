# Earned Leave Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore monthly earned-leave accrual behavior and repair existing `مرخصی استحقاقی` balances on `dehati.ir`.

**Architecture:** Fix the earned-leave allocation path in `LeavePolicyAssignment`, add regression coverage around past-period accrual and future schedule state, then add a repair helper that rewrites allocation totals and schedule rows for one earned leave type on a live site without touching leave applications.

**Tech Stack:** Frappe HRMS, Python, MariaDB, bench console/execute

## Global Constraints

- Preserve existing `Leave Application` data.
- Repair `dehati.ir` as of `2026-08-08`.
- Keep annual policy allocation at `30` and monthly accrual at `2.5`.

---

### Task 1: Restore Earned-Leave Allocation Behavior

**Files:**
- Modify: `hrms/hr/doctype/leave_policy_assignment/leave_policy_assignment.py`
- Test: `hrms/hr/doctype/leave_allocation/test_earned_leaves.py`
- Test: `hrms/hr/doctype/leave_allocation/test_earned_leave_schedule.py`

**Interfaces:**
- Consumes: `LeavePolicyAssignment.get_leaves_for_passed_period()`
- Produces: correct `new_leaves_allocated` and pending future schedule rows for earned leave

- [ ] Write failing tests for earned leave not allocating the full annual quota upfront and for future schedule rows remaining pending.
- [ ] Implement the minimal fix in `LeavePolicyAssignment`.
- [ ] Verify the targeted tests or equivalent console checks reflect the restored behavior.

### Task 2: Add Live-Site Repair Helper

**Files:**
- Create: `hrms/hr/doctype/leave_allocation/earned_leave_repair.py`

**Interfaces:**
- Produces: `repair_earned_leave_allocations(leave_type_name: str, as_of_date: str | None = None, dry_run: bool = True) -> list[dict]`

- [ ] Add a repair helper that recomputes earned-leave allocations from policy assignment + date of joining.
- [ ] Update submitted allocation totals, the initial allocation ledger row, and earned leave schedule rows.
- [ ] Keep the helper generic enough to run for one earned leave type on one site.

### Task 3: Repair `dehati.ir` Data And Verify

**Files:**
- Modify at runtime: `dehati.ir` site data

**Interfaces:**
- Consumes: `repair_earned_leave_allocations(...)`
- Produces: corrected balances and schedule rows for `مرخصی استحقاقی`

- [ ] Back up or snapshot the current state with SQL queries.
- [ ] Set `max_leaves_allowed` for `مرخصی استحقاقی` back to the annual cap.
- [ ] Run the repair helper against `dehati.ir`.
- [ ] Verify final leave type settings, per-employee balances, and ledger totals.
