# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	add_days,
	cint,
	date_diff,
	get_date_str,
	get_datetime,
	get_time,
	getdate,
	now_datetime,
	nowdate,
)

from hrms.hr.doctype.weekly_shift_plan.weekly_shift_plan import (
	get_week_start_date,
	normalize_calendar_date,
	parse_payload,
)

DEFAULT_CUTOFF_TIME = "10:00:00"
RESERVATION_STATUSES = {"Not Required", "Reserved", "Delivered"}
HR_ROLES = {"System Manager", "HR Manager", "HR User"}
MEAL_MANAGER_ROLES = {"Meal Coordinator", "Chef"}
PERSIAN_WEEKDAY_LABELS = {
	0: "دوشنبه",
	1: "سه\u200cشنبه",
	2: "چهارشنبه",
	3: "پنجشنبه",
	4: "جمعه",
	5: "شنبه",
	6: "یکشنبه",
}


class MealWeeklyPlan(Document):
	def before_validate(self):
		self._normalize_week()
		self._set_defaults()
		self._prepare_items()
		if not self.status:
			self.status = "Draft"

	def validate(self):
		self._validate_permissions()
		self._validate_items()

	def _normalize_week(self):
		self.week_start_date = get_week_start_date(self.week_start_date or nowdate())
		self.week_end_date = add_days(self.week_start_date, 6)

	def _set_defaults(self):
		if not self.company:
			employee = get_current_employee(frappe.session.user)
			self.company = employee.get("company") if employee else None

		if self.company and not self.meal_coordinator:
			self.meal_coordinator = get_company_meal_coordinator(self.company) or frappe.session.user

		if not self.cutoff_time:
			self.cutoff_time = get_company_default_cutoff_time(self.company)
		else:
			self.cutoff_time = normalize_time_value(self.cutoff_time)

	def _prepare_items(self):
		for item in self.meal_items or []:
			item.meal_date = normalize_calendar_date(item.meal_date) or item.meal_date
			item.meal_type = item.meal_type or "Lunch"
			if item.meal_date:
				item.meal_day_label = get_weekday_label(item.meal_date)
			if item.meal_item:
				item.menu_title = frappe.db.get_value("Item", item.meal_item, "item_name") or item.meal_item

	def _validate_permissions(self):
		if not can_manage_meals(frappe.session.user, self.company):
			frappe.throw(_("You are not allowed to manage meal plans."), frappe.PermissionError)

	def _validate_items(self):
		start = getdate(self.week_start_date)
		end = getdate(self.week_end_date)
		seen_dates = set()
		available_count = 0

		for row in self.meal_items or []:
			if not row.meal_date:
				frappe.throw(_("Row #{0}: Meal Date is required.").format(row.idx))

			date_key = normalize_calendar_date(row.meal_date)
			if not date_key:
				frappe.throw(_("Row #{0}: Meal Date is invalid.").format(row.idx))

			row_date = getdate(date_key)
			if row_date < start or row_date > end:
				frappe.throw(_("Row #{0}: Meal Date must be inside this week.").format(row.idx))

			if date_key in seen_dates:
				frappe.throw(_("Row #{0}: Duplicate meal date is not allowed.").format(row.idx))
			seen_dates.add(date_key)

			if row.meal_type and row.meal_type != "Lunch":
				frappe.throw(_("Row #{0}: Only Lunch meal type is supported.").format(row.idx))

			if cint(row.is_available):
				available_count += 1
				if not row.meal_item and not (row.menu_title or "").strip():
					frappe.throw(_("Row #{0}: Food Item is required for available rows.").format(row.idx))
				if row.meal_item and not is_employee_meal_item(row.meal_item):
					frappe.throw(_("Row #{0}: Selected item is not marked as employee meal item.").format(row.idx))

		if self.status == "Published" and available_count == 0:
			frappe.throw(_("Please add at least one available meal item before publishing."))


@frappe.whitelist()
def get_meal_plan_context(week_start_date: str | None = None, company: str | None = None) -> dict:
	user = frappe.session.user
	employee = get_current_employee(user)
	if not employee:
		frappe.throw(_("You are not linked to an active employee."))

	target_company = company or employee.get("company")
	if not target_company:
		frappe.throw(_("Company is required for meal plan context."))

	if not can_access_company(user, target_company, employee):
		frappe.throw(_("You are not allowed to access meal plans for this company."), frappe.PermissionError)

	week_start = get_week_start_date(week_start_date or nowdate())
	week_end = add_days(week_start, 6)
	plan_doc = get_latest_meal_plan(target_company, week_start)

	if plan_doc and plan_doc.status == "Published":
		ensure_reservation_rows_for_plan(plan_doc, [employee.get("name")])

	return {
		"company": target_company,
		"week_start_date": week_start,
		"week_end_date": week_end,
		"default_cutoff_time": get_company_default_cutoff_time(target_company),
		"is_company_meal_enabled": is_company_meal_enabled(target_company),
		"is_meal_coordinator": can_manage_meals(user, target_company),
		"employee": employee,
		"plan": serialize_plan(plan_doc) if plan_doc else None,
		"reservations": (
			build_employee_reservation_rows(plan_doc, employee.get("name"))
			if plan_doc and plan_doc.status == "Published"
			else []
		),
		"meal_catalog": get_meal_catalog(target_company),
		"previous_week_plans": list_previous_published_plans(target_company, week_start),
		"can_edit_reservations": bool(
			plan_doc and plan_doc.status == "Published" and is_company_meal_enabled(target_company)
		),
	}


@frappe.whitelist()
def upsert_meal_weekly_plan(payload: str | dict | None = None) -> dict:
	data = parse_payload(payload)
	user = frappe.session.user
	employee = get_current_employee(user)
	if not employee:
		frappe.throw(_("You are not linked to an active employee."))

	plan_name = data.get("name")
	week_start = get_week_start_date(data.get("week_start_date") or nowdate())

	if plan_name:
		doc = frappe.get_doc("Meal Weekly Plan", plan_name)
		company = doc.company
	else:
		company = data.get("company") or employee.get("company")
		doc = frappe.new_doc("Meal Weekly Plan")
		doc.company = company

	if not can_manage_meals(user, company):
		frappe.throw(_("You are not allowed to edit meal plans."), frappe.PermissionError)

	if doc.status == "Closed":
		frappe.throw(_("Closed plans cannot be edited."))

	doc.company = company
	doc.week_start_date = week_start
	doc.week_end_date = add_days(week_start, 6)
	doc.cutoff_time = normalize_time_value(data.get("cutoff_time")) or get_company_default_cutoff_time(company)
	doc.notes = data.get("notes") or ""
	doc.meal_coordinator = get_company_meal_coordinator(company) or user
	if doc.status != "Published":
		doc.status = "Draft"

	incoming_items = data.get("meal_items") or []
	doc.meal_items = []
	for row in incoming_items:
		meal_date = normalize_calendar_date(row.get("meal_date"))
		if not meal_date:
			continue

		meal_item = row.get("meal_item")
		menu_title = frappe.db.get_value("Item", meal_item, "item_name") if meal_item else (row.get("menu_title") or "")
		doc.append(
			"meal_items",
			{
				"meal_date": meal_date,
				"meal_day_label": get_weekday_label(meal_date),
				"meal_type": row.get("meal_type") or "Lunch",
				"meal_item": meal_item,
				"menu_title": (menu_title or "").strip(),
				"menu_description": row.get("menu_description"),
				"is_available": cint(row.get("is_available", 1)),
				"max_portions": row.get("max_portions"),
			},
		)

	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)

	if doc.status == "Published":
		ensure_reservation_rows_for_plan(doc)

	return serialize_plan(doc)


@frappe.whitelist()
def publish_meal_weekly_plan(plan_name: str) -> dict:
	doc = frappe.get_doc("Meal Weekly Plan", plan_name)
	if not can_manage_meals(frappe.session.user, doc.company):
		frappe.throw(_("You are not allowed to publish this meal plan."), frappe.PermissionError)

	if doc.status == "Closed":
		frappe.throw(_("Closed plans cannot be published."))

	doc.status = "Published"
	doc.published_on = now_datetime()
	doc.published_by = frappe.session.user
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)

	ensure_reservation_rows_for_plan(doc)
	return serialize_plan(doc)


@frappe.whitelist()
def save_my_meal_reservations(plan_name: str, reservations: str | dict | list | None = None) -> dict:
	plan = frappe.get_doc("Meal Weekly Plan", plan_name)
	employee = get_current_employee(frappe.session.user)
	if not employee:
		frappe.throw(_("You are not linked to an active employee."))
	if plan.company != employee.get("company"):
		frappe.throw(_("You cannot reserve meals for another company."), frappe.PermissionError)
	if plan.status != "Published":
		frappe.throw(_("Meal reservations are available only for published plans."))
	if not is_company_meal_enabled(plan.company):
		frappe.throw(_("Meal module is disabled for this company."))

	payload = parse_payload(reservations)
	if isinstance(payload, list):
		rows = payload
	elif isinstance(payload, dict):
		rows = payload.get("reservations") or []
	else:
		rows = []

	ensure_reservation_rows_for_plan(plan, [employee.get("name")])
	input_by_date = {}
	for row in rows:
		meal_date = normalize_calendar_date(row.get("meal_date"))
		if meal_date:
			input_by_date[meal_date] = row

	result = []
	available_items = get_available_items(plan)
	for item in available_items:
		meal_date = normalize_calendar_date(item.meal_date)
		if not meal_date:
			continue

		incoming = input_by_date.get(meal_date, {})
		reservation_name = frappe.db.get_value(
			"Meal Reservation",
			{
				"meal_plan": plan.name,
				"employee": employee.get("name"),
				"reservation_date": meal_date,
			},
			"name",
		)
		if reservation_name:
			reservation_doc = frappe.get_doc("Meal Reservation", reservation_name)
		else:
			reservation_doc = frappe.new_doc("Meal Reservation")
			reservation_doc.meal_plan = plan.name
			reservation_doc.company = plan.company
			reservation_doc.employee = employee.get("name")
			reservation_doc.employee_name = employee.get("employee_name")
			reservation_doc.reservation_date = meal_date

		target_status = normalize_reservation_status(incoming)
		if target_status == "Delivered":
			target_status = "Reserved"

		if reservation_doc.reservation_status == "Delivered" and target_status != "Delivered":
			frappe.throw(
				_("Meal on {0} has already been delivered and can no longer be changed.").format(meal_date)
			)

		if has_passed_cutoff(plan, meal_date) and target_status != reservation_doc.reservation_status:
			frappe.throw(
				_("Cutoff time has passed for {0}. Reservation can no longer be changed.").format(meal_date)
			)

		reservation_doc.meal_type = item.meal_type or "Lunch"
		reservation_doc.meal_item = item.meal_item
		reservation_doc.meal_title = item.menu_title
		reservation_doc.reservation_status = target_status
		reservation_doc.reservation_note = (incoming.get("reservation_note") or "").strip()
		reservation_doc.flags.ignore_permissions = True
		reservation_doc.save(ignore_permissions=True)
		result.append(serialize_reservation(reservation_doc))

	return {"plan_name": plan.name, "reservations": result}


@frappe.whitelist()
def update_meal_cutoff_settings(
	cutoff_time: str,
	plan_name: str | None = None,
	company: str | None = None,
	apply_to_company_default: int = 1,
) -> dict:
	if not cutoff_time:
		frappe.throw(_("Cutoff time is required."))

	user = frappe.session.user
	employee = get_current_employee(user)
	target_company = company or (employee or {}).get("company")
	plan_doc = None
	if plan_name:
		plan_doc = frappe.get_doc("Meal Weekly Plan", plan_name)
		target_company = plan_doc.company

	if not target_company:
		frappe.throw(_("Company is required for updating meal cutoff settings."))

	if not can_manage_meals(user, target_company):
		frappe.throw(_("You are not allowed to update meal cutoff settings."), frappe.PermissionError)

	normalized_cutoff = normalize_time_value(cutoff_time)
	if plan_doc:
		if plan_doc.status == "Closed":
			frappe.throw(_("Closed plans cannot be edited."))
		plan_doc.cutoff_time = normalized_cutoff
		plan_doc.flags.ignore_permissions = True
		plan_doc.save(ignore_permissions=True)

	if cint(apply_to_company_default) and frappe.db.has_column("Company", "meal_default_cutoff_time"):
		frappe.db.set_value(
			"Company",
			target_company,
			"meal_default_cutoff_time",
			normalized_cutoff,
			update_modified=True,
		)

	return {
		"company": target_company,
		"cutoff_time": normalized_cutoff,
		"default_cutoff_time": get_company_default_cutoff_time(target_company),
		"plan": serialize_plan(plan_doc) if plan_doc else None,
	}


@frappe.whitelist()
def get_meal_demand_summary(plan_name: str) -> dict:
	plan = frappe.get_doc("Meal Weekly Plan", plan_name)
	if not can_manage_meals(frappe.session.user, plan.company):
		frappe.throw(_("You are not allowed to view this meal summary."), frappe.PermissionError)

	ensure_reservation_rows_for_plan(plan)
	available_items = get_available_items(plan)
	summary_map = {
		get_date_str(getdate(item.meal_date)): {
			"meal_date": get_date_str(getdate(item.meal_date)),
			"meal_day_label": item.meal_day_label,
			"meal_item": item.meal_item,
			"meal_title": item.menu_title,
			"meal_type": item.meal_type or "Lunch",
			"reserved_count": 0,
			"delivered_count": 0,
			"not_required_count": 0,
			"total_requests": 0,
		}
		for item in available_items
	}

	rows = frappe.get_all(
		"Meal Reservation",
		filters={"meal_plan": plan.name},
		fields=["reservation_date", "reservation_status"],
		limit=0,
	)
	for row in rows:
		date_key = get_date_str(getdate(row.get("reservation_date")))
		if date_key not in summary_map:
			continue

		if row.get("reservation_status") == "Delivered":
			summary_map[date_key]["delivered_count"] += 1
		elif row.get("reservation_status") == "Reserved":
			summary_map[date_key]["reserved_count"] += 1
		else:
			summary_map[date_key]["not_required_count"] += 1

	for date_key, item in summary_map.items():
		item["total_requests"] = item["reserved_count"] + item["delivered_count"]
		item["remaining_to_deliver"] = item["reserved_count"]

	return {
		"plan": serialize_plan(plan),
		"total_active_employees": frappe.db.count("Employee", {"company": plan.company, "status": "Active"}),
		"summary": [summary_map[date_key] for date_key in sorted(summary_map.keys())],
	}


@frappe.whitelist()
def list_company_meal_reservations(
	plan_name: str,
	meal_date: str | None = None,
	reservation_status: str | None = None,
	limit: int | None = 500,
) -> list[dict]:
	plan = frappe.get_doc("Meal Weekly Plan", plan_name)
	if not can_manage_meals(frappe.session.user, plan.company):
		frappe.throw(_("You are not allowed to access meal reservations."), frappe.PermissionError)

	ensure_reservation_rows_for_plan(plan)
	filters = {"meal_plan": plan.name}
	if meal_date:
		filters["reservation_date"] = normalize_calendar_date(meal_date)
	if reservation_status:
		filters["reservation_status"] = reservation_status

	return frappe.get_all(
		"Meal Reservation",
		filters=filters,
		fields=[
			"name",
			"employee",
			"employee_name",
			"reservation_date",
			"meal_type",
			"meal_item",
			"meal_title",
			"reservation_status",
			"reservation_note",
			"delivered_on",
			"delivered_by",
			"modified",
		],
		order_by="reservation_date asc, employee_name asc",
		limit=max(cint(limit or 500), 1),
	)


@frappe.whitelist()
def mark_meal_delivery(plan_name: str, meal_date: str, employee: str, delivered: int = 1) -> dict:
	plan = frappe.get_doc("Meal Weekly Plan", plan_name)
	if not can_manage_meals(frappe.session.user, plan.company):
		frappe.throw(_("You are not allowed to mark meal delivery."), frappe.PermissionError)

	date_key = normalize_calendar_date(meal_date)
	if not date_key:
		frappe.throw(_("Meal date is invalid."))

	ensure_reservation_rows_for_plan(plan, [employee])
	reservation_name = frappe.db.get_value(
		"Meal Reservation",
		{
			"meal_plan": plan.name,
			"employee": employee,
			"reservation_date": date_key,
		},
		"name",
	)
	if not reservation_name:
		frappe.throw(_("Reservation was not found for selected employee and date."))

	doc = frappe.get_doc("Meal Reservation", reservation_name)
	target_delivered = cint(delivered)
	if target_delivered:
		if doc.reservation_status == "Not Required":
			frappe.throw(_("Cannot mark delivery for Not Required reservation."))
		doc.reservation_status = "Delivered"
		doc.delivered_on = now_datetime()
		doc.delivered_by = frappe.session.user
	else:
		if doc.reservation_status == "Delivered":
			doc.reservation_status = "Reserved"
		doc.delivered_on = None
		doc.delivered_by = None

	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	return serialize_reservation(doc)


@frappe.whitelist()
def get_meal_catalog(company: str | None = None) -> list[dict]:
	employee = get_current_employee(frappe.session.user)
	target_company = company or (employee or {}).get("company")
	if not target_company:
		return []

	if not can_access_company(frappe.session.user, target_company, employee):
		frappe.throw(_("You are not allowed to access this company meal catalog."), frappe.PermissionError)

	rows = frappe.get_all(
		"Employee Meal Catalog",
		filters={"company": target_company, "is_active": 1},
		fields=["name", "item", "item_name", "description"],
		order_by="item_name asc",
		limit=0,
	)
	return rows


@frappe.whitelist()
def upsert_meal_catalog_item(item_code: str, company: str | None = None, is_active: int = 1) -> dict:
	employee = get_current_employee(frappe.session.user)
	target_company = company or (employee or {}).get("company")
	if not target_company:
		frappe.throw(_("Company is required."))
	if not can_manage_meals(frappe.session.user, target_company):
		frappe.throw(_("You are not allowed to edit meal catalog."), frappe.PermissionError)

	if not is_employee_meal_item(item_code):
		frappe.throw(_("Selected item is not marked as employee meal item."))

	existing = frappe.db.get_value(
		"Employee Meal Catalog",
		{"company": target_company, "item": item_code},
		"name",
	)
	if existing:
		doc = frappe.get_doc("Employee Meal Catalog", existing)
		doc.is_active = cint(is_active)
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.new_doc("Employee Meal Catalog")
		doc.company = target_company
		doc.item = item_code
		doc.is_active = cint(is_active)
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)

	return {
		"name": doc.name,
		"company": doc.company,
		"item": doc.item,
		"item_name": doc.item_name,
		"is_active": cint(doc.is_active),
	}


@frappe.whitelist()
def get_employee_meal_item_options(company: str | None = None, search_text: str | None = None, limit: int = 50) -> list[dict]:
	employee = get_current_employee(frappe.session.user)
	target_company = company or (employee or {}).get("company")
	if target_company and not can_access_company(frappe.session.user, target_company, employee):
		frappe.throw(_("You are not allowed to access meal items for this company."), frappe.PermissionError)

	filters = {"disabled": 0}
	if frappe.db.has_column("Item", "is_employee_meal_item"):
		filters["is_employee_meal_item"] = 1

	if search_text:
		filters["item_name"] = ["like", f"%{search_text.strip()}%"]

	items = frappe.get_all(
		"Item",
		filters=filters,
		fields=["name", "item_name", "description"],
		order_by="item_name asc",
		limit=max(cint(limit or 50), 1),
	)
	return items


@frappe.whitelist()
def copy_meal_plan_from_previous_week(
	source_plan_name: str,
	target_week_start_date: str,
	company: str | None = None,
) -> dict:
	source = frappe.get_doc("Meal Weekly Plan", source_plan_name)
	target_week_start = get_week_start_date(target_week_start_date)
	target_company = company or source.company

	if source.company != target_company:
		frappe.throw(_("Source plan company does not match selected company."))
	if not can_manage_meals(frappe.session.user, target_company):
		frappe.throw(_("You are not allowed to copy meal plans."), frappe.PermissionError)

	meal_items = []
	source_start = get_date_str(getdate(source.week_start_date))
	for row in sorted(source.meal_items or [], key=lambda item: item.meal_date or ""):
		offset = date_diff(get_date_str(getdate(row.meal_date)), source_start) if row.meal_date else 0
		target_date = get_date_str(add_days(target_week_start, offset))
		meal_items.append(
			{
				"meal_date": target_date,
				"meal_type": row.meal_type or "Lunch",
				"meal_item": row.meal_item,
				"menu_title": row.menu_title,
				"menu_description": row.menu_description,
				"is_available": cint(row.is_available),
				"max_portions": row.max_portions,
			}
		)

	return {
		"source_plan": source.name,
		"target_week_start_date": target_week_start,
		"meal_items": meal_items,
	}


# Helpers
def serialize_plan(doc: Document | None) -> dict | None:
	if not doc:
		return None

	return {
		"name": doc.name,
		"company": doc.company,
		"meal_coordinator": doc.meal_coordinator,
		"week_start_date": get_date_str(getdate(doc.week_start_date)),
		"week_end_date": get_date_str(getdate(doc.week_end_date)),
		"status": doc.status,
		"cutoff_time": normalize_time_value(doc.cutoff_time),
		"published_on": doc.published_on,
		"published_by": doc.published_by,
		"notes": doc.notes,
		"meal_items": [
			{
				"name": row.name,
				"meal_date": get_date_str(getdate(row.meal_date)) if row.meal_date else None,
				"meal_day_label": row.meal_day_label,
				"meal_type": row.meal_type or "Lunch",
				"meal_item": row.meal_item,
				"menu_title": row.menu_title,
				"menu_description": row.menu_description,
				"is_available": cint(row.is_available),
				"max_portions": row.max_portions,
			}
			for row in sorted(doc.meal_items or [], key=lambda item: item.meal_date or "")
		],
	}


def serialize_reservation(doc: Document) -> dict:
	return {
		"name": doc.name,
		"meal_plan": doc.meal_plan,
		"company": doc.company,
		"employee": doc.employee,
		"employee_name": doc.employee_name,
		"reservation_date": get_date_str(getdate(doc.reservation_date)) if doc.reservation_date else None,
		"meal_type": doc.meal_type,
		"meal_item": doc.meal_item,
		"meal_title": doc.meal_title,
		"reservation_status": doc.reservation_status,
		"reservation_note": doc.reservation_note,
		"delivered_on": doc.delivered_on,
		"delivered_by": doc.delivered_by,
	}


def build_employee_reservation_rows(plan: Document, employee: str) -> list[dict]:
	available_items = get_available_items(plan)
	if not available_items:
		return []

	reservations = frappe.get_all(
		"Meal Reservation",
		filters={"meal_plan": plan.name, "employee": employee},
		fields=["name", "reservation_date", "reservation_status", "reservation_note", "delivered_on"],
		limit=0,
	)
	reservation_map = {
		get_date_str(getdate(row.reservation_date)): row
		for row in reservations
		if row.get("reservation_date")
	}
	result = []
	for item in available_items:
		date_key = get_date_str(getdate(item.meal_date))
		reservation = reservation_map.get(date_key) or {}
		status = reservation.get("reservation_status") or "Not Required"
		result.append(
			{
				"meal_date": date_key,
				"meal_day_label": item.meal_day_label,
				"meal_type": item.meal_type or "Lunch",
				"meal_item": item.meal_item,
				"menu_title": item.menu_title,
				"menu_description": item.menu_description,
				"reservation_name": reservation.get("name"),
				"reservation_status": status,
				"reservation_note": reservation.get("reservation_note") or "",
				"is_locked": status == "Delivered",
				"after_cutoff": has_passed_cutoff(plan, date_key),
			}
		)
	return result


def get_available_items(plan: Document) -> list:
	return sorted(
		[
			item
			for item in (plan.meal_items or [])
			if item.meal_date and cint(item.is_available) and (item.meal_item or (item.menu_title or "").strip())
		],
		key=lambda item: item.meal_date,
	)


def ensure_reservation_rows_for_plan(plan: Document, employees: list[str] | None = None) -> None:
	if plan.status != "Published":
		return

	available_items = get_available_items(plan)
	if not available_items:
		return

	employee_names = list(employees or [])
	if not employee_names:
		employee_names = frappe.get_all(
			"Employee",
			filters={"company": plan.company, "status": "Active"},
			pluck="name",
		)
	if not employee_names:
		return

	date_keys = [get_date_str(getdate(item.meal_date)) for item in available_items]
	existing_rows = frappe.get_all(
		"Meal Reservation",
		filters={
			"meal_plan": plan.name,
			"employee": ["in", employee_names],
			"reservation_date": ["in", date_keys],
		},
		fields=["employee", "reservation_date"],
		limit=0,
	)
	existing_keys = {
		(row.get("employee"), get_date_str(getdate(row.get("reservation_date"))))
		for row in existing_rows
		if row.get("employee") and row.get("reservation_date")
	}

	for employee in employee_names:
		employee_name = frappe.db.get_value("Employee", employee, "employee_name")
		for item in available_items:
			date_key = get_date_str(getdate(item.meal_date))
			key = (employee, date_key)
			if key in existing_keys:
				continue

			doc = frappe.new_doc("Meal Reservation")
			doc.meal_plan = plan.name
			doc.company = plan.company
			doc.employee = employee
			doc.employee_name = employee_name
			doc.reservation_date = date_key
			doc.meal_type = item.meal_type or "Lunch"
			doc.meal_item = item.meal_item
			doc.meal_title = item.menu_title
			doc.reservation_status = "Not Required"
			doc.flags.ignore_permissions = True
			doc.insert(ignore_permissions=True)


def get_latest_meal_plan(company: str, week_start: str) -> Document | None:
	published_name = frappe.db.get_value(
		"Meal Weekly Plan",
		{
			"company": company,
			"week_start_date": week_start,
			"status": "Published",
			"docstatus": ("!=", 2),
		},
		"name",
		order_by="modified desc",
	)
	if published_name:
		return frappe.get_doc("Meal Weekly Plan", published_name)

	latest_name = frappe.db.get_value(
		"Meal Weekly Plan",
		{
			"company": company,
			"week_start_date": week_start,
			"docstatus": ("!=", 2),
		},
		"name",
		order_by="modified desc",
	)
	if latest_name:
		return frappe.get_doc("Meal Weekly Plan", latest_name)

	# Fallback rule requested by business: if this week has no plan, copy from latest
	# published historical plan and keep meal program running.
	copied = auto_copy_previous_published_plan(company, week_start)
	if copied:
		return copied

	return None


def auto_copy_previous_published_plan(company: str, target_week_start: str) -> Document | None:
	source_name = frappe.db.get_value(
		"Meal Weekly Plan",
		{
			"company": company,
			"status": "Published",
			"week_start_date": ["<", target_week_start],
			"docstatus": ("!=", 2),
		},
		"name",
		order_by="week_start_date desc, modified desc",
	)
	if not source_name:
		return None

	# Idempotency guard in concurrent requests.
	existing_name = frappe.db.get_value(
		"Meal Weekly Plan",
		{"company": company, "week_start_date": target_week_start, "docstatus": ("!=", 2)},
		"name",
	)
	if existing_name:
		return frappe.get_doc("Meal Weekly Plan", existing_name)

	source = frappe.get_doc("Meal Weekly Plan", source_name)
	if not source.meal_items:
		return None

	target = frappe.new_doc("Meal Weekly Plan")
	target.company = company
	target.meal_coordinator = get_company_meal_coordinator(company) or source.meal_coordinator or frappe.session.user
	target.week_start_date = target_week_start
	target.week_end_date = add_days(target_week_start, 6)
	target.cutoff_time = normalize_time_value(source.cutoff_time)
	target.status = "Published"
	target.published_on = now_datetime()
	target.published_by = source.published_by or frappe.session.user
	target.notes = (source.notes or "")

	source_start = get_date_str(getdate(source.week_start_date))
	for row in sorted(source.meal_items or [], key=lambda item: item.meal_date or ""):
		offset = date_diff(get_date_str(getdate(row.meal_date)), source_start) if row.meal_date else 0
		target_date = get_date_str(add_days(target_week_start, offset))
		target.append(
			"meal_items",
			{
				"meal_date": target_date,
				"meal_day_label": get_weekday_label(target_date),
				"meal_type": row.meal_type or "Lunch",
				"meal_item": row.meal_item,
				"menu_title": row.menu_title,
				"menu_description": row.menu_description,
				"is_available": cint(row.is_available),
				"max_portions": row.max_portions,
			},
		)

	target.flags.ignore_permissions = True
	target.insert(ignore_permissions=True)
	ensure_reservation_rows_for_plan(target)
	return target


def list_previous_published_plans(company: str, before_week_start: str, limit: int = 8) -> list[dict]:
	return frappe.get_all(
		"Meal Weekly Plan",
		filters={
			"company": company,
			"status": "Published",
			"week_start_date": ["<", before_week_start],
			"docstatus": ("!=", 2),
		},
		fields=["name", "week_start_date", "week_end_date", "published_on"],
		order_by="week_start_date desc",
		limit=max(cint(limit or 8), 1),
	)


def normalize_reservation_status(row: dict | None) -> str:
	data = row or {}
	status = data.get("reservation_status")
	if status in RESERVATION_STATUSES:
		return status

	if "wants_meal" in data:
		return "Reserved" if cint(data.get("wants_meal")) else "Not Required"

	return "Not Required"


def has_passed_cutoff(plan: Document, meal_date: str) -> bool:
	try:
		cutoff_time = normalize_time_value(plan.cutoff_time)
		cutoff_datetime = get_datetime(f"{meal_date} {cutoff_time}")
		return now_datetime() > cutoff_datetime
	except Exception:
		return False


def can_access_company(user: str, company: str, employee: dict | None = None) -> bool:
	if can_manage_meals(user, company):
		return True
	return bool(employee and employee.get("company") == company)


def can_manage_meals(user: str, company: str | None) -> bool:
	if not company:
		return False

	roles = set(frappe.get_roles(user))
	if HR_ROLES.intersection(roles):
		return True

	company_coordinator = get_company_meal_coordinator(company)
	if company_coordinator and company_coordinator == user:
		return True

	if MEAL_MANAGER_ROLES.intersection(roles):
		employee = get_current_employee(user)
		return bool(employee and employee.get("company") == company)

	return False


def get_current_employee(user: str) -> dict | None:
	return frappe.db.get_value(
		"Employee",
		{"user_id": user, "status": "Active"},
		["name", "employee_name", "company", "user_id"],
		as_dict=True,
	)


def get_company_meal_coordinator(company: str | None) -> str | None:
	if not company or not frappe.db.has_column("Company", "meal_coordinator"):
		return None
	return frappe.db.get_value("Company", company, "meal_coordinator")


def get_company_default_cutoff_time(company: str | None) -> str:
	if company and frappe.db.has_column("Company", "meal_default_cutoff_time"):
		return normalize_time_value(frappe.db.get_value("Company", company, "meal_default_cutoff_time"))
	return DEFAULT_CUTOFF_TIME


def is_company_meal_enabled(company: str | None) -> bool:
	if not company:
		return False
	if not frappe.db.has_column("Company", "meal_enabled"):
		return True
	return cint(frappe.db.get_value("Company", company, "meal_enabled") or 0) == 1


def normalize_time_value(value, default: str = DEFAULT_CUTOFF_TIME) -> str:
	if not value:
		return default
	try:
		parsed = get_time(value)
		return parsed.strftime("%H:%M:%S")
	except Exception:
		return default


def is_employee_meal_item(item_code: str | None) -> bool:
	if not item_code or not frappe.db.exists("Item", item_code):
		return False
	if not frappe.db.has_column("Item", "is_employee_meal_item"):
		return True
	return cint(frappe.db.get_value("Item", item_code, "is_employee_meal_item") or 0) == 1


def get_weekday_label(date_value: str) -> str:
	date = getdate(date_value)
	return PERSIAN_WEEKDAY_LABELS.get(date.weekday(), "")
