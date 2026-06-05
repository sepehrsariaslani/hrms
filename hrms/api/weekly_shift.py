import frappe


@frappe.whitelist()
def get_weekly_shift_context(
	target_date: str | None = None,
	week_start_date: str | None = None,
	employee: str | None = None,
) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import get_weekly_shift_context

	return get_weekly_shift_context(
		target_date=target_date,
		week_start_date=week_start_date,
		employee=employee,
	)


@frappe.whitelist()
def get_weekly_shift_slot_templates() -> list[dict]:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import get_weekly_shift_slot_templates

	return get_weekly_shift_slot_templates()


@frappe.whitelist()
def upsert_weekly_shift_plan(payload: str | dict | None = None) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import upsert_weekly_shift_plan

	return upsert_weekly_shift_plan(payload=payload)


@frappe.whitelist()
def submit_weekly_shift_plan(plan_name: str) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import submit_weekly_shift_plan

	return submit_weekly_shift_plan(plan_name=plan_name)


@frappe.whitelist()
def list_my_weekly_shift_plans(
	week_start_date: str | None = None,
	status: str | None = None,
) -> list[dict]:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import list_my_weekly_shift_plans

	return list_my_weekly_shift_plans(week_start_date=week_start_date, status=status)


@frappe.whitelist()
def list_team_weekly_shift_plans(
	week_start_date: str | None = None,
	status: str | None = None,
) -> list[dict]:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import list_team_weekly_shift_plans

	return list_team_weekly_shift_plans(week_start_date=week_start_date, status=status)


@frappe.whitelist()
def get_shift_allocator_team_overview(week_start_date: str | None = None) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import get_shift_allocator_team_overview

	return get_shift_allocator_team_overview(week_start_date=week_start_date)


@frappe.whitelist()
def approve_weekly_shift_plan(plan_name: str, note: str | None = None) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import approve_weekly_shift_plan

	return approve_weekly_shift_plan(plan_name=plan_name, note=note)


@frappe.whitelist()
def reject_weekly_shift_plan(plan_name: str, reason: str | None = None) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import reject_weekly_shift_plan

	return reject_weekly_shift_plan(plan_name=plan_name, reason=reason)


@frappe.whitelist()
def create_weekly_shift_plan_amendment(source_plan_name: str) -> dict:
	from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import (
		create_weekly_shift_plan_amendment,
	)

	return create_weekly_shift_plan_amendment(source_plan_name=source_plan_name)


@frappe.whitelist()
def get_weekly_shift_finalization_context(week_start_date: str | None = None) -> dict:
	from hrms.hr.doctype.weekly_shift_finalization.weekly_shift_finalization import (
		get_weekly_shift_finalization_context,
	)

	return get_weekly_shift_finalization_context(week_start_date=week_start_date)


@frappe.whitelist()
def upsert_weekly_shift_finalization(payload: str | dict | None = None) -> dict:
	from hrms.hr.doctype.weekly_shift_finalization.weekly_shift_finalization import (
		upsert_weekly_shift_finalization,
	)

	return upsert_weekly_shift_finalization(payload=payload)


@frappe.whitelist()
def finalize_weekly_shift_finalization(finalization_name: str) -> dict:
	from hrms.hr.doctype.weekly_shift_finalization.weekly_shift_finalization import (
		finalize_weekly_shift_finalization,
	)

	return finalize_weekly_shift_finalization(finalization_name=finalization_name)


@frappe.whitelist()
def create_weekly_shift_finalization_amendment(source_finalization_name: str) -> dict:
	from hrms.hr.doctype.weekly_shift_finalization.weekly_shift_finalization import (
		create_weekly_shift_finalization_amendment,
	)

	return create_weekly_shift_finalization_amendment(source_finalization_name=source_finalization_name)


@frappe.whitelist()
def get_employee_finalized_shift_slots(
	employee: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
) -> list[dict]:
	from hrms.hr.doctype.weekly_shift_finalization.weekly_shift_finalization import (
		get_employee_finalized_shift_slots,
	)

	return get_employee_finalized_shift_slots(employee=employee, from_date=from_date, to_date=to_date)
