# Employer Insurance Derived From Employee Share Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make future Salary Slip employer insurance derive from the actual employee insurance deduction.

**Architecture:** Keep all callers unchanged. `SalarySlip.get_employer_insurance_share()` prefers the `EI` deduction, while `SalarySlip.calculate_net_pay()` synchronizes the result after final deduction calculation so Smart Attendance refresh persists the correct field.

**Tech Stack:** Frappe v16, HRMS Python, unittest.

## Global Constraints

- Employer insurance is `EI * 23 / 7` whenever an `EI` deduction exists.
- Existing submitted Salary Slips and Journal Entries must not be modified.
- Do not change MCP or the Accounts application.

---

### Task 1: Derive employer insurance from the Salary Slip deduction

**Files:**
- Modify: `hrms/payroll/doctype/salary_slip/salary_slip.py:453-459,1061-1090`
- Modify: `hrms/tests/test_employer_insurance_share.py`

**Interfaces:**
- Consumes: `SalarySlip.deductions` rows with `abbr` and `amount`.
- Produces: `SalarySlip.get_employer_insurance_share() -> float` and an updated `employer_insurance_share_iran` after salary calculation.

- [ ] **Step 1: Write the failing test**

```python
def test_final_salary_calculation_syncs_employer_insurance_field(self):
	self.salary_slip.deductions = [frappe._dict({"abbr": "EI", "amount": 7000})]
	self.salary_slip.employer_insurance_share_iran = 1
	self.salary_slip.sync_employer_insurance_share()
	self.assertEqual(self.salary_slip.employer_insurance_share_iran, 23000)
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

def sync_employer_insurance_share(self):
	if self.meta.has_field("employer_insurance_share_iran"):
		self.employer_insurance_share_iran = self.get_employer_insurance_share()
```

- [ ] **Step 4: Run targeted tests to verify they pass**

Run: `bench --site dehati.ir run-tests --app hrms --module hrms.tests.test_employer_insurance_share`

Expected: the targeted Salary Slip tests pass.

- [ ] **Step 5: Commit**

```bash
git add hrms/payroll/doctype/salary_slip/salary_slip.py hrms/payroll/doctype/salary_slip/test_salary_slip.py
git commit -m "اصلاح محاسبه بیمه کارفرما از سهم کارمند"
```
