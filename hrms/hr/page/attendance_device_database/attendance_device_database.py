import csv
import io
import traceback
from collections import defaultdict
import importlib
from uuid import uuid4

import frappe
from frappe import _
from frappe.utils import cint, cstr
from frappe.utils.background_jobs import get_job_status

from hrms.api.employee_checkin_remote_sync import (
	fetch_source_logs_with_runtime_config,
	normalize_code,
	normalize_text,
)
from hrms.hr.page.attendance_interpolation.attendance_interpolation import _build_runtime_config, _get_settings_doc

JOB_CACHE_PREFIX = "attendance_device_database_job"
JOB_CACHE_TTL_SECONDS = 24 * 60 * 60
_EXPORTER_MODULE = None


def _get_exporter():
	global _EXPORTER_MODULE
	if _EXPORTER_MODULE:
		return _EXPORTER_MODULE

	try:
		_EXPORTER_MODULE = importlib.import_module("hrms.api.employee_checkin_export")
	except ModuleNotFoundError as exc:
		missing = exc.name or "dependency"
		frappe.throw(
			_("Missing Python dependency '{0}'. Install required packages first (for example: python-tds, jdatetime).").format(
				missing
			)
		)

	return _EXPORTER_MODULE


def _build_config(source_date_from="", source_date_to="", max_source_rows=0):
	doc = _get_settings_doc()
	if not doc.enabled:
		frappe.throw(_("Attendance Interpolation is disabled in settings."))
	return _build_runtime_config(
		doc,
		dry_run=True,
		source_date_from=source_date_from,
		source_date_to=source_date_to,
		max_source_rows=max_source_rows,
		preview_limit=50,
	)


def _sort_key_employee_code(value):
	text = cstr(value or "").strip().upper()
	if not text:
		return (1, "", 10**9)
	if "-" in text:
		prefix, suffix = text.rsplit("-", 1)
		try:
			return (0, prefix, int(suffix))
		except ValueError:
			return (0, prefix, 10**9)
	return (0, text, 10**9)


def _load_employee_mapping():
	fields = ["name", "employee_name", "employee_number", "attendance_device_id"]
	employee_meta = frappe.get_meta("Employee")
	if employee_meta.has_field("custom_source_person_id"):
		fields.append("custom_source_person_id")
	employees = frappe.get_all("Employee", fields=fields, limit_page_length=200000)
	rows = []
	if frappe.db.exists("DocType", "Employee Attendance Device Mapping"):
		rows = frappe.get_all(
			"Employee Attendance Device Mapping",
			fields=["parent", "attendance_device_id", "device_id"],
			filters={"parenttype": "Employee"},
			limit_page_length=0,
		)

	employee_index = {row["name"]: row for row in employees}
	device_master = {}
	if frappe.db.exists("DocType", "Attendance Device"):
		for device in frappe.get_all(
			"Attendance Device",
			fields=["name", "device_id", "company", "location"],
			limit_page_length=0,
		):
			device_master[normalize_text(device.get("name"))] = {
				"device_id_value": normalize_text(device.get("device_id")),
				"company": normalize_text(device.get("company")),
				"location": normalize_text(device.get("location")),
			}
	device_map = defaultdict(list)
	person_map = {}
	employee_has_device_mapping = set()

	for employee in employees:
		employee_key = normalize_text(employee.get("name"))
		employee_name = normalize_text(employee.get("employee_name"))
		employee_number = normalize_code(employee.get("employee_number"))
		source_person_id = normalize_code(employee.get("custom_source_person_id"))
		legacy_device_code = normalize_code(employee.get("attendance_device_id"))

		if source_person_id:
			person_map[source_person_id] = employee_key
		if employee_number:
			person_map[employee_number] = employee_key
		if legacy_device_code:
			employee_has_device_mapping.add(employee_key)
			device_map[legacy_device_code].append(
				{
					"employee": employee_key,
					"employee_name": employee_name,
					"employee_number": employee_number,
					"source_person_id": source_person_id,
					"mapping_device_id": "",
					"mapping_source": "legacy_field",
				}
			)

	for row in rows:
		employee = employee_index.get(row.get("parent")) or {}
		employee_key = normalize_text(employee.get("name"))
		if not employee_key:
			continue
		device_code = normalize_code(row.get("attendance_device_id"))
		if not device_code:
			continue
		employee_has_device_mapping.add(employee_key)
		device_map[device_code].append(
			{
				"employee": employee_key,
				"employee_name": normalize_text(employee.get("employee_name")),
				"employee_number": normalize_code(employee.get("employee_number")),
				"source_person_id": normalize_code(employee.get("custom_source_person_id")),
				"mapping_device_id": normalize_text(row.get("device_id")),
				"mapping_device_id_value": normalize_text((device_master.get(normalize_text(row.get("device_id"))) or {}).get("device_id_value")),
				"mapping_company": normalize_text((device_master.get(normalize_text(row.get("device_id"))) or {}).get("company")),
				"mapping_location": normalize_text((device_master.get(normalize_text(row.get("device_id"))) or {}).get("location")),
				"mapping_source": "custom_table",
			}
		)

	for key, values in list(device_map.items()):
		unique = {}
		for value in values:
			unique[value["employee"]] = value
		device_map[key] = list(unique.values())

	employees_missing_device_code = []
	for employee in employees:
		employee_key = normalize_text(employee.get("name"))
		if not employee_key:
			continue
		if employee_key in employee_has_device_mapping:
			continue
		employees_missing_device_code.append(
			{
				"device_code": "",
				"source_employee_code": "",
				"device_id": "",
				"device_identifier": "",
				"system_branch_code": "",
				"system_branch_name": "",
				"employee": employee_key,
				"employee_name": normalize_text(employee.get("employee_name")),
				"employee_number": normalize_code(employee.get("employee_number")),
				"source_person_id": normalize_code(employee.get("custom_source_person_id")),
				"source_full_name": "",
				"mapping_source": "employee_missing_device_code",
				"source_database": "",
				"source_hits": 0,
				"match_rule": "",
				"device_company": "",
				"device_location": "",
			}
		)

	return person_map, device_map, employees_missing_device_code


def _filter_matches_for_source(matches, source_branch_code):
	if not matches:
		return []

	branch_code = normalize_code(source_branch_code)
	if not branch_code:
		return matches

	filtered = []
	for match in matches:
		device_id_value = normalize_code(match.get("mapping_device_id_value"))
		device_link = normalize_code(match.get("mapping_device_id"))
		if device_id_value and device_id_value == branch_code:
			filtered.append(match)
			continue
		if device_link and device_link == branch_code:
			filtered.append(match)
			continue

	return filtered or matches


def _resolve_employee_strict(log_row, by_person_id, by_device_code):
	person_id = normalize_code(log_row.get("Person_ID"))
	device_code = normalize_code(log_row.get("Employee_Code"))

	if person_id and person_id in by_person_id:
		return by_person_id[person_id], "person_id"

	if device_code and device_code in by_device_code:
		unique_matches = {}
		for employee in by_device_code[device_code]:
			if employee and employee.get("name"):
				unique_matches[employee.get("name")] = employee
		matches = list(unique_matches.values())

		if len(matches) == 1:
			return matches[0], "employee_code"

		if person_id:
			for employee in matches:
				if normalize_code(employee.get("employee_number")) == person_id:
					return employee, "employee_code+person_id"
				if normalize_code(employee.get("custom_source_person_id")) == person_id:
					return employee, "employee_code+source_person_id"

		return None, "ambiguous_employee_code"

	return None, ""


def _build_device_report_payload(source_logs, connection_info):
	person_map, device_map, employees_missing_device_code = _load_employee_mapping()
	by_person_id, by_device_code, _by_name = _get_exporter().load_employee_index()
	source_hits = defaultdict(int)
	source_databases_by_device = defaultdict(set)
	unmatched_groups = {}
	rows = []
	summary = []

	for log_row in source_logs:
		person_id = normalize_code(log_row.get("Person_ID"))
		device_code = normalize_code(log_row.get("Employee_Code"))
		attendance_employee_code = device_code or person_id
		source_full_name = normalize_text(log_row.get("Full_Name"))
		source_database = normalize_text(log_row.get("Source_Database"))
		source_branch_code = normalize_code(log_row.get("Branch_Code"))
		source_machine_no = normalize_code(log_row.get("Machine_No"))
		matched_employee, match_rule = _resolve_employee_strict(
			log_row, by_person_id, by_device_code
		)

		if not matched_employee:
			unmatched_key = (
				device_code,
				person_id,
				source_full_name,
				source_database,
			)
			current = unmatched_groups.get(unmatched_key)
			if not current:
				current = {
					"device_code": attendance_employee_code,
					"source_employee_code": device_code,
					"device_id": "",
					"device_identifier": "",
					"system_branch_code": "",
					"system_branch_name": "",
					"employee": "",
					"employee_name": source_full_name,
					"employee_number": "",
					"source_person_id": person_id,
					"source_full_name": source_full_name,
					"mapping_source": "missing_employee",
					"source_database": source_database,
					"source_hits": 0,
					"match_rule": "",
					"device_company": "",
					"device_location": "",
					"source_branch_code": source_branch_code,
					"source_machine_no": source_machine_no,
				}
			current["source_hits"] = cint(current["source_hits"]) + 1
			unmatched_groups[unmatched_key] = current

		if not attendance_employee_code:
			continue
		source_hits[attendance_employee_code] += 1
		source_databases_by_device[attendance_employee_code].add(source_database)
		map_lookup_code = device_code or person_id
		matches = _filter_matches_for_source(
			device_map.get(map_lookup_code, []),
			source_branch_code=source_branch_code,
		)
		source_employee = normalize_text((matched_employee or {}).get("name")) or person_map.get(person_id, "")
		source_employee_name = normalize_text((matched_employee or {}).get("employee_name"))
		source_employee_number = normalize_code((matched_employee or {}).get("employee_number"))

		if not matches:
			rows.append(
				{
					"device_code": attendance_employee_code,
					"source_employee_code": device_code,
					"device_id": "",
					"employee": source_employee,
					"employee_name": source_employee_name,
					"employee_number": source_employee_number,
					"source_person_id": person_id,
					"source_full_name": source_full_name,
					"mapping_source": "not_mapped",
					"source_database": source_database,
					"source_hits": source_hits[attendance_employee_code],
					"match_rule": match_rule,
					"device_company": "",
					"device_location": "",
					"device_identifier": "",
					"system_branch_code": "",
					"system_branch_name": "",
					"source_branch_code": source_branch_code,
					"source_machine_no": source_machine_no,
					"source_branch_codes": source_branch_code,
				}
			)
			continue

		for match in matches:
			rows.append(
				{
					"device_code": attendance_employee_code,
					"source_employee_code": device_code,
					"device_id": match.get("mapping_device_id") or "",
					"employee": match.get("employee") or "",
					"employee_name": match.get("employee_name") or "",
					"employee_number": match.get("employee_number") or "",
					"source_person_id": match.get("source_person_id") or person_id,
					"source_full_name": source_full_name,
					"mapping_source": match.get("mapping_source") or "",
					"source_database": source_database,
					"source_hits": source_hits[attendance_employee_code],
					"match_rule": match_rule,
					"device_company": match.get("mapping_company") or "",
					"device_location": match.get("mapping_location") or "",
					"device_identifier": match.get("mapping_device_id_value") or "",
					"system_branch_code": match.get("mapping_device_id_value") or "",
					"system_branch_name": match.get("mapping_location") or match.get("mapping_company") or "",
					"source_branch_code": source_branch_code,
					"source_machine_no": source_machine_no,
					"source_branch_codes": source_branch_code,
				}
			)

	# Include mapped devices with zero source hits.
	for device_code, matches in device_map.items():
		if source_hits.get(device_code, 0) > 0:
			continue
		for match in matches:
			rows.append(
				{
					"device_code": device_code,
					"source_employee_code": "",
					"device_id": match.get("mapping_device_id") or "",
					"employee": match.get("employee") or "",
					"employee_name": match.get("employee_name") or "",
					"employee_number": match.get("employee_number") or "",
					"source_person_id": match.get("source_person_id") or "",
					"source_full_name": "",
					"mapping_source": match.get("mapping_source") or "",
					"source_database": ", ".join(sorted(source_databases_by_device.get(device_code) or [])),
					"source_hits": source_hits.get(device_code, 0),
					"match_rule": "",
					"device_company": match.get("mapping_company") or "",
					"device_location": match.get("mapping_location") or "",
					"device_identifier": match.get("mapping_device_id_value") or "",
					"system_branch_code": match.get("mapping_device_id_value") or "",
					"system_branch_name": match.get("mapping_location") or match.get("mapping_company") or "",
					"source_branch_code": "",
					"source_machine_no": "",
					"source_branch_codes": "",
				}
			)

	# Explicitly include unmatched source rows (employee not found in ERP).
	rows.extend(unmatched_groups.values())
	rows.extend(employees_missing_device_code)

	# Deduplicate identical rows first.
	unique = {}
	for row in rows:
		key = (
			row.get("device_code") or "",
			row.get("source_employee_code") or "",
			row.get("employee") or "",
			row.get("employee_number") or "",
			row.get("source_person_id") or "",
			row.get("source_full_name") or "",
			row.get("mapping_source") or "",
			row.get("source_database") or "",
			row.get("device_company") or "",
			row.get("device_location") or "",
			row.get("device_identifier") or "",
			row.get("system_branch_code") or "",
			row.get("system_branch_name") or "",
			row.get("source_branch_code") or "",
			row.get("source_machine_no") or "",
			row.get("source_branch_codes") or "",
		)
		current = unique.get(key)
		if not current:
			unique[key] = row
			continue
		current["source_hits"] = max(cint(current.get("source_hits")), cint(row.get("source_hits")))
		if row.get("source_database"):
			if current.get("source_database"):
				merged = {item.strip() for item in (current["source_database"] + "," + row["source_database"]).split(",") if item.strip()}
				current["source_database"] = ", ".join(sorted(merged))
			else:
				current["source_database"] = row["source_database"]
		if not current.get("match_rule") and row.get("match_rule"):
			current["match_rule"] = row["match_rule"]
		if not current.get("source_full_name") and row.get("source_full_name"):
			current["source_full_name"] = row["source_full_name"]
		if row.get("source_branch_codes"):
			existing = {x.strip() for x in cstr(current.get("source_branch_codes") or "").split(",") if x.strip()}
			existing.update({x.strip() for x in cstr(row.get("source_branch_codes") or "").split(",") if x.strip()})
			current["source_branch_codes"] = ", ".join(sorted(existing))

	rows = list(unique.values())

	# Aggregate by business key to avoid duplicated lines across databases.
	aggregated = {}
	for row in rows:
		agg_key = (
			row.get("device_code") or "",
			row.get("source_employee_code") or "",
			row.get("device_id") or "",
			row.get("device_company") or "",
			row.get("device_location") or "",
			row.get("device_identifier") or "",
			row.get("system_branch_code") or "",
			row.get("system_branch_name") or "",
			row.get("source_branch_code") or "",
			row.get("source_machine_no") or "",
			row.get("employee") or "",
			row.get("employee_name") or "",
			row.get("employee_number") or "",
			row.get("source_person_id") or "",
			row.get("source_full_name") or "",
			row.get("mapping_source") or "",
		)
		item = aggregated.get(agg_key)
		if not item:
			item = dict(row)
			item["_source_db_set"] = {
				db.strip()
				for db in cstr(row.get("source_database") or "").split(",")
				if db.strip()
			}
			item["_match_rule_set"] = {
				rule.strip()
				for rule in cstr(row.get("match_rule") or "").split(",")
				if rule.strip()
			}
			item["_source_branch_codes_set"] = {
				code.strip()
				for code in cstr(row.get("source_branch_codes") or "").split(",")
				if code.strip()
			}
			item["source_hits"] = cint(row.get("source_hits"))
			aggregated[agg_key] = item
			continue

		item["source_hits"] = max(cint(item.get("source_hits")), cint(row.get("source_hits")))
		item["_source_db_set"].update(
			{db.strip() for db in cstr(row.get("source_database") or "").split(",") if db.strip()}
		)
		item["_match_rule_set"].update(
			{rule.strip() for rule in cstr(row.get("match_rule") or "").split(",") if rule.strip()}
		)
		item["_source_branch_codes_set"].update(
			{code.strip() for code in cstr(row.get("source_branch_codes") or "").split(",") if code.strip()}
		)

	rows = []
	for item in aggregated.values():
		item["source_database"] = ", ".join(sorted(item.pop("_source_db_set", set())))
		item["match_rule"] = ", ".join(sorted(item.pop("_match_rule_set", set())))
		item["source_branch_codes"] = ", ".join(sorted(item.pop("_source_branch_codes_set", set())))
		rows.append(item)

	grouped = defaultdict(list)
	for row in rows:
		grouped[row["device_code"]].append(row)

	for device_code in sorted(grouped.keys()):
		if not device_code:
			continue
		employees = {
			(entry.get("employee") or entry.get("source_person_id") or "").strip()
			for entry in grouped[device_code]
			if (entry.get("employee") or entry.get("source_person_id") or "").strip()
		}
		summary.append(
			{
				"device_code": device_code,
				"employee_count": len(employees),
				"device_id": next((entry.get("device_id") for entry in grouped[device_code] if entry.get("device_id")), ""),
				"source_hits": source_hits.get(device_code, 0),
			}
		)

	return {
		"connection": connection_info,
		"source_device_count": len(source_hits),
		"mapped_device_count": len(summary),
		"summary": summary,
		"rows": sorted(
			rows,
			key=lambda item: (
				_sort_key_employee_code(item.get("employee")),
				item.get("device_code") or "zzz",
				item.get("source_machine_no") or "",
				item.get("source_branch_code") or "",
				item.get("source_person_id") or "",
			),
		),
	}


def _job_cache_key(job_token):
	return f"{JOB_CACHE_PREFIX}:{job_token}"


def _save_job_state(job_token, payload):
	frappe.cache().set_value(
		_job_cache_key(job_token),
		payload,
		expires_in_sec=JOB_CACHE_TTL_SECONDS,
		shared=True,
	)


def _get_job_state(job_token):
	return frappe.cache().get_value(_job_cache_key(job_token), shared=True) or {}


def _normalize_job_status(status):
	if not status:
		return ""
	if hasattr(status, "value"):
		return str(status.value).lower()
	return str(status).lower()


def _normalize_user(value):
	return str(value or "").strip().lower()


def _assert_job_access(state):
	if not state:
		frappe.throw(_("Job not found or expired."))
	if _normalize_user(state.get("owner")) != _normalize_user(frappe.session.user):
		frappe.throw(_("You do not have access to this job."))


def _run_preview_device_database_job(job_token, config):
	state = _get_job_state(job_token)
	if not state:
		return
	state["status"] = "started"
	_save_job_state(job_token, state)

	try:
		result = fetch_source_logs_with_runtime_config(config, site_override=config.get("site"))
		source_logs = result.pop("source_logs", [])
		report = _build_device_report_payload(source_logs, connection_info=result)
		state["status"] = "finished"
		state["error"] = ""
		state["result"] = report
		_save_job_state(job_token, state)
	except Exception:
		state["status"] = "failed"
		state["error"] = traceback.format_exc()
		state["result"] = None
		_save_job_state(job_token, state)
		raise


def _enqueue_device_database_job(config):
	job_token = uuid4().hex
	job_id = f"attendance_device_database_preview_{frappe.session.user}_{job_token[:10]}"
	_save_job_state(
		job_token,
		{
			"owner": frappe.session.user,
			"job_id": job_id,
			"status": "queued",
			"result": None,
			"error": "",
		},
	)
	frappe.enqueue(
		"hrms.hr.page.attendance_device_database.attendance_device_database._run_preview_device_database_job",
		queue="long",
		timeout=60 * 60 * 2,
		job_id=job_id,
		job_token=job_token,
		config=config,
		enqueue_after_commit=True,
	)
	return {
		"job_token": job_token,
		"job_id": job_id,
		"status": "queued",
		"poll_seconds": 2,
	}


@frappe.whitelist()
def preview_device_database(source_date_from="", source_date_to="", max_source_rows=0):
	frappe.only_for(("HR Manager", "System Manager"))
	config = _build_config(
		source_date_from=source_date_from,
		source_date_to=source_date_to,
		max_source_rows=max(0, cint(max_source_rows)),
	)
	result = fetch_source_logs_with_runtime_config(config, site_override=config.get("site"))
	source_logs = result.pop("source_logs", [])
	return _build_device_report_payload(source_logs, connection_info=result)


@frappe.whitelist()
def enqueue_preview_device_database(source_date_from="", source_date_to="", max_source_rows=0):
	frappe.only_for(("HR Manager", "System Manager"))
	config = _build_config(
		source_date_from=source_date_from,
		source_date_to=source_date_to,
		max_source_rows=max(0, cint(max_source_rows)),
	)
	return _enqueue_device_database_job(config)


@frappe.whitelist()
def get_device_database_job_status(job_token):
	frappe.only_for(("HR Manager", "System Manager"))
	state = _get_job_state(job_token)
	_assert_job_access(state)

	status = _normalize_job_status(state.get("status"))
	if not status:
		status = "queued"
	if status not in {"finished", "failed"}:
		job_state = _normalize_job_status(get_job_status(state.get("job_id")))
		if job_state:
			status = job_state

	response = {
		"job_id": state.get("job_id"),
		"status": status,
		"error": state.get("error") or "",
		"result": None,
	}
	if status == "finished":
		response["result"] = state.get("result") or {}
	elif status == "failed" and not response["error"]:
		response["error"] = _("Background job failed. Check RQ Job log for details.")
	return response


@frappe.whitelist()
def download_device_database_csv(job_token="", source_date_from="", source_date_to="", max_source_rows=0):
	frappe.only_for(("HR Manager", "System Manager"))
	report = None
	if job_token:
		state = _get_job_state(job_token)
		_assert_job_access(state)
		report = state.get("result")

	if not report:
		config = _build_config(
			source_date_from=source_date_from,
			source_date_to=source_date_to,
			max_source_rows=max(0, cint(max_source_rows)),
		)
		result = fetch_source_logs_with_runtime_config(config, site_override=config.get("site"))
		source_logs = result.pop("source_logs", [])
		report = _build_device_report_payload(source_logs, connection_info=result)

	buffer = io.StringIO()
	fieldnames = [
		"device_code",
		"source_employee_code",
		"device_id",
		"device_company",
		"device_location",
		"device_identifier",
		"system_branch_code",
		"system_branch_name",
		"employee",
		"employee_name",
		"employee_number",
		"source_full_name",
		"source_branch_codes",
		"source_branch_code",
		"source_machine_no",
		"mapping_source",
		"source_database",
		"source_hits",
		"match_rule",
	]
	writer = csv.DictWriter(buffer, fieldnames=fieldnames)
	writer.writeheader()
	for row in report["rows"]:
		writer.writerow(row)

	filename = "attendance_device_database_report.csv"
	frappe.response["type"] = "download"
	frappe.response["filename"] = filename
	frappe.response["filecontent"] = buffer.getvalue()
	frappe.response["content_type"] = "text/csv; charset=utf-8"
