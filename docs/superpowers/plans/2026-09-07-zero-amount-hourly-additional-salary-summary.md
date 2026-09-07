# Zero-Amount Hourly Additional Salary Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Count zero-amount hourly rewards and penalties in Salary Slip hours summaries.

**Architecture:** Move existing hour accumulation ahead of the existing zero-value component skip; do not alter additional salary amount or component-row logic.

**Tech Stack:** Frappe v16, HRMS Python, unittest.

## Global Constraints

- Hours are counted regardless of whether their amount is zero.
- Zero-value component rows remain excluded when `remove_if_zero_valued` is true.
- No monetary totals change.

---

### Task 1: Accumulate hours before zero-value skipping

**Files:**
- Modify: `hrms/payroll/doctype/salary_slip/salary_slip.py:1756-1780`
- Create: `hrms/tests/test_zero_amount_hourly_additional_salary_summary.py`

- [ ] **Step 1: Write failing test**

```python
def test_zero_amount_hourly_earning_is_counted_in_summary(self):
	slip = SalarySlip({"doctype": "Salary Slip", "additional_earning_hours": 0})
	slip.accumulate_additional_salary_hours(
		frappe._dict({"amount_calculation_type": "Hours", "hours": 3, "hour_rate_type": ""}),
		"earnings",
	)
	self.assertEqual(slip.additional_earning_hours, 3)
```

- [ ] **Step 2: Run test and verify existing integration behavior fails**

Run: `bench --site dehati.ir run-tests --app hrms --module hrms.tests.test_zero_amount_hourly_additional_salary_summary`

Expected: failing integration assertion before the accumulation order is corrected.

- [ ] **Step 3: Move accumulation before zero-value skip**

```python
self.accumulate_additional_salary_hours(additional_salary, component_type)
if flt(additional_salary.amount) == 0 and remove_if_zero_valued:
	continue
```

- [ ] **Step 4: Run targeted tests and refresh a draft sample**

Run: `bench --site dehati.ir run-tests --app hrms --module hrms.tests.test_zero_amount_hourly_additional_salary_summary`

Expected: PASS; draft Salary Slip refresh shows the summed hours.
