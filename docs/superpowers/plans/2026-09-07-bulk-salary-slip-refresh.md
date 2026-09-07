# Bulk Salary Slip Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe draft-only bulk refresh for Salary Slips in the list view.

**Architecture:** A whitelisted Python function performs independent savepoint-protected refreshes and returns categorized results. The existing Salary Slip list JavaScript invokes it for selected rows and displays the summary.

**Tech Stack:** Frappe v16, HRMS Python, Frappe list-view JavaScript, unittest.

## Global Constraints

- Only Salary Slips with `docstatus == 0` may be refreshed.
- Each item failure must not roll back successful selected items.
- No submitted/cancelled Salary Slip, Journal Entry, or Payroll Entry is modified.

---

### Task 1: Add server-side bulk refresh

**Files:**
- Modify: `hrms/payroll/doctype/salary_slip/salary_slip.py`
- Create: `hrms/tests/test_bulk_salary_slip_refresh.py`

**Interfaces:**
- Produces: `bulk_refresh_from_smart_attendance(salary_slips) -> dict` with `refreshed`, `skipped`, and `errors` lists.

- [ ] **Step 1: Write failing tests**

```python
def test_rejects_empty_selection(self):
	with self.assertRaises(frappe.ValidationError):
		bulk_refresh_from_smart_attendance([])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bench --site dehati.ir run-tests --app hrms --module hrms.tests.test_bulk_salary_slip_refresh`

Expected: FAIL because the bulk refresh function does not exist.

- [ ] **Step 3: Implement draft-only independent processing**

```python
for name in salary_slips:
	frappe.db.savepoint(savepoint)
	try:
		slip = frappe.get_doc("Salary Slip", name)
		if slip.docstatus != 0:
			skipped.append(name)
			continue
		slip.refresh_from_smart_attendance()
		refreshed.append(name)
	except Exception as exc:
		frappe.db.rollback(save_point=savepoint)
		errors.append({"salary_slip": name, "error": str(exc)})
```

- [ ] **Step 4: Run targeted tests**

Run: `bench --site dehati.ir run-tests --app hrms --module hrms.tests.test_bulk_salary_slip_refresh`

Expected: PASS.

### Task 2: Add list-view action

**Files:**
- Modify: `hrms/public/js/salary_slip_list_accounting.js`

- [ ] **Step 1: Add confirmation and server call**

```javascript
frappe.confirm(__("فقط فیش‌های پیش‌نویس انتخاب‌شده رفرش می‌شوند."), () => {
	frappe.call({ method: "hrms.payroll.doctype.salary_slip.salary_slip.bulk_refresh_from_smart_attendance", args: { salary_slips: slips } });
});
```

- [ ] **Step 2: Display result counts and refresh list**

```javascript
frappe.msgprint(__("{0} فیش رفرش شد؛ {1} فیش نادیده گرفته شد؛ {2} خطا داشت.", [refreshed, skipped, errors]));
listview.refresh();
```

- [ ] **Step 3: Run formatting/syntax and server tests**

Run: `python3 -m py_compile hrms/payroll/doctype/salary_slip/salary_slip.py && bench --site dehati.ir run-tests --app hrms --module hrms.tests.test_bulk_salary_slip_refresh`

Expected: PASS.
