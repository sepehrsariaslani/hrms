# Employer Insurance Derived From Employee Share Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make future Salary Slip employer insurance derive from the actual employee insurance deduction.

**Architecture:** Keep all callers unchanged and modify only `SalarySlip.get_employer_insurance_share()`. The method will prefer the `EI` deduction and use the stored field only when the deduction is absent.

**Tech Stack:** Frappe v16, HRMS Python, unittest.

## Global Constraints

- Employer insurance is `EI * 23 / 7` whenever an `EI` deduction exists.
- Existing submitted Salary Slips and Journal Entries must not be modified.
- Do not change MCP or the Accounts application.

---

### Task 1: Derive employer insurance from the Salary Slip deduction

**Files:**
- Modify: `hrms/payroll/doctype/salary_slip/salary_slip.py:453-458`
- Modify: `hrms/payroll/doctype/salary_slip/test_salary_slip.py`

**Interfaces:**
- Consumes: `SalarySlip.deductions` rows with `abbr` and `amount`.
- Produces: `SalarySlip.get_employer_insurance_share() -> float`.

- [ ] **Step 1: Write the failing test**

```python
def test_employer_insurance_uses_employee_insurance_deduction(self):
	self.salary_slip.deductions = [frappe._dict({"abbr": "EI", "amount": 7000})]
	self.salary_slip.employer_insurance_share_iran = 1
	self.assertEqual(self.salary_slip.get_employer_insurance_share(), 23000)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bench --site dehati.ir run-tests --app hrms --module hrms.payroll.doctype.salary_slip.test_salary_slip`

Expected: the new test fails because the stored value `1` is returned.

- [ ] **Step 3: Write minimal implementation**

```python
employee_insurance = next((flt(row.amount) for row in self.deductions if row.abbr == "EI"), None)
if employee_insurance is not None:
	return employee_insurance * 23 / 7
return flt(self.get("employer_insurance_share_iran"))
```

- [ ] **Step 4: Run targeted tests to verify they pass**

Run: `bench --site dehati.ir run-tests --app hrms --module hrms.payroll.doctype.salary_slip.test_salary_slip`

Expected: the targeted Salary Slip tests pass.

- [ ] **Step 5: Commit**

```bash
git add hrms/payroll/doctype/salary_slip/salary_slip.py hrms/payroll/doctype/salary_slip/test_salary_slip.py
git commit -m "اصلاح محاسبه بیمه کارفرما از سهم کارمند"
```
