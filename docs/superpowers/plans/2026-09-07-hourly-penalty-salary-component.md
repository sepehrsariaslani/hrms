# Hourly Penalty Salary Component Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Smart Attendance hourly penalties available as the `جریمه ساعتی` deduction in every current Salary Structure on dehati.ir.

**Architecture:** Keep Smart Attendance as the source of Additional Salary records. Add one idempotent Salary Component named `جریمه ساعتی` (`HRDH`, type `Deduction`) with no formula, then add it once to each structure's deductions. Draft structures are saved in place; submitted structures are copied as amended records and their future Salary Structure Assignments are pointed to the amendment only after validation.

**Tech Stack:** Frappe Framework v16, HRMS Salary Component, Salary Structure, Salary Structure Assignment, Additional Salary.

## Global Constraints

- Scope is the `dehati.ir` site and company `عظیمیه` only.
- Do not change `پاداش ساعتی`, its formula, or existing rows.
- Create `جریمه ساعتی` only if it does not already exist; it must have type `Deduction`, abbreviation `HRDH`, no formula, and no default amount.
- Do not modify submitted Salary Slips or submitted Additional Salary records.
- A structure may contain at most one `جریمه ساعتی` deduction row.
- Never modify a submitted Salary Structure in place; create an amended version and move only future assignments.

---

### Task 1: Capture configuration and prove the missing setup

**Files:**
- Create: `hrms/tests/test_hourly_penalty_configuration.py`
- Read: `docs/superpowers/specs/2026-09-07-hourly-penalty-salary-component-design.md`

**Interfaces:**
- Consumes: `Salary Component`, `Salary Structure`, and `Salary Structure Assignment` records on `dehati.ir`.
- Produces: `TestHourlyPenaltyConfiguration.test_every_active_structure_has_one_hourly_penalty_deduction`.

- [ ] **Step 1: Write the failing verification test**

```python
import unittest

import frappe


class TestHourlyPenaltyConfiguration(unittest.TestCase):
	def test_every_active_structure_has_one_hourly_penalty_deduction(self):
		component = frappe.db.get_value(
			"Salary Component",
			"جریمه ساعتی",
			["type", "salary_component_abbr", "amount_based_on_formula", "formula"],
			as_dict=True,
		)
		self.assertEqual(component.type, "Deduction")
		self.assertEqual(component.salary_component_abbr, "HRDH")
		self.assertFalse(component.amount_based_on_formula)
		self.assertFalse(component.formula)

		for name in frappe.get_all(
			"Salary Structure",
			filters={"company": "عظیمیه", "is_active": "Yes", "docstatus": ["!=", 2]},
			pluck="name",
		):
			structure = frappe.get_doc("Salary Structure", name)
			self.assertEqual(
				sum(row.salary_component == "جریمه ساعتی" for row in structure.deductions),
				1,
				name,
			)
```

- [ ] **Step 2: Run the test to verify the current configuration fails**

Run:

```bash
bench --site dehati.ir run-tests --app hrms --module hrms.tests.test_hourly_penalty_configuration
```

Expected: failure because `جریمه ساعتی` does not exist or is absent from one or more Salary Structures.

- [ ] **Step 3: Save an immutable pre-change snapshot**

Run the following read-only query and save its JSON output in the execution notes before any write:

```python
{
	"structures": [
		{
			"name": structure.name,
			"docstatus": structure.docstatus,
			"deductions": [row.salary_component for row in structure.deductions],
		}
		for structure in (
			frappe.get_doc("Salary Structure", name)
			for name in frappe.get_all(
				"Salary Structure",
				filters={"company": "عظیمیه", "is_active": "Yes", "docstatus": ["!=", 2]},
				pluck="name",
			)
		)
	]
}
```

### Task 2: Apply the idempotent hourly-penalty configuration

**Files:**
- Modify: `hrms/tests/test_hourly_penalty_configuration.py`
- Create: `hrms/regional/iran/utils/hourly_penalty_setup.py`

**Interfaces:**
- Consumes: `ensure_hourly_penalty_configuration(company: str, effective_date: str) -> dict`.
- Produces: one `Salary Component` and a result with `updated_drafts`, `amended_structures`, `updated_assignments`, and `skipped`.

- [ ] **Step 1: Implement the idempotent setup function**

```python
def ensure_hourly_penalty_configuration(company: str, effective_date: str) -> dict:
	component = _get_or_create_hourly_penalty_component()
	result = {"component": component.name, "updated_drafts": [], "amended_structures": [], "updated_assignments": [], "skipped": []}
	for name in frappe.get_all(
		"Salary Structure",
		filters={"company": company, "is_active": "Yes", "docstatus": ["!=", 2]},
		pluck="name",
	):
		structure = frappe.get_doc("Salary Structure", name)
		if any(row.salary_component == component.name for row in structure.deductions):
			result["skipped"].append(name)
			continue
		if structure.docstatus == 0:
			structure.append("deductions", {"salary_component": component.name, "amount_based_on_formula": 0, "formula": ""})
			structure.save()
			result["updated_drafts"].append(name)
		else:
			amendment = _amend_salary_structure_with_hourly_penalty(structure, component.name)
			result["amended_structures"].append({"from": name, "to": amendment.name})
			result["updated_assignments"].extend(
				_move_future_assignments(name, amendment.name, effective_date)
			)
	return result
```

- [ ] **Step 2: Use explicit amendment and future-assignment helpers**

```python
from frappe.model.copy_doc import copy_doc


def _amend_salary_structure_with_hourly_penalty(structure, component_name):
	structure.cancel()
	amendment = copy_doc(structure)
	amendment.amended_from = structure.name
	amendment.append(
		"deductions",
		{"salary_component": component_name, "amount_based_on_formula": 0, "formula": ""},
	)
	amendment.insert()
	amendment.submit()
	return amendment


def _move_future_assignments(old_structure, new_structure, effective_date):
	updated = []
	for name in frappe.get_all(
		"Salary Structure Assignment",
		filters={
			"salary_structure": old_structure,
			"docstatus": 1,
			"from_date": [">=", effective_date],
		},
		pluck="name",
	):
		assignment = frappe.get_doc("Salary Structure Assignment", name)
		assignment.cancel()
		replacement = copy_doc(assignment)
		replacement.amended_from = assignment.name
		replacement.salary_structure = new_structure
		replacement.insert()
		replacement.submit()
		updated.append({"from": name, "to": replacement.name})
	return updated
```

- [ ] **Step 3: Create the component with the Smart Attendance contract**

```python
def _get_or_create_hourly_penalty_component():
	name = "جریمه ساعتی"
	component = frappe.db.get_value("Salary Component", name, "name")
	if component:
		doc = frappe.get_doc("Salary Component", component)
		if doc.type != "Deduction":
			frappe.throw("نوع مؤلفه جریمه ساعتی باید Deduction باشد")
		return doc

	doc = frappe.get_doc(
		{
			"doctype": "Salary Component",
			"salary_component": name,
			"salary_component_abbr": "HRDH",
			"type": "Deduction",
			"amount_based_on_formula": 0,
			"formula": "",
			"default_amount": 0,
			"do_not_include_in_total": 1,
			"remove_if_zero_valued": 1,
			"is_tax_applicable": 0,
		}
	)
	doc.insert()
	return doc
```

- [ ] **Step 4: Perform a dry run for company `عظیمیه`**

Run the function with a transaction rollback after capturing its result. Confirm every target structure is classified as draft update, amendment, or skipped before committing any document.

- [ ] **Step 5: Apply the configuration with the user-approved effective date**

Run:

```python
ensure_hourly_penalty_configuration(company="عظیمیه", effective_date="2026-09-07")
```

Expected: every active Salary Structure has exactly one `جریمه ساعتی` deduction and no existing component row changes.

- [ ] **Step 6: Re-run the verification test**

Run:

```bash
bench --site dehati.ir run-tests --app hrms --module hrms.tests.test_hourly_penalty_configuration
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add hrms/regional/iran/utils/hourly_penalty_setup.py hrms/tests/test_hourly_penalty_configuration.py
git commit -m "افزودن جریمه ساعتی به ساختارهای حقوق"
```

### Task 3: Validate Smart Attendance end-to-end without changing employee pay

**Files:**
- Test: `hrms/tests/test_hourly_penalty_configuration.py`

**Interfaces:**
- Consumes: `get_or_create_hourly_additional_salary_component(operation_type="Deduction")` from `accounts.smart_attendance_report`.
- Produces: confirmation that it resolves to `جریمه ساعتی` and that a zero-hour-free Salary Slip retains zero impact.

- [ ] **Step 1: Add the integration assertion**

```python
from accounts.smart_attendance_report import get_or_create_hourly_additional_salary_component


def test_smart_attendance_resolves_hourly_penalty_component(self):
	result = get_or_create_hourly_additional_salary_component(operation_type="Deduction")
	self.assertTrue(result["success"])
	self.assertEqual(result["component_type"], "Deduction")
	self.assertEqual(result["salary_component"], "جریمه ساعتی")
```

- [ ] **Step 2: Run the integration assertion**

Run:

```bash
bench --site dehati.ir run-tests --app hrms --module hrms.tests.test_hourly_penalty_configuration
```

Expected: PASS without creating a new Additional Salary, Salary Slip, or Journal Entry.

- [ ] **Step 3: Commit**

```bash
git add hrms/tests/test_hourly_penalty_configuration.py
git commit -m "تست اتصال جریمه ساعتی با حضور هوشمند"
```
