# تجمیع کسری صندوق در فیش حقوقی Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** نمایش یک ردیف تجمیعی برای کسری‌های صندوق هم‌مؤلفه در هر فیش حقوقی.

**Architecture:** شرط تجمیع Additional Salary به‌جای رد کردن همه رکوردهای دارای سند مرجع، فقط مراجع مالی حساس را جدا نگه می‌دارد. نام همه Additional Salaryهای تجمیع‌شده در همان ردیف فیش حفظ می‌شود.

**Tech Stack:** Frappe v16, HRMS Python, unittest.

## Global Constraints

- کسری صندوقِ ناشی از `Cashier Reconciliation` باید تجمیع شود.
- حقوق تکراری، جایگزین ساختار، مالیات متغیر، مزایای منعطف، تعهدات و اصلاحات حقوق جدا می‌مانند.
- هیچ رکورد Additional Salary تغییر یا حذف نمی‌شود.

---

### Task 1: تجمیع رکوردهای دارای مرجع عادی

**Files:**

- Modify: `hrms/payroll/doctype/salary_slip/salary_slip.py:1810-1820`
- Create: `hrms/tests/test_additional_salary_component_aggregation.py`

- [x] **Step 1: Write the failing test**

```python
def test_cashier_reconciliation_additional_salary_is_aggregated(self):
	additional_salary = frappe._dict({
		"overwrite": 0, "is_recurring": 0,
		"ref_doctype": "Cashier Reconciliation",
	})
	component = frappe._dict({
		"variable_based_on_taxable_salary": 0,
		"accrual_component": 0, "is_flexible_benefit": 0,
	})
	self.assertTrue(SalarySlip.should_aggregate_additional_salary(None, additional_salary, component))
```

- [x] **Step 2: Run the test and verify it fails**

Run: `bench --site dehati.ir run-tests --module hrms.tests.test_additional_salary_component_aggregation`

Expected: FAIL because records with every `ref_doctype` are excluded.

- [x] **Step 3: Implement the minimal exclusion list**

```python
non_aggregable_references = {"Arrear", "Payroll Correction", "Employee Benefit Claim"}
return bool(
	... and additional_salary.ref_doctype not in non_aggregable_references ...
)
```

- [x] **Step 4: Run the targeted test and refresh a draft slip**

Run: `bench --site dehati.ir run-tests --module hrms.tests.test_additional_salary_component_aggregation`

Expected: PASS; one «کسری صندوق» row contains the sum and all source names.

- [ ] **Step 5: Commit**

```bash
git add hrms/payroll/doctype/salary_slip/salary_slip.py hrms/tests/test_additional_salary_component_aggregation.py
git commit -m "تجمیع کسری صندوق در فیش حقوقی"
```
