import traceback
from uuid import uuid4

import frappe
from frappe import _
from frappe.utils import cint
from frappe.utils.background_jobs import get_job_status

from hrms.api.employee_checkin_remote_sync import run_sync_with_runtime_config

JOB_CACHE_PREFIX = "attendance_interpolation_job"
JOB_CACHE_TTL_SECONDS = 24 * 60 * 60


def _to_bool(value):
	return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _get_settings_doc():
	return frappe.get_single("Attendance Interpolation Settings")


def _get_secret(doc, fieldname):
	try:
		return doc.get_password(fieldname, raise_exception=False) or ""
	except Exception:
		return ""


def _build_runtime_config(doc, dry_run, source_date_from="", source_date_to="", max_source_rows=None, preview_limit=None):
	connection_mode = (doc.connection_mode or "vpn_direct_sql").strip().lower()
	target_site = (doc.target_site or frappe.local.site).strip()

	max_rows_value = doc.max_source_rows if max_source_rows is None else max_source_rows
	preview_limit_value = doc.preview_limit if preview_limit is None else preview_limit

	config = {
		"enabled": 1 if doc.enabled else 0,
		"site": target_site,
		"connection_mode": connection_mode,
		"dry_run": 1 if dry_run else 0,
		"batch_size": cint(doc.batch_size) or 1000,
		"skip_missing_employees": 1 if doc.skip_missing_employees else 0,
		"auto_create_missing_employees": 1 if cint(getattr(doc, "auto_create_missing_employees", 1)) else 0,
		"preserve_manual_changes": 1 if cint(getattr(doc, "preserve_manual_changes", 1)) else 0,
		"default_employee_company": (getattr(doc, "default_employee_company", "") or "").strip(),
		"dedupe_on": doc.dedupe_on or "employee+time+log_type",
		"source_date_from": (source_date_from or doc.source_date_from or "").strip(),
		"source_date_to": (source_date_to or doc.source_date_to or "").strip(),
		"max_source_rows": max(0, cint(max_rows_value)),
		"preview_limit": max(1, cint(preview_limit_value) or 20),
		"vpn": {
			"gateway_host": (doc.vpn_gateway_host or "").strip(),
			"gateway_port": cint(doc.vpn_gateway_port) or 1600,
			"username": (doc.vpn_username or "").strip(),
			"password": _get_secret(doc, "vpn_password"),
			"vpn_command": (doc.vpn_command or "openfortivpn").strip(),
			"realm": (doc.vpn_realm or "").strip(),
			"trusted_cert": (doc.vpn_trusted_cert or "").strip(),
			"insecure_ssl": 1 if doc.vpn_insecure_ssl else 0,
			"disable_default_route": 1 if cint(getattr(doc, "vpn_disable_default_route", 1)) else 0,
			"targets": [
				line.strip()
				for line in (doc.vpn_targets or "").replace(",", "\n").splitlines()
				if line.strip()
			],
			"connect_timeout_seconds": cint(doc.vpn_connect_timeout_seconds) or 40,
			"ready_wait_seconds": cint(doc.vpn_ready_wait_seconds) or 90,
			"poll_seconds": cint(doc.vpn_poll_seconds) or 2,
		},
		"ssh_tunnel": {
			"gateway_host": (doc.ssh_gateway_host or "").strip(),
			"gateway_port": cint(doc.ssh_gateway_port) or 22,
			"gateway_user": (doc.ssh_gateway_user or "").strip(),
			"gateway_password": _get_secret(doc, "ssh_gateway_password"),
			"local_bind_host": (doc.ssh_local_bind_host or "127.0.0.1").strip(),
			"local_bind_port": cint(doc.ssh_local_bind_port) or 11433,
			"remote_sql_host": (doc.ssh_remote_sql_host or "").strip(),
			"remote_sql_port": cint(doc.ssh_remote_sql_port) or 1433,
			"connect_timeout_seconds": cint(doc.ssh_connect_timeout_seconds) or 30,
			"poll_seconds": cint(doc.ssh_poll_seconds) or 1,
			"strict_host_key_checking": 0,
			"sshpass_command": "sshpass",
		},
		"sql": {
			"host": (doc.sql_host or "").strip(),
			"port": cint(doc.sql_port) or 1433,
			"database": (doc.sql_database or "EOS").strip(),
			"user": (doc.sql_user or "").strip(),
			"password": _get_secret(doc, "sql_password"),
		},
	}

	return config


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


def _assert_job_access(state):
	if not state:
		frappe.throw(_("Job not found or expired."))
	if normalize_user(state.get("owner")) != normalize_user(frappe.session.user):
		frappe.throw(_("You do not have access to this job."))


def normalize_user(value):
	return str(value or "").strip().lower()


def _enqueue_interpolation_job(config, action):
	job_token = uuid4().hex
	job_id = f"attendance_interpolation_{action}_{frappe.session.user}_{job_token[:10]}"
	_save_job_state(
		job_token,
		{
			"owner": frappe.session.user,
			"job_id": job_id,
			"status": "queued",
			"action": action,
			"result": None,
			"error": "",
		},
	)
	frappe.enqueue(
		"hrms.hr.page.attendance_interpolation.attendance_interpolation._run_interpolation_job",
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


def _run_interpolation_job(job_token, config):
	state = _get_job_state(job_token)
	if not state:
		return
	state["status"] = "started"
	_save_job_state(job_token, state)

	try:
		result = run_sync_with_runtime_config(config, site_override=config.get("site"))
		state["status"] = "finished"
		state["result"] = result
		state["error"] = ""
		_save_job_state(job_token, state)
	except Exception:
		state["status"] = "failed"
		state["error"] = traceback.format_exc()
		state["result"] = None
		_save_job_state(job_token, state)
		raise


@frappe.whitelist()
def get_interpolation_settings():
	frappe.only_for(("HR Manager", "System Manager"))
	doc = _get_settings_doc()

	return {
		"enabled": 1 if doc.enabled else 0,
		"target_site": doc.target_site,
		"connection_mode": doc.connection_mode,
		"source_date_from": doc.source_date_from,
		"source_date_to": doc.source_date_to,
		"max_source_rows": doc.max_source_rows,
		"preview_limit": doc.preview_limit,
		"dedupe_on": doc.dedupe_on,
		"skip_missing_employees": doc.skip_missing_employees,
		"auto_create_missing_employees": cint(getattr(doc, "auto_create_missing_employees", 1)),
		"preserve_manual_changes": cint(getattr(doc, "preserve_manual_changes", 1)),
		"default_employee_company": getattr(doc, "default_employee_company", ""),
		"vpn_disable_default_route": cint(getattr(doc, "vpn_disable_default_route", 1)),
		"batch_size": doc.batch_size,
		"has_vpn_password": 1 if _get_secret(doc, "vpn_password") else 0,
		"has_sql_password": 1 if _get_secret(doc, "sql_password") else 0,
		"has_ssh_password": 1 if _get_secret(doc, "ssh_gateway_password") else 0,
	}


@frappe.whitelist()
def preview_interpolation(source_date_from="", source_date_to="", max_source_rows=0, preview_limit=30):
	frappe.only_for(("HR Manager", "System Manager"))
	doc = _get_settings_doc()
	if not doc.enabled:
		frappe.throw(_("Attendance Interpolation is disabled in settings."))

	config = _build_runtime_config(
		doc,
		dry_run=True,
		source_date_from=source_date_from,
		source_date_to=source_date_to,
		max_source_rows=max_source_rows,
		preview_limit=preview_limit,
	)
	return run_sync_with_runtime_config(config, site_override=config["site"])


@frappe.whitelist()
def import_interpolation(source_date_from="", source_date_to="", max_source_rows=0, preview_limit=30, confirmed=0):
	frappe.only_for(("HR Manager", "System Manager"))
	if not _to_bool(confirmed):
		frappe.throw(_("Import confirmation is required."))

	doc = _get_settings_doc()
	if not doc.enabled:
		frappe.throw(_("Attendance Interpolation is disabled in settings."))

	config = _build_runtime_config(
		doc,
		dry_run=False,
		source_date_from=source_date_from,
		source_date_to=source_date_to,
		max_source_rows=max_source_rows,
		preview_limit=preview_limit,
	)
	return run_sync_with_runtime_config(config, site_override=config["site"])


@frappe.whitelist()
def enqueue_preview_interpolation(source_date_from="", source_date_to="", max_source_rows=0, preview_limit=30):
	frappe.only_for(("HR Manager", "System Manager"))
	doc = _get_settings_doc()
	if not doc.enabled:
		frappe.throw(_("Attendance Interpolation is disabled in settings."))

	config = _build_runtime_config(
		doc,
		dry_run=True,
		source_date_from=source_date_from,
		source_date_to=source_date_to,
		max_source_rows=max_source_rows,
		preview_limit=preview_limit,
	)
	return _enqueue_interpolation_job(config=config, action="preview")


@frappe.whitelist()
def enqueue_import_interpolation(
	source_date_from="",
	source_date_to="",
	max_source_rows=0,
	preview_limit=30,
	confirmed=0,
):
	frappe.only_for(("HR Manager", "System Manager"))
	if not _to_bool(confirmed):
		frappe.throw(_("Import confirmation is required."))

	doc = _get_settings_doc()
	if not doc.enabled:
		frappe.throw(_("Attendance Interpolation is disabled in settings."))

	config = _build_runtime_config(
		doc,
		dry_run=False,
		source_date_from=source_date_from,
		source_date_to=source_date_to,
		max_source_rows=max_source_rows,
		preview_limit=preview_limit,
	)
	return _enqueue_interpolation_job(config=config, action="import")


@frappe.whitelist()
def get_interpolation_job_status(job_token):
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
		"action": state.get("action"),
		"error": state.get("error") or "",
		"result": None,
	}
	if status == "finished":
		response["result"] = state.get("result") or {}
	elif status == "failed" and not response["error"]:
		response["error"] = _("Background job failed. Check RQ Job log for details.")
	return response
