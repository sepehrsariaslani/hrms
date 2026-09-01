# Payroll Entry Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Safely recover failed payroll accruals and record employee-level salary liability.

**Architecture:** A guarded `PayrollEntry` server method will reuse the existing accrual-Journal-Entry logic for submitted, unlinked slips. A Payroll Entry button calls it only for the recovery state. The hourly-leave defect is fixed independently with a regression test.

**Tech Stack:** Frappe, ERPNext, HRMS, Python unittest.

## Global Constraints

- Never alter payment Journal Entries during recovery.
- Validate all Salary Component accounts before any Journal Entry is created.
- Reject a Payroll Entry that already has an accrual Journal Entry.
- Use existing employee-wise Payroll Settings for Employee parties.

---

### Task 1: Recovery service and tests

**Files:**
- Modify: `hrms/payroll/doctype/payroll_entry/payroll_entry.py`
- Test: `hrms/payroll/doctype/payroll_entry/test_payroll_entry.py`

- [ ] Write failing tests for recovering submitted, unlinked slips and rejecting a second recovery.
- [ ] Run the focused payroll-entry test module and verify the method is absent.
- [ ] Add `recover_accrual_journal_entry`: find submitted unlinked slips; pre-validate all component accounts; reject existing accrual; call `make_accrual_jv_entry`; then mark the entry submitted and clear the error only after successful submission.
- [ ] Run the payroll-entry test module again and verify it passes.
- [ ] Commit: `افزودن بازیابی امن سند تعهد حقوق`.

### Task 2: Recovery form action

**Files:**
- Modify: `hrms/payroll/doctype/payroll_entry/payroll_entry.js`

- [ ] Verify no recovery action exists in the current form.
- [ ] Add Persian `بازیابی سند تعهد حقوق` only for a failed submitted Payroll Entry with unlinked submitted slips.
- [ ] Confirm that the dialog says it creates a liability only and does not pay employees.
- [ ] Build the HRMS assets and verify the action reaches the server method.
- [ ] Commit: `افزودن دکمه بازیابی سند تعهد حقوق`.

### Task 3: Hourly leave regression

**Files:**
- Modify: `hrms/payroll/doctype/salary_slip/salary_slip.py`
- Test: `hrms/payroll/doctype/salary_slip/test_salary_slip.py`

- [ ] Write a failing test: two leave hours beginning at `09:00` must end at `11:00`.
- [ ] Run the test and verify the existing code produces a time before `09:00`.
- [ ] Calculate `to_time` from the declared `from_time`, not midnight.
- [ ] Run salary-slip and payroll-entry test modules.
- [ ] Commit: `اصلاح زمان پایان مرخصی ساعتی در فیش حقوقی`.

### Task 4: dehati.ir recovery verification

- [ ] Confirm `حق اولاد` has an account for `عظیمیه` and no accrual Journal Entry exists.
- [ ] Enable employee-wise payroll accounting.
- [ ] Recover `HR-PRUN-2026-00001` once.
- [ ] Verify all payable credits are tagged with their Employee, all slips link to one submitted accrual Journal Entry, and the Payroll Entry error clears.
- [ ] Do not submit, cancel, or edit the existing Bank Entry draft.
