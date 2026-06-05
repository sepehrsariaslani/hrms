import frappe


@frappe.whitelist()
def get_meal_plan_context(week_start_date: str | None = None, company: str | None = None) -> dict:
	from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import get_meal_plan_context

	return get_meal_plan_context(week_start_date=week_start_date, company=company)


@frappe.whitelist()
def upsert_meal_weekly_plan(payload: str | dict | None = None) -> dict:
	from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import upsert_meal_weekly_plan

	return upsert_meal_weekly_plan(payload=payload)


@frappe.whitelist()
def publish_meal_weekly_plan(plan_name: str) -> dict:
	from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import publish_meal_weekly_plan

	return publish_meal_weekly_plan(plan_name=plan_name)


@frappe.whitelist()
def save_my_meal_reservations(plan_name: str, reservations: str | dict | list | None = None) -> dict:
	from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import save_my_meal_reservations

	return save_my_meal_reservations(plan_name=plan_name, reservations=reservations)


@frappe.whitelist()
def update_meal_cutoff_settings(
	cutoff_time: str,
	plan_name: str | None = None,
	company: str | None = None,
	apply_to_company_default: int = 1,
) -> dict:
	from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import update_meal_cutoff_settings

	return update_meal_cutoff_settings(
		cutoff_time=cutoff_time,
		plan_name=plan_name,
		company=company,
		apply_to_company_default=apply_to_company_default,
	)


@frappe.whitelist()
def get_meal_demand_summary(plan_name: str) -> dict:
	from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import get_meal_demand_summary

	return get_meal_demand_summary(plan_name=plan_name)


@frappe.whitelist()
def list_company_meal_reservations(
	plan_name: str,
	meal_date: str | None = None,
	reservation_status: str | None = None,
	limit: int | None = 500,
) -> list[dict]:
	from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import list_company_meal_reservations

	return list_company_meal_reservations(
		plan_name=plan_name,
		meal_date=meal_date,
		reservation_status=reservation_status,
		limit=limit,
	)


@frappe.whitelist()
def mark_meal_delivery(plan_name: str, meal_date: str, employee: str, delivered: int = 1) -> dict:
	from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import mark_meal_delivery

	return mark_meal_delivery(
		plan_name=plan_name,
		meal_date=meal_date,
		employee=employee,
		delivered=delivered,
	)


@frappe.whitelist()
def get_meal_catalog(company: str | None = None) -> list[dict]:
	from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import get_meal_catalog

	return get_meal_catalog(company=company)


@frappe.whitelist()
def upsert_meal_catalog_item(item_code: str, company: str | None = None, is_active: int = 1) -> dict:
	from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import upsert_meal_catalog_item

	return upsert_meal_catalog_item(item_code=item_code, company=company, is_active=is_active)


@frappe.whitelist()
def get_employee_meal_item_options(
	company: str | None = None,
	search_text: str | None = None,
	limit: int = 50,
) -> list[dict]:
	from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import get_employee_meal_item_options

	return get_employee_meal_item_options(company=company, search_text=search_text, limit=limit)


@frappe.whitelist()
def copy_meal_plan_from_previous_week(
	source_plan_name: str,
	target_week_start_date: str,
	company: str | None = None,
) -> dict:
	from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import copy_meal_plan_from_previous_week

	return copy_meal_plan_from_previous_week(
		source_plan_name=source_plan_name,
		target_week_start_date=target_week_start_date,
		company=company,
	)
