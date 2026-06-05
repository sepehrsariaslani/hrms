import json
from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

NEWSLETTER_DOCTYPE = "HR Newsletter"
RECEIPT_DOCTYPE = "HR Newsletter Receipt"
POLL_DOCTYPE = "HR Newsletter Poll"
POLL_OPTION_DOCTYPE = "HR Newsletter Poll Option"
POLL_VOTE_DOCTYPE = "HR Newsletter Poll Vote"
NEWSLETTER_MANAGER_ROLES = {"HR Manager", "HR User", "System Manager"}


@frappe.whitelist()
def get_newsletter_dashboard_context() -> dict:
	is_manager = _is_newsletter_manager()
	current_employee = _get_current_employee()

	if not _has_doctype(NEWSLETTER_DOCTYPE):
		return {
			"employee_newsletters": [],
			"managed_newsletters": [],
			"stats": {
				"total_sent": 0,
				"published": 0,
				"scheduled": 0,
				"read_count": 0,
				"unread_count": 0,
			},
			"is_newsletter_manager": is_manager,
		}

	newsletters = frappe.get_all(
		NEWSLETTER_DOCTYPE,
		fields=["name", "title", "summary", "status", "modified", "creation"],
		filters={"docstatus": ["!=", 2]},
		order_by="modified desc",
		limit_page_length=50,
	)

	employee_rows = []
	managed_rows = []

	for row in newsletters:
		doc = frappe.get_doc(NEWSLETTER_DOCTYPE, row.name)
		serialized = _serialize_newsletter(doc, current_employee)

		if is_manager:
			managed_rows.append(serialized)

		if _can_employee_view_newsletter(doc, current_employee):
			employee_rows.append(serialized)

	if not is_manager:
		employee_rows = [
			row
			for row in employee_rows
			if row.get("status") in {"Published", "Scheduled"}
		]

	stats = _build_dashboard_stats(employee_rows if not is_manager else managed_rows)

	return {
		"employee_newsletters": employee_rows,
		"managed_newsletters": managed_rows,
		"stats": stats,
		"is_newsletter_manager": is_manager,
	}


@frappe.whitelist()
def get_newsletter_audience_options() -> dict:
	_assert_newsletter_manager()

	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "employee_name", "designation", "user_id"],
		order_by="employee_name asc",
		limit_page_length=0,
	)

	user_ids = [row.user_id for row in employees if row.user_id]
	roles_by_user = _get_roles_by_users(user_ids)

	role_set = set()
	rows = []
	for employee in employees:
		roles = sorted(set(roles_by_user.get(employee.user_id, [])))
		if employee.designation:
			roles.append(employee.designation)
		roles = sorted(set(filter(None, roles)))

		role_set.update(roles)
		rows.append(
			{
				"name": employee.name,
				"employee_name": employee.employee_name,
				"designation": employee.designation,
				"roles": roles,
			}
		)

	role_options = _build_role_options(role_set)

	return {
		"roles": sorted(role_set),
		"role_options": role_options,
		"employees": rows,
	}


@frappe.whitelist()
def get_newsletter_detail(newsletter_name: str, include_report: int = 0) -> dict:
	_ensure_newsletter_doctype()
	current_employee = _get_current_employee()
	doc = frappe.get_doc(NEWSLETTER_DOCTYPE, newsletter_name)

	if not (_is_newsletter_manager() or _can_employee_view_newsletter(doc, current_employee)):
		frappe.throw(_("You are not allowed to view this newsletter."))

	newsletter = _serialize_newsletter(doc, current_employee)
	if cint(include_report):
		report = _build_report_payload(doc)
		return {"newsletter": newsletter, **report}

	return {"newsletter": newsletter}


@frappe.whitelist()
def upsert_newsletter(payload: str | dict | None = None) -> dict:
	_assert_newsletter_manager()
	_ensure_newsletter_doctype()

	data = _parse_payload(payload)
	name = data.get("name")

	if name:
		doc = frappe.get_doc(NEWSLETTER_DOCTYPE, name)
	else:
		doc = frappe.new_doc(NEWSLETTER_DOCTYPE)

	_apply_newsletter_payload(doc, data)
	doc.save()
	if "polls" in data:
		_sync_newsletter_polls(doc, data.get("polls"))

	status = _safe_text(data.get("status") or _safe_text(doc.get("status")) or "Draft")
	if status in {"Published", "Scheduled"}:
		_sync_newsletter_receipts(doc)

	return _serialize_newsletter(doc, _get_current_employee())


@frappe.whitelist()
def mark_newsletter_read(newsletter_name: str) -> dict:
	_ensure_newsletter_doctype()
	current_employee = _get_current_employee(required=True)
	doc = frappe.get_doc(NEWSLETTER_DOCTYPE, newsletter_name)

	if not _can_employee_view_newsletter(doc, current_employee):
		frappe.throw(_("You are not allowed to access this newsletter."))

	if not _has_doctype(RECEIPT_DOCTYPE):
		return {"ok": True, "message": "Receipt doctype is not installed"}

	receipt_name = frappe.db.get_value(
		RECEIPT_DOCTYPE,
		{"newsletter": newsletter_name, "employee": current_employee.name},
		"name",
	)

	if receipt_name:
		receipt = frappe.get_doc(RECEIPT_DOCTYPE, receipt_name)
	else:
		receipt = frappe.new_doc(RECEIPT_DOCTYPE)
		_set_doc_field(receipt, current_employee.name, "employee")
		_set_doc_field(receipt, current_employee.employee_name, "employee_name")
		_set_doc_field(receipt, current_employee.designation, "designation")
		_set_doc_field(receipt, newsletter_name, "newsletter")

	_set_doc_field(receipt, 1, "is_read")
	_set_doc_field(receipt, now_datetime(), "read_on")
	receipt.save(ignore_permissions=True)

	_update_newsletter_read_stats(newsletter_name)

	return {
		"ok": True,
		"receipt": receipt.as_dict(),
	}


@frappe.whitelist()
def get_newsletter_report(newsletter_name: str) -> dict:
	_assert_newsletter_manager()
	_ensure_newsletter_doctype()
	doc = frappe.get_doc(NEWSLETTER_DOCTYPE, newsletter_name)
	report = _build_report_payload(doc)
	return {
		"newsletter": _serialize_newsletter(doc, _get_current_employee()),
		**report,
	}


@frappe.whitelist()
def submit_poll_vote(newsletter_name: str, poll_name: str, selected_options=None) -> dict:
	_ensure_newsletter_doctype()
	current_employee = _get_current_employee(required=True)
	newsletter_doc = frappe.get_doc(NEWSLETTER_DOCTYPE, newsletter_name)

	if not _can_employee_view_newsletter(newsletter_doc, current_employee):
		frappe.throw(_("You are not allowed to vote on this newsletter."))

	_ensure_poll_doctype()
	poll_doc = frappe.get_doc(POLL_DOCTYPE, poll_name)
	if _safe_text(poll_doc.get("newsletter")) != newsletter_name:
		frappe.throw(_("This poll does not belong to the selected newsletter."))

	option_rows = _get_poll_option_rows(poll_doc)
	option_texts = {row["option_text"] for row in option_rows}
	selected_texts = _parse_json_array(selected_options)
	selected_texts = [row for row in selected_texts if row in option_texts]
	selected_texts = list(dict.fromkeys(selected_texts))

	if not selected_texts:
		frappe.throw(_("Please select at least one option."))

	allow_multiple = bool(cint(poll_doc.get("allow_multiple")))
	if not allow_multiple and len(selected_texts) > 1:
		frappe.throw(_("This poll accepts only one option."))

	existing_votes = frappe.get_all(
		POLL_VOTE_DOCTYPE,
		filters={"poll": poll_doc.name, "employee": current_employee.name},
		fields=["name"],
		limit_page_length=0,
	)
	for row in existing_votes:
		frappe.delete_doc(POLL_VOTE_DOCTYPE, row.name, ignore_permissions=True, force=1)

	for option_text in selected_texts:
		vote = frappe.new_doc(POLL_VOTE_DOCTYPE)
		_set_doc_field(vote, newsletter_name, "newsletter")
		_set_doc_field(vote, poll_doc.name, "poll")
		_set_doc_field(vote, current_employee.name, "employee")
		_set_doc_field(vote, current_employee.employee_name, "employee_name")
		_set_doc_field(vote, frappe.session.user, "user_id")
		_set_doc_field(vote, option_text, "option", "option_text")
		vote.insert(ignore_permissions=True)

	return {
		"ok": True,
		"poll": _serialize_poll(
			poll_doc,
			current_employee=current_employee,
			is_manager=_is_newsletter_manager(),
		),
	}


def _build_report_payload(newsletter_doc) -> dict:
	targeted = _get_targeted_employees(newsletter_doc)
	targeted_by_employee = {row["employee"]: row for row in targeted}

	receipts_by_employee = {}
	if _has_doctype(RECEIPT_DOCTYPE):
		receipts = frappe.get_all(
			RECEIPT_DOCTYPE,
			filters={"newsletter": newsletter_doc.name},
			fields=["name", "employee", "employee_name", "designation", "is_read", "read_on"],
			limit_page_length=0,
		)
		for row in receipts:
			receipts_by_employee[row.employee] = row

	recipients = []
	for employee, employee_row in targeted_by_employee.items():
		receipt = receipts_by_employee.get(employee)
		recipients.append(
			{
				"employee": employee,
				"employee_name": employee_row.get("employee_name") or employee,
				"designation": employee_row.get("designation") or "",
				"is_read": bool(receipt and cint(receipt.get("is_read"))),
				"read_on": receipt.get("read_on") if receipt else None,
			}
		)

	total_recipients = len(recipients)
	read_count = sum(1 for row in recipients if row.get("is_read"))
	unread_count = max(total_recipients - read_count, 0)
	read_rate = round((read_count / total_recipients) * 100, 1) if total_recipients else 0

	role_stats = defaultdict(lambda: {"recipient_count": 0, "read_count": 0})
	for row in recipients:
		role = row.get("designation") or _("Unassigned")
		role_stats[role]["recipient_count"] += 1
		if row.get("is_read"):
			role_stats[role]["read_count"] += 1

	by_role = []
	for role, stats in role_stats.items():
		recipient_count = stats["recipient_count"]
		read_count_for_role = stats["read_count"]
		by_role.append(
			{
				"role": role,
				"recipient_count": recipient_count,
				"read_count": read_count_for_role,
				"read_rate": round((read_count_for_role / recipient_count) * 100, 1)
				if recipient_count
				else 0,
			}
		)

	by_role.sort(key=lambda row: row["role"])

	return {
		"stats": {
			"recipient_count": total_recipients,
			"total_recipients": total_recipients,
			"read_count": read_count,
			"total_reads": read_count,
			"unread_count": unread_count,
			"read_rate": read_rate,
		},
		"recipients": recipients,
		"by_role": by_role,
	}


def _build_dashboard_stats(newsletters: list[dict]) -> dict:
	published = sum(1 for row in newsletters if row.get("status") == "Published")
	scheduled = sum(1 for row in newsletters if row.get("status") == "Scheduled")
	total_sent = sum(cint(row.get("recipient_count") or 0) for row in newsletters)
	read_count = sum(cint(row.get("read_count") or 0) for row in newsletters)
	unread_count = sum(cint(row.get("unread_count") or 0) for row in newsletters)

	return {
		"total_sent": total_sent,
		"published": published,
		"scheduled": scheduled,
		"read_count": read_count,
		"unread_count": unread_count,
	}


def _serialize_newsletter(newsletter_doc, current_employee=None) -> dict:
	audience_mode = _safe_text(
		_get_doc_value(newsletter_doc, "audience_mode", default="All Employees")
	)
	target_roles = _parse_json_array(
		_get_doc_value(newsletter_doc, "target_roles_json", "target_roles", default=[])
	)
	target_employees = _parse_json_array(
		_get_doc_value(newsletter_doc, "target_employees_json", "target_employees", default=[])
	)
	excluded_employees = _parse_json_array(
		_get_doc_value(newsletter_doc, "excluded_employees_json", "excluded_employees", default=[])
	)
	status = _safe_text(_get_doc_value(newsletter_doc, "status", default="Draft"))

	attachments = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": NEWSLETTER_DOCTYPE,
			"attached_to_name": newsletter_doc.name,
		},
		fields=["file_name", "file_url", "attached_to_field", "is_private", "creation"],
		order_by="creation asc",
		limit_page_length=0,
	)

	cover_image = _safe_text(
		_get_doc_value(newsletter_doc, "cover_image", "image", default="")
	)
	if not cover_image:
		cover_file = next(
			(
				row
				for row in attachments
				if _safe_text(row.get("attached_to_field")) in {"cover_image", "image"}
			),
			None,
		)
		if cover_file:
			cover_image = _safe_text(cover_file.get("file_url"))

	stats = _get_newsletter_stats(newsletter_doc.name)
	is_read = _is_newsletter_read_by_employee(newsletter_doc.name, current_employee)

	return {
		"name": newsletter_doc.name,
		"title": _safe_text(_get_doc_value(newsletter_doc, "title", "subject", default="")),
		"summary": _safe_text(_get_doc_value(newsletter_doc, "summary", "description", default="")),
		"content": _safe_text(_get_doc_value(newsletter_doc, "content", default="")),
		"cover_image": cover_image,
		"cover_caption": _safe_text(_get_doc_value(newsletter_doc, "cover_caption", default="")),
		"status": status,
		"audience_mode": audience_mode,
		"target_roles": target_roles,
		"target_employees": target_employees,
		"excluded_employees": excluded_employees,
		"scheduled_publish_at": _get_doc_value(newsletter_doc, "scheduled_publish_at", "schedule_at", "publish_on"),
		"published_on": _get_doc_value(newsletter_doc, "published_on", "publish_date"),
		"published_by": _safe_text(_get_doc_value(newsletter_doc, "published_by")),
		"published_by_name": _safe_text(
			_get_doc_value(newsletter_doc, "published_by_name", default=_get_user_full_name(newsletter_doc.owner))
		),
		"expires_on": _get_doc_value(newsletter_doc, "expires_on", "expiry_date"),
		"send_push_notification": cint(_get_doc_value(newsletter_doc, "send_push_notification", default=0)),
		"is_read": is_read,
		"recipient_count": stats["recipient_count"],
		"read_count": stats["read_count"],
		"unread_count": stats["unread_count"],
		"read_rate": stats["read_rate"],
		"creation": newsletter_doc.creation,
		"modified": newsletter_doc.modified,
		"owner": newsletter_doc.owner,
		"modified_by": newsletter_doc.modified_by,
		"polls": _get_newsletter_polls(
			newsletter_doc.name,
			current_employee=current_employee,
			is_manager=_is_newsletter_manager(),
		),
		"attachments": [
			{
				"file_name": row.get("file_name"),
				"file_url": row.get("file_url"),
				"url": row.get("file_url"),
				"attached_to_field": row.get("attached_to_field"),
			}
			for row in attachments
			if row.get("file_url")
		],
	}


def _apply_newsletter_payload(newsletter_doc, payload: dict) -> None:
	title = _safe_text(payload.get("title"))
	if not title:
		frappe.throw(_("Title is required."))

	content = _safe_text(payload.get("content"))
	if not content:
		frappe.throw(_("Content is required."))

	status = _safe_text(payload.get("status") or "Draft")
	if status not in {"Draft", "Scheduled", "Published", "Cancelled"}:
		status = "Draft"

	target_roles = _parse_json_array(payload.get("target_roles"))
	target_employees = _parse_json_array(payload.get("target_employees"))
	excluded_employees = _parse_json_array(payload.get("excluded_employees"))
	audience_mode = _safe_text(payload.get("audience_mode") or "All Employees")
	if audience_mode != "By Role":
		excluded_employees = []

	_set_doc_field(newsletter_doc, title, "title", "subject")
	_set_doc_field(newsletter_doc, _safe_text(payload.get("summary")), "summary", "description")
	_set_doc_field(newsletter_doc, content, "content")
	_set_doc_field(newsletter_doc, _safe_text(payload.get("cover_image")), "cover_image", "image")
	_set_doc_field(newsletter_doc, _safe_text(payload.get("cover_caption")), "cover_caption")
	_set_doc_field(newsletter_doc, audience_mode, "audience_mode")
	_set_doc_field(newsletter_doc, json.dumps(target_roles, ensure_ascii=False), "target_roles_json")
	_set_doc_field(newsletter_doc, json.dumps(target_employees, ensure_ascii=False), "target_employees_json")
	_set_doc_field(newsletter_doc, json.dumps(excluded_employees, ensure_ascii=False), "excluded_employees_json")
	_set_doc_field(newsletter_doc, ", ".join(target_roles), "target_roles")
	_set_doc_field(newsletter_doc, ", ".join(target_employees), "target_employees")
	_set_doc_field(newsletter_doc, ", ".join(excluded_employees), "excluded_employees")
	_set_doc_field(newsletter_doc, cint(payload.get("send_push_notification") or 0), "send_push_notification")

	schedule_dt = payload.get("scheduled_publish_at")
	expiry_dt = payload.get("expires_on")
	if schedule_dt:
		_set_doc_field(newsletter_doc, schedule_dt, "scheduled_publish_at", "schedule_at", "publish_on")
	if expiry_dt:
		_set_doc_field(newsletter_doc, expiry_dt, "expires_on", "expiry_date")

	_set_doc_field(newsletter_doc, status, "status")
	if status == "Published":
		_set_doc_field(newsletter_doc, now_datetime(), "published_on", "publish_date")
		_set_doc_field(newsletter_doc, frappe.session.user, "published_by")
		_set_doc_field(newsletter_doc, _get_user_full_name(frappe.session.user), "published_by_name")


def _sync_newsletter_polls(newsletter_doc, polls_payload) -> None:
	if not _has_poll_doctypes():
		return

	rows = _parse_poll_payload_rows(polls_payload)
	existing_poll_names = set(
		frappe.get_all(POLL_DOCTYPE, filters={"newsletter": newsletter_doc.name}, pluck="name")
	)
	kept_poll_names = set()

	for row in rows:
		question = _safe_text(row.get("question"))
		if not question:
			continue

		option_rows = _parse_poll_option_texts(row.get("options"))
		if len(option_rows) < 2:
			continue

		poll_name = _safe_text(row.get("name"))
		if poll_name and frappe.db.exists(POLL_DOCTYPE, {"name": poll_name, "newsletter": newsletter_doc.name}):
			poll_doc = frappe.get_doc(POLL_DOCTYPE, poll_name)
		else:
			poll_doc = frappe.new_doc(POLL_DOCTYPE)
			_set_doc_field(poll_doc, newsletter_doc.name, "newsletter")

		previous_options = _get_poll_option_rows(poll_doc)
		previous_option_texts = [item["option_text"] for item in previous_options]
		current_option_texts = [item["option_text"] for item in option_rows]

		_set_doc_field(poll_doc, question, "question")
		_set_doc_field(poll_doc, cint(row.get("allow_multiple") or 0), "allow_multiple")
		_set_doc_field(poll_doc, cint(row.get("is_private") or 0), "is_private")
		_set_doc_field(poll_doc, cint(row.get("show_voters") or 0), "show_voters")
		_set_doc_field(poll_doc, _build_poll_token(poll_doc.name or ""), "placeholder_token")
		poll_doc.set("options", [])
		for option in option_rows:
			poll_doc.append(
				"options",
				{
					"option_text": option["option_text"],
				},
			)

		poll_doc.save(ignore_permissions=True)
		_set_doc_field(poll_doc, _build_poll_token(poll_doc.name), "placeholder_token")
		poll_doc.save(ignore_permissions=True)
		kept_poll_names.add(poll_doc.name)

		if previous_option_texts and previous_option_texts != current_option_texts:
			_clear_poll_votes(poll_doc.name)

	for poll_name in existing_poll_names:
		if poll_name in kept_poll_names:
			continue
		_delete_poll_with_votes(poll_name)


def _get_newsletter_polls(newsletter_name: str, current_employee=None, is_manager: bool = False) -> list[dict]:
	if not _has_poll_doctypes():
		return []

	polls = frappe.get_all(
		POLL_DOCTYPE,
		filters={"newsletter": newsletter_name},
		fields=["name", "question", "allow_multiple", "is_private", "show_voters", "placeholder_token", "modified"],
		order_by="modified asc",
		limit_page_length=0,
	)

	return [
		_serialize_poll(
			poll,
			current_employee=current_employee,
			is_manager=is_manager,
		)
		for poll in polls
	]


def _serialize_poll(poll_doc_or_row, current_employee=None, is_manager: bool = False) -> dict:
	poll_name = _safe_text(getattr(poll_doc_or_row, "name", None) or poll_doc_or_row.get("name"))
	poll_doc = poll_doc_or_row
	if not hasattr(poll_doc_or_row, "meta"):
		poll_doc = frappe.get_doc(POLL_DOCTYPE, poll_name)

	option_rows = _get_poll_option_rows(poll_doc)
	vote_rows = frappe.get_all(
		POLL_VOTE_DOCTYPE,
		filters={"poll": poll_name},
		fields=["employee", "employee_name", "option", "creation"],
		order_by="creation asc",
		limit_page_length=0,
	)

	voters_by_option = defaultdict(list)
	for vote in vote_rows:
		option_text = _safe_text(vote.get("option"))
		if not option_text:
			continue
		voters_by_option[option_text].append(
			{
				"employee": vote.get("employee"),
				"employee_name": vote.get("employee_name") or vote.get("employee"),
			}
		)

	current_employee_name = _safe_text(getattr(current_employee, "name", None) or (current_employee or {}).get("name"))
	current_employee_votes = [
		_safe_text(vote.get("option"))
		for vote in vote_rows
		if _safe_text(vote.get("employee")) == current_employee_name
	]

	is_private = bool(cint(getattr(poll_doc, "is_private", None) if hasattr(poll_doc, "meta") else poll_doc.get("is_private")))
	show_voters = bool(cint(getattr(poll_doc, "show_voters", None) if hasattr(poll_doc, "meta") else poll_doc.get("show_voters")))
	can_show_voters = is_manager or (show_voters and not is_private)

	options = []
	for row in option_rows:
		option_text = row["option_text"]
		voters = voters_by_option.get(option_text, [])
		options.append(
			{
				"name": row.get("name"),
				"option_text": option_text,
				"vote_count": len(voters),
				"voters": voters if can_show_voters else [],
			}
		)

	return {
		"name": poll_name,
		"question": _safe_text(getattr(poll_doc, "question", None) if hasattr(poll_doc, "meta") else poll_doc.get("question")),
		"allow_multiple": cint(getattr(poll_doc, "allow_multiple", None) if hasattr(poll_doc, "meta") else poll_doc.get("allow_multiple")),
		"is_private": cint(getattr(poll_doc, "is_private", None) if hasattr(poll_doc, "meta") else poll_doc.get("is_private")),
		"show_voters": cint(getattr(poll_doc, "show_voters", None) if hasattr(poll_doc, "meta") else poll_doc.get("show_voters")),
		"placeholder_token": _safe_text(
			getattr(poll_doc, "placeholder_token", None) if hasattr(poll_doc, "meta") else poll_doc.get("placeholder_token")
		)
		or _build_poll_token(poll_name),
		"total_votes": len(vote_rows),
		"my_votes": current_employee_votes,
		"options": options,
	}


def _get_poll_option_rows(poll_doc) -> list[dict]:
	option_rows = []
	for row in (poll_doc.get("options") or []):
		option_text = _safe_text(row.get("option_text"))
		if not option_text:
			continue
		option_rows.append(
			{
				"name": row.get("name"),
				"option_text": option_text,
			}
		)
	return option_rows


def _parse_poll_payload_rows(raw_rows) -> list[dict]:
	if raw_rows is None:
		return []

	rows = raw_rows
	if isinstance(raw_rows, str):
		rows = frappe.parse_json(raw_rows) or []
	if not isinstance(rows, list):
		return []

	return [row for row in rows if isinstance(row, dict)]


def _parse_poll_option_texts(raw_options) -> list[dict]:
	options = raw_options
	if isinstance(raw_options, str):
		options = frappe.parse_json(raw_options) or []
	if not isinstance(options, list):
		return []

	rows = []
	seen = set()
	for row in options:
		text = ""
		if isinstance(row, dict):
			text = _safe_text(row.get("option_text") or row.get("value") or row.get("label"))
		else:
			text = _safe_text(row)
		if not text or text in seen:
			continue
		seen.add(text)
		rows.append({"option_text": text})

	return rows


def _clear_poll_votes(poll_name: str) -> None:
	if not _has_doctype(POLL_VOTE_DOCTYPE):
		return

	vote_names = frappe.get_all(POLL_VOTE_DOCTYPE, filters={"poll": poll_name}, pluck="name")
	for vote_name in vote_names:
		frappe.delete_doc(POLL_VOTE_DOCTYPE, vote_name, ignore_permissions=True, force=1)


def _delete_poll_with_votes(poll_name: str) -> None:
	_clear_poll_votes(poll_name)
	frappe.delete_doc(POLL_DOCTYPE, poll_name, ignore_permissions=True, force=1)


def _build_poll_token(poll_name: str) -> str:
	poll_name = _safe_text(poll_name)
	if not poll_name:
		return ""
	return f"[[POLL:{poll_name}]]"


def _sync_newsletter_receipts(newsletter_doc) -> None:
	if not _has_doctype(RECEIPT_DOCTYPE):
		return

	targeted = _get_targeted_employees(newsletter_doc)
	targeted_by_employee = {row["employee"]: row for row in targeted}

	existing = frappe.get_all(
		RECEIPT_DOCTYPE,
		filters={"newsletter": newsletter_doc.name},
		fields=["name", "employee"],
		limit_page_length=0,
	)
	existing_by_employee = {row.employee: row.name for row in existing}

	for employee_name, employee_row in targeted_by_employee.items():
		if employee_name in existing_by_employee:
			continue

		receipt = frappe.new_doc(RECEIPT_DOCTYPE)
		_set_doc_field(receipt, newsletter_doc.name, "newsletter")
		_set_doc_field(receipt, employee_name, "employee")
		_set_doc_field(receipt, employee_row.get("employee_name"), "employee_name")
		_set_doc_field(receipt, employee_row.get("designation"), "designation")
		_set_doc_field(receipt, 0, "is_read")
		receipt.insert(ignore_permissions=True)

	for employee_name, receipt_name in existing_by_employee.items():
		if employee_name in targeted_by_employee:
			continue
		frappe.delete_doc(RECEIPT_DOCTYPE, receipt_name, ignore_permissions=True, force=1)

	_update_newsletter_read_stats(newsletter_doc.name)


def _get_targeted_employees(newsletter_doc) -> list[dict]:
	audience_mode = _safe_text(_get_doc_value(newsletter_doc, "audience_mode", default="All Employees"))
	target_roles = set(
		_parse_json_array(_get_doc_value(newsletter_doc, "target_roles_json", "target_roles", default=[]))
	)
	target_employees = set(
		_parse_json_array(
			_get_doc_value(newsletter_doc, "target_employees_json", "target_employees", default=[])
		)
	)
	excluded_employees = set(
		_parse_json_array(
			_get_doc_value(newsletter_doc, "excluded_employees_json", "excluded_employees", default=[])
		)
	)

	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "employee_name", "designation", "user_id"],
		limit_page_length=0,
	)

	if audience_mode == "Specific Employees":
		return [
			{
				"employee": row.name,
				"employee_name": row.employee_name,
				"designation": row.designation,
			}
			for row in employees
			if row.name in target_employees
		]

	if audience_mode == "By Role":
		roles_by_user = _get_roles_by_users([row.user_id for row in employees if row.user_id])
		rows = []
		for row in employees:
			user_roles = set(roles_by_user.get(row.user_id, []))
			if row.designation:
				user_roles.add(row.designation)
			if not target_roles.intersection(user_roles):
				continue
			if row.name in excluded_employees:
				continue
			rows.append(
				{
					"employee": row.name,
					"employee_name": row.employee_name,
					"designation": row.designation,
				}
			)
		return rows

	return [
		{
			"employee": row.name,
			"employee_name": row.employee_name,
			"designation": row.designation,
		}
		for row in employees
	]


def _can_employee_view_newsletter(newsletter_doc, current_employee) -> bool:
	if _is_newsletter_manager():
		return True

	if not current_employee:
		return False

	audience_mode = _safe_text(_get_doc_value(newsletter_doc, "audience_mode", default="All Employees"))
	if audience_mode == "All Employees":
		return True

	target_employees = set(
		_parse_json_array(
			_get_doc_value(newsletter_doc, "target_employees_json", "target_employees", default=[])
		)
	)
	if audience_mode == "Specific Employees":
		return current_employee.name in target_employees

	target_roles = set(
		_parse_json_array(_get_doc_value(newsletter_doc, "target_roles_json", "target_roles", default=[]))
	)
	excluded_employees = set(
		_parse_json_array(
			_get_doc_value(newsletter_doc, "excluded_employees_json", "excluded_employees", default=[])
		)
	)
	if audience_mode == "By Role" and current_employee.name in excluded_employees:
		return False
	if not target_roles:
		return False

	user_roles = set(frappe.get_roles(frappe.session.user))
	if current_employee.designation:
		user_roles.add(current_employee.designation)

	return bool(target_roles.intersection(user_roles))


def _is_newsletter_read_by_employee(newsletter_name: str, current_employee) -> bool:
	if not current_employee:
		return False

	if not _has_doctype(RECEIPT_DOCTYPE):
		return False

	return bool(
		frappe.db.get_value(
			RECEIPT_DOCTYPE,
			{"newsletter": newsletter_name, "employee": current_employee.name},
			"is_read",
		)
	)


def _get_newsletter_stats(newsletter_name: str) -> dict:
	if _has_doctype(RECEIPT_DOCTYPE):
		recipient_count = frappe.db.count(RECEIPT_DOCTYPE, {"newsletter": newsletter_name})
		read_count = frappe.db.count(RECEIPT_DOCTYPE, {"newsletter": newsletter_name, "is_read": 1})
	else:
		recipient_count = cint(
			frappe.db.get_value(NEWSLETTER_DOCTYPE, newsletter_name, "recipient_count") or 0
		)
		read_count = cint(frappe.db.get_value(NEWSLETTER_DOCTYPE, newsletter_name, "read_count") or 0)

	unread_count = max(recipient_count - read_count, 0)
	read_rate = round((read_count / recipient_count) * 100, 1) if recipient_count else 0

	return {
		"recipient_count": recipient_count,
		"read_count": read_count,
		"unread_count": unread_count,
		"read_rate": read_rate,
	}


def _update_newsletter_read_stats(newsletter_name: str) -> None:
	if not _has_doctype(NEWSLETTER_DOCTYPE):
		return

	stats = _get_newsletter_stats(newsletter_name)
	doc = frappe.get_doc(NEWSLETTER_DOCTYPE, newsletter_name)
	_set_doc_field(doc, stats["recipient_count"], "recipient_count", "total_recipients")
	_set_doc_field(doc, stats["read_count"], "read_count", "total_reads")
	_set_doc_field(doc, stats["unread_count"], "unread_count")
	_set_doc_field(doc, stats["read_rate"], "read_rate")
	doc.save(ignore_permissions=True)


def _get_roles_by_users(user_ids: list[str]) -> dict[str, list[str]]:
	if not user_ids:
		return {}

	has_roles = frappe.get_all(
		"Has Role",
		filters={"parenttype": "User", "parent": ["in", user_ids]},
		fields=["parent", "role"],
		limit_page_length=0,
	)
	rows = defaultdict(list)
	for row in has_roles:
		role = _safe_text(row.get("role"))
		if role in {"All", "Guest"}:
			continue
		rows[row.get("parent")].append(role)

	return rows


def _build_role_options(roles: set[str]) -> list[dict]:
	rows = []
	for role in sorted(filter(None, roles)):
		role_value = _safe_text(role)
		if not role_value:
			continue
		rows.append(
			{
				"value": role_value,
				"label": _safe_text(_(role_value)) or role_value,
			}
		)

	rows.sort(key=lambda row: row["label"])
	return rows


def _set_doc_field(doc, value, *fieldnames: str) -> None:
	for fieldname in fieldnames:
		if not fieldname:
			continue
		if doc.meta.has_field(fieldname):
			doc.set(fieldname, value)
			return


def _get_doc_value(doc, *fieldnames: str, default=None):
	for fieldname in fieldnames:
		if fieldname and doc.meta.has_field(fieldname):
			value = doc.get(fieldname)
			if value not in (None, ""):
				return value
	return default


def _parse_payload(payload: str | dict | None) -> dict:
	if not payload:
		return {}
	if isinstance(payload, dict):
		return payload

	try:
		return frappe.parse_json(payload) or {}
	except Exception:
		return json.loads(payload)


def _parse_json_array(value) -> list[str]:
	if value is None:
		return []
	if isinstance(value, list):
		return [
			_safe_text(item)
			for item in value
			if _safe_text(item)
		]
	if not isinstance(value, str):
		return []

	text = value.strip()
	if not text:
		return []

	try:
		parsed = frappe.parse_json(text)
		if isinstance(parsed, list):
			return [_safe_text(item) for item in parsed if _safe_text(item)]
	except Exception:
		pass

	return [_safe_text(item) for item in text.split(",") if _safe_text(item)]


def _safe_text(value) -> str:
	if value is None:
		return ""
	return str(value).strip()


def _get_current_employee(required: bool = False):
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user, "status": "Active"},
		["name", "employee_name", "designation"],
		as_dict=True,
	)
	if required and not employee:
		frappe.throw(_("Active employee record is required for this action."))
	return employee


def _is_newsletter_manager() -> bool:
	roles = set(frappe.get_roles(frappe.session.user))
	return bool(roles.intersection(NEWSLETTER_MANAGER_ROLES))


def _assert_newsletter_manager() -> None:
	if not _is_newsletter_manager():
		frappe.throw(_("You are not allowed to manage newsletters."))


def _has_doctype(doctype_name: str) -> bool:
	return bool(frappe.db.exists("DocType", doctype_name))


def _has_poll_doctypes() -> bool:
	return _has_doctype(POLL_DOCTYPE) and _has_doctype(POLL_OPTION_DOCTYPE) and _has_doctype(POLL_VOTE_DOCTYPE)


def _ensure_poll_doctype() -> None:
	if _has_doctype(POLL_DOCTYPE):
		return
	frappe.throw(_("DocType HR Newsletter Poll was not found. Please migrate the site first."))


def _get_user_full_name(user_id: str | None) -> str:
	user = _safe_text(user_id)
	if not user:
		return ""
	return _safe_text(frappe.db.get_value("User", user, "full_name") or user)


def _ensure_newsletter_doctype() -> None:
	if not _has_doctype(NEWSLETTER_DOCTYPE):
		frappe.throw(
			_(
				"DocType HR Newsletter was not found. Please create HR Newsletter and HR Newsletter Receipt doctypes first."
			)
		)
