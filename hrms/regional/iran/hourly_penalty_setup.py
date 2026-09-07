from __future__ import annotations

import frappe
from frappe.utils import cint


HOURLY_PENALTY_COMPONENT = "جریمه ساعتی"
HOURLY_PENALTY_ABBR = "HRDH"


def clean_dehati_amended_salary_structure_names(company: str = "عظیمیه") -> dict:
	"""Delete cancelled predecessors and restore clean names to their active amendments."""
	if company != "عظیمیه":
		frappe.throw("این عملیات فقط برای شرکت عظیمیه مجاز است")

	cancelled_names = frappe.get_all(
		"Salary Structure",
		filters={"company": company, "docstatus": 2},
		pluck="name",
	)
	if not cancelled_names:
		return {"deleted_structures": [], "deleted_assignments": [], "renamed_structures": {}}

	replacements = {}
	for old_name in cancelled_names:
		active_names = frappe.get_all(
			"Salary Structure",
			filters={"company": company, "docstatus": ["!=", 2], "amended_from": old_name},
			pluck="name",
		)
		if len(active_names) != 1:
			frappe.throw(f"برای ساختار لغوشده {old_name} باید دقیقاً یک نسخهٔ فعال وجود داشته باشد")
		replacements[old_name] = active_names[0]

	frappe.db.savepoint("clean_hourly_penalty_structure_names")
	try:
		cancelled_assignments = frappe.get_all(
			"Salary Structure Assignment",
			filters={"company": company, "docstatus": 2, "salary_structure": ["in", cancelled_names]},
			pluck="name",
		)
		active_assignments = frappe.get_all(
			"Salary Structure Assignment",
			filters={"company": company, "docstatus": ["!=", 2], "amended_from": ["!=", ""]},
			pluck="name",
		)
		for name in active_assignments:
			frappe.db.set_value("Salary Structure Assignment", name, "amended_from", "", update_modified=False)
		for name in cancelled_assignments:
			frappe.delete_doc("Salary Structure Assignment", name, force=1, ignore_permissions=True)

		for old_name, new_name in replacements.items():
			frappe.db.set_value("Salary Structure", new_name, "amended_from", "", update_modified=False)
			frappe.delete_doc("Salary Structure", old_name, force=1, ignore_permissions=True)
			frappe.rename_doc("Salary Structure", new_name, old_name, force=True)

		frappe.db.commit()
		return {
			"deleted_structures": cancelled_names,
			"deleted_assignments": cancelled_assignments,
			"renamed_structures": {new: old for old, new in replacements.items()},
		}
	except Exception:
		frappe.db.rollback(save_point="clean_hourly_penalty_structure_names")
		raise


def rebuild_dehati_payroll_for_hourly_penalty(company: str = "عظیمیه") -> dict:
	"""Remove incorrect payroll documents and make hourly penalties usable in every active structure."""
	if company != "عظیمیه":
		frappe.throw("این عملیات فقط برای شرکت عظیمیه مجاز است")

	frappe.db.savepoint("hourly_penalty_rebuild")
	try:
		result = _cancel_and_remove_salary_slips(company)
		result.update(_configure_hourly_penalty(company))
		frappe.db.commit()
		return result
	except Exception:
		frappe.db.rollback(save_point="hourly_penalty_rebuild")
		raise


def _cancel_and_remove_salary_slips(company: str) -> dict:
	slip_names = frappe.get_all(
		"Salary Slip", filters={"company": company, "docstatus": ["!=", 2]}, pluck="name"
	)
	journal_names = sorted(
		{
			name
			for name in frappe.get_all(
				"Salary Slip",
				filters={"name": ["in", slip_names], "journal_entry": ["!=", ""]},
				pluck="journal_entry",
			)
			if name
		}
	)
	payroll_names = frappe.get_all(
		"Payroll Entry", filters={"company": company, "docstatus": ["!=", 2]}, pluck="name"
	)

	cancelled_journals = []
	for name in journal_names:
		journal = frappe.get_doc("Journal Entry", name)
		if journal.docstatus == 1:
			journal.cancel()
			cancelled_journals.append(name)

	cancelled_slips = []
	for name in slip_names:
		slip = frappe.get_doc("Salary Slip", name)
		if slip.docstatus == 1:
			slip.cancel()
			cancelled_slips.append(name)

	for name in slip_names:
		frappe.delete_doc("Salary Slip", name, force=1, ignore_permissions=True)

	cancelled_payroll_entries = []
	for name in payroll_names:
		payroll = frappe.get_doc("Payroll Entry", name)
		if payroll.docstatus == 1:
			payroll.cancel()
			cancelled_payroll_entries.append(name)

	return {
		"cancelled_journal_entries": cancelled_journals,
		"cancelled_salary_slips": cancelled_slips,
		"deleted_salary_slips": slip_names,
		"cancelled_payroll_entries": cancelled_payroll_entries,
	}


def _configure_hourly_penalty(company: str) -> dict:
	component = _get_or_create_hourly_penalty_component()
	structures = [
		frappe.get_doc("Salary Structure", name)
		for name in frappe.get_all(
			"Salary Structure",
			filters={"company": company, "is_active": "Yes", "docstatus": ["!=", 2]},
			pluck="name",
		)
	]
	submitted = [structure for structure in structures if structure.docstatus == 1]
	submitted_names = [structure.name for structure in submitted]
	assignment_names = frappe.get_all(
		"Salary Structure Assignment",
		filters={"company": company, "docstatus": 1, "salary_structure": ["in", submitted_names]},
		pluck="name",
	)

	for name in assignment_names:
		frappe.get_doc("Salary Structure Assignment", name).cancel()
	for structure in submitted:
		structure.cancel()

	replacements = {}
	updated_drafts = []
	for structure in structures:
		if any(row.salary_component == component.name for row in structure.deductions):
			continue
		if structure.name not in submitted_names:
			structure.append("deductions", _penalty_row())
			structure.save()
			updated_drafts.append(structure.name)
			continue

		amendment = frappe.copy_doc(structure)
		amendment.amended_from = structure.name
		amendment.append("deductions", _penalty_row())
		amendment.insert(ignore_permissions=True)
		amendment.submit()
		replacements[structure.name] = amendment.name

	replaced_assignments = []
	for name in assignment_names:
		assignment = frappe.get_doc("Salary Structure Assignment", name)
		replacement = frappe.copy_doc(assignment)
		replacement.amended_from = assignment.name
		replacement.salary_structure = replacements[assignment.salary_structure]
		replacement.insert(ignore_permissions=True)
		replacement.submit()
		replaced_assignments.append({"from": assignment.name, "to": replacement.name})

	return {
		"salary_component": component.name,
		"updated_draft_structures": updated_drafts,
		"amended_structures": replacements,
		"replaced_assignments": replaced_assignments,
	}


def _get_or_create_hourly_penalty_component():
	name = frappe.db.get_value("Salary Component", HOURLY_PENALTY_COMPONENT, "name")
	if name:
		component = frappe.get_doc("Salary Component", name)
		if component.type != "Deduction":
			frappe.throw("نوع مؤلفه جریمه ساعتی باید Deduction باشد")
		if component.meta.has_field("salary_component_abbr") and component.salary_component_abbr != HOURLY_PENALTY_ABBR:
			frappe.throw("کد مؤلفه جریمه ساعتی باید HRDH باشد")
		if component.meta.has_field("disabled") and cint(component.disabled):
			component.disabled = 0
			component.save()
		return component

	component = frappe.new_doc("Salary Component")
	component.salary_component = HOURLY_PENALTY_COMPONENT
	component.salary_component_abbr = HOURLY_PENALTY_ABBR
	component.type = "Deduction"
	for fieldname, value in {
		"amount_based_on_formula": 0,
		"formula": "",
		"do_not_include_in_total": 1,
		"remove_if_zero_valued": 1,
		"is_tax_applicable": 0,
		"depends_on_payment_days": 0,
		"disabled": 0,
	}.items():
		if component.meta.has_field(fieldname):
			component.set(fieldname, value)
	component.insert(ignore_permissions=True)
	return component


def _penalty_row() -> dict:
	return {"salary_component": HOURLY_PENALTY_COMPONENT, "amount_based_on_formula": 0, "formula": ""}
