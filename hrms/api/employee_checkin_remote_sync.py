import argparse
import importlib
import json
import os
import shlex
import shutil
import socket
import subprocess
import time

import frappe
from frappe.utils import get_datetime
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.utils.attendance_device_mapping import append_employee_device_mapping

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(CURRENT_DIR, "employee_checkin_remote.local.json")
_EXPORTER_MODULE = None
CHECKIN_SOURCE_KEY_FIELD = "custom_source_log_key"

EMPLOYEE_CHECKIN_CUSTOM_FIELDS = {
    "Employee Checkin": [
        {
            "fieldname": CHECKIN_SOURCE_KEY_FIELD,
            "label": "Attendance Source Key",
            "fieldtype": "Data",
            "insert_after": "device_id",
            "read_only": 1,
            "in_list_view": 0,
        }
    ]
}


def parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def parse_int(value, default_value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default_value


def _get_exporter():
    global _EXPORTER_MODULE
    if _EXPORTER_MODULE:
        return _EXPORTER_MODULE

    try:
        _EXPORTER_MODULE = importlib.import_module("hrms.api.employee_checkin_export")
    except ModuleNotFoundError as exc:
        missing = exc.name or "dependency"
        frappe.throw(
            f"Missing Python dependency '{missing}'. Install required packages first (for example: jdatetime, python-tds)."
        )

    return _EXPORTER_MODULE


def normalize_text(value):
    return _get_exporter().normalize_text(value)


def normalize_code(value):
    return _get_exporter().normalize_code(value)


def load_config(config_path):
    with open(config_path, encoding="utf-8") as config_file:
        config = json.load(config_file)

    if not isinstance(config, dict):
        frappe.throw("Remote sync config must be a JSON object.")

    config.setdefault("enabled", 1)
    config.setdefault("site", "dehati.ir")
    config.setdefault("connection_mode", "vpn_direct_sql")
    config.setdefault("dry_run", 0)
    config.setdefault("batch_size", 1000)
    config.setdefault("skip_missing_employees", 1)
    config.setdefault("dedupe_on", "employee+time+log_type")
    config.setdefault("source_date_from", "")
    config.setdefault("source_date_to", "")
    config.setdefault("max_source_rows", 0)
    config.setdefault("preview_limit", 20)
    config.setdefault("vpn", {})
    config.setdefault("ssh_tunnel", {})
    config.setdefault("sql", {})
    return config


def ensure_connected_site(site):
    exporter = _get_exporter()
    active_site = getattr(frappe.local, "site", None)
    if active_site:
        if site and site != active_site:
            frappe.throw(f"Connected site is '{active_site}', but config site is '{site}'.")
        return False

    if not site:
        frappe.throw("No active site found. Set `site` in config or pass `--site`.")

    frappe.init(site=site, sites_path=exporter.SITES_PATH)
    frappe.connect()
    return True


def check_port_open(host, port, timeout_seconds=2):
    try:
        with socket.create_connection((host, int(port)), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def parse_target_host_port(target):
    text = str(target or "").strip()
    if not text:
        return None
    if ":" in text:
        host, port = text.rsplit(":", 1)
        return host.strip(), parse_int(port, 443)
    return text, 443


def parse_targets(targets):
    if isinstance(targets, list):
        return [str(target).strip() for target in targets if str(target).strip()]

    text = str(targets or "").strip()
    if not text:
        return []

    items = []
    for row in text.splitlines():
        for part in row.split(","):
            part = part.strip()
            if part:
                items.append(part)
    return items


def ensure_checkin_source_key_field():
    try:
        create_custom_fields(EMPLOYEE_CHECKIN_CUSTOM_FIELDS, update=True)
    except Exception:
        # Keep sync operational even if custom field provisioning fails.
        pass


def split_full_name(full_name):
    parts = [part for part in normalize_text(full_name).split(" ") if part]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def get_default_company(config):
    configured = normalize_text(config.get("default_employee_company"))
    if configured:
        return configured

    user_default = normalize_text(frappe.defaults.get_user_default("Company"))
    if user_default:
        return user_default

    companies = frappe.get_all("Company", pluck="name", limit_page_length=2)
    if len(companies) == 1:
        return normalize_text(companies[0])
    return ""


def build_source_log_key(log_row, source_log_type):
    exporter = _get_exporter()
    database_name = normalize_text(log_row.get("Source_Database"))
    punch_date = exporter.normalize_jalali_date(log_row.get("Punch_Date"), database_name)
    parts = [
        database_name,
        normalize_text(log_row.get("Source_Table")),
        normalize_code(log_row.get("Person_ID")),
        normalize_code(log_row.get("Employee_Code")),
        normalize_code(log_row.get("Branch_Code")),
        normalize_code(log_row.get("Machine_No")),
        normalize_text(punch_date),
        normalize_text(log_row.get("Punch_Time")),
        normalize_text(source_log_type),
        normalize_code(log_row.get("Record_No")),
    ]
    return "|".join(parts)


def _load_deleted_manual_blocks(mode):
    mode_text = str(mode or "employee+time+log_type").strip().lower()
    blocked_source_keys = set()
    blocked_dedupe_keys = set()
    deleted_rows = frappe.get_all(
        "Deleted Document",
        fields=["data"],
        filters={"deleted_doctype": "Employee Checkin", "restored": 0},
        order_by="creation desc",
        limit_page_length=50000,
    )

    for row in deleted_rows:
        payload = row.get("data")
        if not payload:
            continue
        try:
            deleted_doc = json.loads(payload)
        except Exception:
            continue

        if not isinstance(deleted_doc, dict):
            continue

        source_key = normalize_text(deleted_doc.get(CHECKIN_SOURCE_KEY_FIELD))
        if source_key:
            blocked_source_keys.add(source_key)

        employee = normalize_text(deleted_doc.get("employee"))
        timestamp_value = deleted_doc.get("time")
        log_type = normalize_text(deleted_doc.get("log_type"))
        if not employee or not timestamp_value:
            continue
        timestamp = str(get_datetime(timestamp_value))
        if mode_text == "employee+time":
            blocked_dedupe_keys.add((employee, timestamp))
        else:
            blocked_dedupe_keys.add((employee, timestamp, log_type))

    return blocked_source_keys, blocked_dedupe_keys


def build_auto_created_employee(log_row, timestamp, company_name):
    source_person_id = normalize_code(log_row.get("Person_ID"))
    source_employee_code = normalize_code(log_row.get("Employee_Code"))
    source_full_name = normalize_text(log_row.get("Full_Name"))
    first_name, last_name = split_full_name(source_full_name)
    employee_name = source_full_name or f"Employee {source_person_id or source_employee_code or 'Unknown'}"

    doc = frappe.new_doc("Employee")
    doc.naming_series = "HR-EMP-"
    doc.employee_name = employee_name
    doc.first_name = first_name or employee_name
    if last_name:
        doc.last_name = last_name
    if company_name:
        doc.company = company_name
    if timestamp:
        try:
            doc.date_of_joining = str(get_datetime(timestamp).date())
        except Exception:
            pass
    if source_person_id:
        doc.employee_number = source_person_id
    elif source_employee_code:
        doc.employee_number = source_employee_code
    if doc.meta.has_field("custom_source_person_id") and source_person_id:
        doc.custom_source_person_id = source_person_id
    if doc.meta.has_field("attendance_device_id") and source_employee_code:
        doc.attendance_device_id = source_employee_code
    return doc


def _append_new_employee_to_indexes(employee_doc, by_person_id, by_device_code, by_name):
    source_person_id = normalize_code(employee_doc.get("custom_source_person_id"))
    employee_number = normalize_code(employee_doc.get("employee_number"))
    attendance_device_id = normalize_code(employee_doc.get("attendance_device_id"))
    employee_name = normalize_text(employee_doc.get("employee_name"))
    if source_person_id:
        by_person_id[source_person_id] = employee_doc
    if employee_number:
        by_person_id[employee_number] = employee_doc
    if attendance_device_id:
        by_device_code[attendance_device_id].append(employee_doc)
    if employee_name:
        by_name[employee_name].append(employee_doc)


def create_missing_employee_for_log(log_row, timestamp, company_name, by_person_id, by_device_code, by_name):
    employee_doc = build_auto_created_employee(log_row, timestamp, company_name)
    employee_doc.flags.ignore_permissions = True
    employee_doc.flags.ignore_mandatory = True
    employee_doc.insert(ignore_permissions=True, ignore_mandatory=True)
    source_employee_code = normalize_code(log_row.get("Employee_Code"))
    device_hint = normalize_code(log_row.get("Machine_No")) or normalize_code(log_row.get("Branch_Code"))
    append_employee_device_mapping(
        employee_doc,
        source_employee_code,
        device_id=device_hint,
        company=employee_doc.get("company"),
        location=normalize_code(log_row.get("Branch_Code")),
    )
    employee_doc.save(ignore_permissions=True)
    _append_new_employee_to_indexes(employee_doc, by_person_id, by_device_code, by_name)
    return employee_doc


def wait_for_port(host, port, wait_seconds, poll_seconds):
    deadline = time.time() + max(1, int(wait_seconds))
    poll = max(1, int(poll_seconds))
    while time.time() < deadline:
        if check_port_open(host, port):
            return
        time.sleep(poll)
    frappe.throw(f"Target did not open {host}:{port} within {wait_seconds} seconds.")


def wait_for_targets(targets, wait_seconds, poll_seconds):
    parsed_targets = [parse_target_host_port(t) for t in parse_targets(targets)]
    parsed_targets = [t for t in parsed_targets if t]
    if not parsed_targets:
        return

    deadline = time.time() + max(1, int(wait_seconds))
    poll = max(1, int(poll_seconds))

    while time.time() < deadline:
        unresolved = []
        for host, port in parsed_targets:
            if not check_port_open(host, port):
                unresolved.append(f"{host}:{port}")

        if not unresolved:
            return

        time.sleep(poll)

    frappe.throw("Targets are unreachable: " + ", ".join(unresolved))


def _process_output(process):
    stdout_text = ""
    stderr_text = ""
    if process.stdout:
        stdout_text = (process.stdout.read() or "").strip()
    if process.stderr:
        stderr_text = (process.stderr.read() or "").strip()
    return stdout_text, stderr_text


def _strip_sudo_prefix(parts):
    if not parts:
        return parts
    if os.path.basename(parts[0]) != "sudo":
        return parts

    index = 1
    while index < len(parts) and parts[index].startswith("-"):
        index += 1
    return parts[index:]


def start_openfortivpn(vpn_config):
    gateway_host = str(vpn_config.get("gateway_host") or "").strip()
    gateway_port = parse_int(vpn_config.get("gateway_port"), 443)
    username = str(vpn_config.get("username") or "").strip()
    password = str(vpn_config.get("password") or "").strip()

    if not gateway_host or not username or not password:
        frappe.throw("VPN settings are incomplete (gateway_host, username, password are required).")

    command_text = str(vpn_config.get("vpn_command") or "openfortivpn").strip() or "openfortivpn"
    cmd = shlex.split(command_text)
    if not cmd:
        cmd = ["openfortivpn"]
    if os.path.basename(cmd[0]) == "sudo" and shutil.which(cmd[0]) is None:
        cmd = _strip_sudo_prefix(cmd)
    if not cmd:
        cmd = ["openfortivpn"]
    if shutil.which(cmd[0]) is None:
        frappe.throw(
            f"VPN command executable '{cmd[0]}' was not found. Set VPN Command to a valid executable such as 'openfortivpn'."
        )

    cmd.extend(
        [
            f"{gateway_host}:{gateway_port}",
            "--username",
            username,
        ]
    )

    help_cmd = [cmd[0], "--help"]
    help_result = subprocess.run(
        help_cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    supports_password_stdin = "--passwd-on-stdin" in (help_result.stdout or "")
    if supports_password_stdin:
        cmd.append("--passwd-on-stdin")
    else:
        cmd.extend(["-p", password])

    realm = str(vpn_config.get("realm") or "").strip()
    if realm:
        cmd.extend(["--realm", realm])

    trusted_cert = str(vpn_config.get("trusted_cert") or "").strip()
    if trusted_cert:
        cmd.extend(["--trusted-cert", trusted_cert])

    if parse_bool(vpn_config.get("insecure_ssl")):
        cmd.append("--insecure-ssl")

    if parse_bool(vpn_config.get("disable_default_route", 1)):
        if not any(str(part).startswith("--set-routes") for part in cmd):
            cmd.append("--set-routes=0")

    extra_args = str(vpn_config.get("extra_args") or "").strip()
    if extra_args:
        cmd.extend(shlex.split(extra_args))

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if supports_password_stdin and process.stdin:
        process.stdin.write(password + "\n")
        process.stdin.flush()
        process.stdin.close()

    wait_seconds = parse_int(vpn_config.get("connect_timeout_seconds"), 40)
    poll_seconds = parse_int(vpn_config.get("poll_seconds"), 1)
    for _ in range(max(1, wait_seconds)):
        if process.poll() is not None:
            stdout_text, stderr_text = _process_output(process)
            details = stderr_text or stdout_text or "no output"
            frappe.throw(f"openfortivpn exited early: {details}")
        time.sleep(max(1, poll_seconds))

    target_hosts = []
    for target in parse_targets(vpn_config.get("targets")):
        parsed_target = parse_target_host_port(target)
        if parsed_target:
            target_hosts.append(parsed_target[0])

    for target_host in target_hosts:
        route_commands = [
            ["sudo", "-n", "ip", "route", "replace", f"{target_host}/32", "dev", "ppp0"],
            ["ip", "route", "replace", f"{target_host}/32", "dev", "ppp0"],
        ]
        for route_cmd in route_commands:
            result = subprocess.run(route_cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                break

    wait_for_targets(
        vpn_config.get("targets"),
        parse_int(vpn_config.get("ready_wait_seconds"), 90),
        parse_int(vpn_config.get("poll_seconds"), 2),
    )

    return process, "VPN connected."


def build_ssh_tunnel_command(tunnel_config):
    gateway_host = str(tunnel_config.get("gateway_host") or "").strip()
    gateway_user = str(tunnel_config.get("gateway_user") or "").strip()
    if not gateway_host or not gateway_user:
        frappe.throw("`gateway_host` and `gateway_user` are required in ssh_tunnel config.")

    gateway_port = parse_int(tunnel_config.get("gateway_port"), 22)
    local_bind_host = str(tunnel_config.get("local_bind_host") or "127.0.0.1").strip()
    local_bind_port = parse_int(tunnel_config.get("local_bind_port"), 11433)
    remote_sql_host = str(tunnel_config.get("remote_sql_host") or "").strip()
    remote_sql_port = parse_int(tunnel_config.get("remote_sql_port"), 1433)
    if not remote_sql_host:
        frappe.throw("`remote_sql_host` is required in ssh_tunnel config.")

    strict_host_key_checking = "yes"
    if not parse_bool(tunnel_config.get("strict_host_key_checking", 1)):
        strict_host_key_checking = "no"

    base_parts = [
        "ssh",
        "-N",
        "-p",
        str(gateway_port),
        "-L",
        f"{local_bind_host}:{local_bind_port}:{remote_sql_host}:{remote_sql_port}",
        "-o",
        f"StrictHostKeyChecking={strict_host_key_checking}",
        "-o",
        "ExitOnForwardFailure=yes",
        "-o",
        "ServerAliveInterval=30",
        "-o",
        "ServerAliveCountMax=3",
    ]

    private_key_path = str(tunnel_config.get("gateway_private_key") or "").strip()
    password = str(tunnel_config.get("gateway_password") or "").strip()
    if private_key_path:
        base_parts.extend(["-i", private_key_path])
    if not parse_bool(tunnel_config.get("strict_host_key_checking", 1)):
        base_parts.extend(["-o", "UserKnownHostsFile=/dev/null"])

    base_parts.append(f"{gateway_user}@{gateway_host}")
    ssh_command = " ".join(shlex.quote(part) for part in base_parts)

    if password:
        sshpass_command = str(tunnel_config.get("sshpass_command") or "sshpass").strip() or "sshpass"
        return f"{shlex.quote(sshpass_command)} -p {shlex.quote(password)} {ssh_command}"

    return ssh_command


def start_ssh_tunnel(tunnel_config):
    local_bind_host = str(tunnel_config.get("local_bind_host") or "127.0.0.1").strip()
    local_bind_port = parse_int(tunnel_config.get("local_bind_port"), 11433)

    if check_port_open(local_bind_host, local_bind_port):
        return None, "Using existing open local tunnel port."

    command = build_ssh_tunnel_command(tunnel_config)
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    wait_seconds = parse_int(tunnel_config.get("connect_timeout_seconds"), 30)
    poll_seconds = parse_int(tunnel_config.get("poll_seconds"), 1)

    for _ in range(max(1, wait_seconds)):
        if process.poll() is not None:
            stdout_text, stderr_text = _process_output(process)
            details = stderr_text or stdout_text or "no output"
            frappe.throw(f"SSH tunnel process exited early: {details}")

        if check_port_open(local_bind_host, local_bind_port):
            return process, "SSH tunnel established."

        time.sleep(max(1, poll_seconds))

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    frappe.throw(f"SSH tunnel did not bind local port {local_bind_host}:{local_bind_port}.")


def stop_process(process):
    if not process:
        return ""
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        return "Background process killed."
    return "Background process stopped."


def configure_exporter(sql_config, tunnel_config):
    exporter = _get_exporter()
    exporter.SQL_SERVER = str(sql_config.get("host") or tunnel_config.get("local_bind_host") or "127.0.0.1").strip()
    exporter.SQL_PORT = parse_int(sql_config.get("port") or tunnel_config.get("local_bind_port"), 11433)
    exporter.SQL_DATABASE = str(sql_config.get("database") or "EOS").strip()
    exporter.SQL_USER = str(sql_config.get("user") or "").strip()
    exporter.SQL_PASSWORD = str(sql_config.get("password") or "").strip()


def load_existing_keys(mode):
    rows = frappe.get_all(
        "Employee Checkin",
        fields=["employee", "time", "log_type"],
        limit_page_length=1000000,
    )
    keys = set()
    mode_text = str(mode or "employee+time+log_type").strip().lower()
    for row in rows:
        employee = normalize_text(row.get("employee"))
        timestamp = str(get_datetime(row.get("time")))
        log_type = normalize_text(row.get("log_type"))
        if mode_text == "employee+time":
            keys.add((employee, timestamp))
        else:
            keys.add((employee, timestamp, log_type))
    return keys


def load_existing_source_keys():
    if not frappe.get_meta("Employee Checkin").has_field(CHECKIN_SOURCE_KEY_FIELD):
        return set()

    rows = frappe.get_all(
        "Employee Checkin",
        fields=[CHECKIN_SOURCE_KEY_FIELD],
        filters=[[CHECKIN_SOURCE_KEY_FIELD, "!=", ""]],
        limit_page_length=1000000,
    )
    return {normalize_text(row.get(CHECKIN_SOURCE_KEY_FIELD)) for row in rows if row.get(CHECKIN_SOURCE_KEY_FIELD)}


def make_key(mode, employee, timestamp, log_type):
    mode_text = str(mode or "employee+time+log_type").strip().lower()
    if mode_text == "employee+time":
        return (employee, timestamp)
    return (employee, timestamp, log_type)


def _normalize_filter_date(date_text):
    if not str(date_text or "").strip():
        return ""
    return _get_exporter().normalize_jalali_date(date_text)


def _filter_source_logs(source_logs, config):
    exporter = _get_exporter()
    date_from = _normalize_filter_date(config.get("source_date_from"))
    date_to = _normalize_filter_date(config.get("source_date_to"))
    max_rows = max(0, parse_int(config.get("max_source_rows"), 0))

    filtered = []
    for row in source_logs:
        punch_date = exporter.normalize_jalali_date(row.get("Punch_Date"), row.get("Source_Database"))
        if date_from and punch_date and punch_date < date_from:
            continue
        if date_to and punch_date and punch_date > date_to:
            continue
        filtered.append(row)
        if max_rows and len(filtered) >= max_rows:
            break
    return filtered


def fetch_source_logs_with_runtime_config(runtime_config, site_override=""):
    exporter = _get_exporter()
    config = dict(runtime_config or {})
    if not parse_bool(config.get("enabled", 1)):
        return {"enabled": False, "message": "Remote sync is disabled in config.", "source_logs": []}

    configured_site = str(site_override or config.get("site") or "").strip()
    connected_here = ensure_connected_site(configured_site)
    connection_mode = str(config.get("connection_mode") or "vpn_direct_sql").strip().lower()

    vpn_process = None
    tunnel_process = None
    connection_message = ""

    try:
        vpn_config = config.get("vpn") or {}
        tunnel_config = config.get("ssh_tunnel") or {}
        sql_config = config.get("sql") or {}

        if connection_mode == "ssh_tunnel":
            tunnel_process, connection_message = start_ssh_tunnel(tunnel_config)
            wait_for_port(
                str(tunnel_config.get("local_bind_host") or "127.0.0.1").strip(),
                parse_int(tunnel_config.get("local_bind_port"), 11433),
                parse_int(tunnel_config.get("ready_wait_seconds"), 10),
                parse_int(tunnel_config.get("poll_seconds"), 1),
            )
        elif connection_mode == "vpn_direct_sql":
            vpn_process, connection_message = start_openfortivpn(vpn_config)
        else:
            connection_message = "Direct SQL mode (no connection bootstrap)."

        configure_exporter(sql_config, tunnel_config)
        source_logs, source_databases, live_sql_used = exporter.fetch_complete_source_logs()
        source_fetch_error = normalize_text(
            getattr(exporter, "get_last_source_fetch_error", lambda: "")()
        )
        source_logs = _filter_source_logs(source_logs, config)

        if not live_sql_used and source_fetch_error:
            connection_message = f"{connection_message} Fallback used because live SQL failed: {source_fetch_error}".strip()

        return {
            "enabled": True,
            "site": getattr(frappe.local, "site", configured_site),
            "connection_mode": connection_mode,
            "connection_message": connection_message,
            "live_sql_used": live_sql_used,
            "source_fetch_error": source_fetch_error,
            "source_databases": source_databases,
            "source_log_count": len(source_logs),
            "source_date_from": _normalize_filter_date(config.get("source_date_from")),
            "source_date_to": _normalize_filter_date(config.get("source_date_to")),
            "source_logs": source_logs,
        }
    finally:
        stop_process(tunnel_process)
        stop_process(vpn_process)
        if connected_here:
            frappe.destroy()


def run_sync_with_runtime_config(runtime_config, site_override=""):
    exporter = _get_exporter()
    config = dict(runtime_config or {})
    if not parse_bool(config.get("enabled", 1)):
        return {"enabled": False, "message": "Remote sync is disabled in config."}

    configured_site = str(site_override or config.get("site") or "").strip()
    connected_here = ensure_connected_site(configured_site)
    connection_mode = str(config.get("connection_mode") or "vpn_direct_sql").strip().lower()

    vpn_process = None
    tunnel_process = None
    connection_message = ""

    try:
        vpn_config = config.get("vpn") or {}
        tunnel_config = config.get("ssh_tunnel") or {}
        sql_config = config.get("sql") or {}

        if connection_mode == "ssh_tunnel":
            tunnel_process, connection_message = start_ssh_tunnel(tunnel_config)
            wait_for_port(
                str(tunnel_config.get("local_bind_host") or "127.0.0.1").strip(),
                parse_int(tunnel_config.get("local_bind_port"), 11433),
                parse_int(tunnel_config.get("ready_wait_seconds"), 10),
                parse_int(tunnel_config.get("poll_seconds"), 1),
            )
        elif connection_mode == "vpn_direct_sql":
            vpn_process, connection_message = start_openfortivpn(vpn_config)
        else:
            connection_message = "Direct SQL mode (no connection bootstrap)."

        ensure_checkin_source_key_field()
        configure_exporter(sql_config, tunnel_config)
        by_person_id, by_device_code, by_name = exporter.load_employee_index()
        source_logs, source_databases, live_sql_used = exporter.fetch_complete_source_logs()
        source_fetch_error = normalize_text(
            getattr(exporter, "get_last_source_fetch_error", lambda: "")()
        )
        source_logs = _filter_source_logs(source_logs, config)

        existing_keys = load_existing_keys(config.get("dedupe_on"))
        existing_source_keys = load_existing_source_keys()
        dry_run = parse_bool(config.get("dry_run", 0))
        skip_missing_employees = parse_bool(config.get("skip_missing_employees", 1))
        auto_create_missing_employees = parse_bool(config.get("auto_create_missing_employees", 1))
        preserve_manual_changes = parse_bool(config.get("preserve_manual_changes", 1))
        batch_size = max(1, parse_int(config.get("batch_size"), 1000))
        preview_limit = max(1, parse_int(config.get("preview_limit"), 20))
        default_company = get_default_company(config)

        created = 0
        skipped_existing = 0
        skipped_missing_employee = 0
        skipped_invalid_datetime = 0
        skipped_manual_changes = 0
        auto_created_employees = 0
        errors = 0
        sample_results = []
        preview_rows = []

        seen_keys_in_run = set()
        all_known_keys = set(existing_keys)
        blocked_source_keys = set()
        blocked_dedupe_keys = set()
        if preserve_manual_changes:
            blocked_source_keys, blocked_dedupe_keys = _load_deleted_manual_blocks(config.get("dedupe_on"))

        for index, log_row in enumerate(source_logs, start=1):
            try:
                source_database = normalize_text(log_row.get("Source_Database"))
                source_date = exporter.normalize_jalali_date(
                    log_row.get("Punch_Date"),
                    source_database,
                )
                source_time = normalize_text(log_row.get("Punch_Time"))
                source_person_id = normalize_code(log_row.get("Person_ID"))
                source_employee_code = normalize_code(log_row.get("Employee_Code"))
                source_full_name = normalize_text(log_row.get("Full_Name"))
                source_table = normalize_text(log_row.get("Source_Table"))
                source_log_type = normalize_text(log_row.get("Source_Log_Type")) or "IN"
                source_log_key = build_source_log_key(log_row, source_log_type)

                employee_doc, match_rule = exporter.choose_employee_for_log(
                    log_row, by_person_id, by_device_code, by_name
                )
                if not employee_doc:
                    if auto_create_missing_employees:
                        timestamp_for_joining = exporter.jalali_to_gregorian_datetime(
                            log_row.get("Punch_Date"),
                            log_row.get("Punch_Time"),
                            log_row.get("Source_Database"),
                        )
                        if dry_run:
                            auto_employee_name = normalize_text(
                                f"AUTO-{source_person_id or source_employee_code or index}"
                            )
                            employee_doc = {
                                "name": auto_employee_name,
                                "employee_name": source_full_name or auto_employee_name,
                                "employee_number": source_person_id or source_employee_code,
                                "custom_source_person_id": source_person_id,
                                "attendance_device_id": source_employee_code,
                            }
                            _append_new_employee_to_indexes(employee_doc, by_person_id, by_device_code, by_name)
                            match_rule = "auto_created_employee_dry_run"
                            auto_created_employees += 1
                        else:
                            employee_doc = create_missing_employee_for_log(
                                log_row=log_row,
                                timestamp=timestamp_for_joining,
                                company_name=default_company,
                                by_person_id=by_person_id,
                                by_device_code=by_device_code,
                                by_name=by_name,
                            )
                            match_rule = "auto_created_employee"
                            auto_created_employees += 1

                    if not employee_doc:
                        if skip_missing_employees:
                            skipped_missing_employee += 1
                            if len(preview_rows) < preview_limit:
                                preview_rows.append(
                                    {
                                        "row": index,
                                        "status": "missing_employee",
                                        "match_rule": "",
                                        "employee": "",
                                        "employee_name": "",
                                        "source_person_id": source_person_id,
                                        "source_employee_code": source_employee_code,
                                        "source_full_name": source_full_name,
                                        "source_database": source_database,
                                        "source_table": source_table,
                                        "source_date": source_date,
                                        "source_time": source_time,
                                        "time": "",
                                        "log_type": source_log_type,
                                        "device_id": "",
                                    }
                                )
                            continue
                        frappe.throw("Employee mapping not found for source row.")

                timestamp = exporter.jalali_to_gregorian_datetime(
                    log_row.get("Punch_Date"),
                    log_row.get("Punch_Time"),
                    log_row.get("Source_Database"),
                )
                if not timestamp:
                    skipped_invalid_datetime += 1
                    if len(preview_rows) < preview_limit:
                        preview_rows.append(
                            {
                                "row": index,
                                "status": "invalid_datetime",
                                "match_rule": match_rule,
                                "employee": normalize_text(employee_doc.get("name")),
                                "employee_name": normalize_text(employee_doc.get("employee_name")),
                                "source_person_id": source_person_id,
                                "source_employee_code": source_employee_code,
                                "source_full_name": source_full_name,
                                "source_database": source_database,
                                "source_table": source_table,
                                "source_date": source_date,
                                "source_time": source_time,
                                "time": "",
                                "log_type": source_log_type,
                                "device_id": "",
                            }
                        )
                    continue

                log_type = source_log_type
                employee = normalize_text(employee_doc.get("name"))
                employee_name = normalize_text(employee_doc.get("employee_name"))

                machine_no = normalize_code(log_row.get("Machine_No"))
                branch_code = normalize_code(log_row.get("Branch_Code"))
                if machine_no or branch_code:
                    device_id = f"machine:{machine_no}|branch:{branch_code}"
                else:
                    device_id = f"db:{normalize_text(log_row.get('Source_Database'))}"

                dedupe_key = make_key(config.get("dedupe_on"), employee, timestamp, log_type)
                if preserve_manual_changes and (
                    source_log_key in blocked_source_keys or dedupe_key in blocked_dedupe_keys
                ):
                    skipped_manual_changes += 1
                    if len(preview_rows) < preview_limit:
                        preview_rows.append(
                            {
                                "row": index,
                                "status": "skipped_manual_override",
                                "match_rule": match_rule,
                                "employee": employee,
                                "employee_name": employee_name,
                                "source_person_id": source_person_id,
                                "source_employee_code": source_employee_code,
                                "source_full_name": source_full_name,
                                "source_database": source_database,
                                "source_table": source_table,
                                "source_date": source_date,
                                "source_time": source_time,
                                "time": timestamp,
                                "log_type": log_type,
                                "device_id": device_id,
                            }
                        )
                    continue

                if source_log_key and source_log_key in existing_source_keys:
                    skipped_existing += 1
                    if len(preview_rows) < preview_limit:
                        preview_rows.append(
                            {
                                "row": index,
                                "status": "existing",
                                "match_rule": match_rule,
                                "employee": employee,
                                "employee_name": employee_name,
                                "source_person_id": source_person_id,
                                "source_employee_code": source_employee_code,
                                "source_full_name": source_full_name,
                                "source_database": source_database,
                                "source_table": source_table,
                                "source_date": source_date,
                                "source_time": source_time,
                                "time": timestamp,
                                "log_type": log_type,
                                "device_id": device_id,
                            }
                        )
                    continue

                if dedupe_key in all_known_keys or dedupe_key in seen_keys_in_run:
                    skipped_existing += 1
                    if len(preview_rows) < preview_limit:
                        preview_rows.append(
                            {
                                "row": index,
                                "status": "existing",
                                "match_rule": match_rule,
                                "employee": employee,
                                "employee_name": employee_name,
                                "source_person_id": source_person_id,
                                "source_employee_code": source_employee_code,
                                "source_full_name": source_full_name,
                                "source_database": source_database,
                                "source_table": source_table,
                                "source_date": source_date,
                                "source_time": source_time,
                                "time": timestamp,
                                "log_type": log_type,
                                "device_id": device_id,
                            }
                        )
                    continue

                if not dry_run:
                    doc = frappe.new_doc("Employee Checkin")
                    doc.employee = employee
                    doc.employee_name = employee_name
                    doc.time = timestamp
                    doc.log_type = log_type
                    doc.device_id = device_id
                    if doc.meta.has_field(CHECKIN_SOURCE_KEY_FIELD):
                        doc.set(CHECKIN_SOURCE_KEY_FIELD, source_log_key)
                    doc.skip_auto_attendance = 0
                    doc.flags.ignore_permissions = True
                    doc.insert()
                    if created > 0 and created % batch_size == 0:
                        frappe.db.commit()

                created += 1
                seen_keys_in_run.add(dedupe_key)
                all_known_keys.add(dedupe_key)
                if source_log_key:
                    existing_source_keys.add(source_log_key)

                if len(preview_rows) < preview_limit:
                    preview_rows.append(
                        {
                            "row": index,
                            "status": "new" if not dry_run else "would_create",
                            "match_rule": match_rule,
                            "employee": employee,
                            "employee_name": employee_name,
                            "source_person_id": source_person_id,
                            "source_employee_code": source_employee_code,
                            "source_full_name": source_full_name,
                            "source_table": source_table,
                            "time": timestamp,
                            "log_type": log_type,
                            "source_database": source_database,
                            "source_date": source_date,
                            "source_time": source_time,
                            "device_id": device_id,
                        }
                    )
            except Exception as exc:
                errors += 1
                if len(preview_rows) < preview_limit:
                    preview_rows.append(
                        {
                            "row": index,
                            "status": "error",
                            "match_rule": "",
                            "employee": "",
                            "employee_name": "",
                            "source_person_id": "",
                            "source_employee_code": "",
                            "source_full_name": "",
                            "source_database": normalize_text(log_row.get("Source_Database")),
                            "source_table": normalize_text(log_row.get("Source_Table")),
                            "source_date": exporter.normalize_jalali_date(
                                log_row.get("Punch_Date"),
                                log_row.get("Source_Database"),
                            ),
                            "source_time": normalize_text(log_row.get("Punch_Time")),
                            "time": "",
                            "log_type": normalize_text(log_row.get("Source_Log_Type")) or "IN",
                            "device_id": "",
                            "error": str(exc),
                        }
                    )

        sample_results = list(preview_rows)

        if not dry_run:
            frappe.db.commit()

        return {
            "enabled": True,
            "site": getattr(frappe.local, "site", configured_site),
            "connection_mode": connection_mode,
            "connection_message": connection_message,
            "live_sql_used": live_sql_used,
            "source_fetch_error": source_fetch_error,
            "source_databases": source_databases,
            "source_log_count": len(source_logs),
            "source_date_from": _normalize_filter_date(config.get("source_date_from")),
            "source_date_to": _normalize_filter_date(config.get("source_date_to")),
            "created": created,
            "skipped_existing": skipped_existing,
            "skipped_missing_employee": skipped_missing_employee,
            "skipped_invalid_datetime": skipped_invalid_datetime,
            "skipped_manual_changes": skipped_manual_changes,
            "auto_created_employees": auto_created_employees,
            "errors": errors,
            "dry_run": dry_run,
            "sample_results": sample_results,
            "preview_rows": preview_rows,
        }
    finally:
        stop_process(tunnel_process)
        stop_process(vpn_process)
        if connected_here:
            frappe.destroy()


def _run_direct_sync(config_path, site_override=""):
    if not os.path.exists(config_path):
        frappe.throw(f"Config file not found: {config_path}")

    config = load_config(config_path)
    result = run_sync_with_runtime_config(config, site_override=site_override)
    result["config_path"] = config_path
    return result


@frappe.whitelist()
def sync_employee_checkins_direct(config_path=DEFAULT_CONFIG_PATH, site=""):
    return _run_direct_sync(config_path=config_path, site_override=site)


def main():
    parser = argparse.ArgumentParser(description="Direct sync Employee Checkins from remote SQL.")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to remote sync JSON config.")
    parser.add_argument("--site", default="", help="Frappe site name override.")
    args = parser.parse_args()

    result = _run_direct_sync(config_path=args.config, site_override=args.site)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
