import csv
import json
import os
import socket
import subprocess
import time
from collections import defaultdict

import frappe
from frappe.utils import get_datetime

DEFAULT_CSV_PATH = (
    "/Users/sepehr/Downloads/frappe-bench/apps/hrms/hrms/api/Employee_Checkin_Import.csv"
)
DEFAULT_MISSING_CSV_PATH = (
    "/Users/sepehr/Downloads/frappe-bench/apps/hrms/hrms/api/Employee_Checkin_Missing_Employees.csv"
)
DEFAULT_VPN_CONFIG_PATH = (
    "/Users/sepehr/Downloads/frappe-bench/apps/hrms/hrms/api/employee_checkin_vpn.local.json"
)

PERSIAN_CHAR_MAP = str.maketrans(
    {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ة": "ه",
        "ۀ": "ه",
        "ؤ": "و",
        "\u200c": " ",
        "\u200f": "",
        "\u200e": "",
    }
)


def parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_int(value, default_value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default_value


def run_shell_command(command, timeout_seconds):
    if not str(command or "").strip():
        frappe.throw("VPN command is empty in VPN config.")

    completed = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=max(1, int(timeout_seconds)),
    )
    if completed.returncode != 0:
        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()
        details = stderr or stdout or "No output"
        frappe.throw(f"VPN command failed: {details}")


def parse_target_host_port(target):
    text = str(target or "").strip()
    if not text:
        return None
    if ":" in text:
        host, port = text.rsplit(":", 1)
        host = host.strip()
        if not host:
            return None
        return host, parse_int(port, 443)
    return text, 443


def can_connect_target(host, port):
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except OSError:
        return False


def wait_for_targets(targets, max_wait_seconds, poll_interval_seconds):
    if not targets:
        return

    deadline = time.time() + max(1, int(max_wait_seconds))
    interval = max(1, int(poll_interval_seconds))

    while time.time() < deadline:
        unresolved_targets = []
        for target in targets:
            host_port = parse_target_host_port(target)
            if not host_port:
                continue
            host, port = host_port
            if not can_connect_target(host, port):
                unresolved_targets.append(f"{host}:{port}")
        if not unresolved_targets:
            return
        time.sleep(interval)

    frappe.throw(
        "VPN connected but targets are still unreachable: " + ", ".join(unresolved_targets)
    )


def load_vpn_config(vpn_config_path):
    with open(vpn_config_path, encoding="utf-8") as config_file:
        config = json.load(config_file)

    if not isinstance(config, dict):
        frappe.throw("VPN config must be a JSON object.")

    config.setdefault("enabled", 1)
    config.setdefault("connect_timeout_seconds", 60)
    config.setdefault("disconnect_timeout_seconds", 30)
    config.setdefault("wait_after_connect_seconds", 0)
    config.setdefault("reachability_wait_seconds", 90)
    config.setdefault("reachability_poll_seconds", 3)
    config.setdefault("targets", [])
    return config


def connect_vpn(vpn_config_path):
    if not os.path.exists(vpn_config_path):
        frappe.throw(f"VPN config file not found: {vpn_config_path}")

    config = load_vpn_config(vpn_config_path)
    if not parse_bool(config.get("enabled")):
        return {
            "vpn_enabled": False,
            "vpn_connected": False,
            "vpn_config_path": vpn_config_path,
            "vpn_message": "VPN config is disabled.",
            "disconnect_command": "",
        }

    connect_command = str(config.get("connect_command") or "").strip()
    disconnect_command = str(config.get("disconnect_command") or "").strip()
    disconnect_timeout_seconds = parse_int(config.get("disconnect_timeout_seconds"), 30)
    run_shell_command(connect_command, parse_int(config.get("connect_timeout_seconds"), 60))
    connected = True
    try:
        wait_after_connect = parse_int(config.get("wait_after_connect_seconds"), 0)
        if wait_after_connect > 0:
            time.sleep(wait_after_connect)

        wait_for_targets(
            config.get("targets") or [],
            parse_int(config.get("reachability_wait_seconds"), 90),
            parse_int(config.get("reachability_poll_seconds"), 3),
        )
    except Exception:
        if connected and disconnect_command:
            try:
                run_shell_command(disconnect_command, disconnect_timeout_seconds)
            except Exception:
                pass
        raise

    return {
        "vpn_enabled": True,
        "vpn_connected": True,
        "vpn_config_path": vpn_config_path,
        "vpn_message": "VPN connected successfully.",
        "disconnect_command": disconnect_command,
        "disconnect_timeout_seconds": disconnect_timeout_seconds,
    }


def disconnect_vpn(vpn_state):
    disconnect_command = str((vpn_state or {}).get("disconnect_command") or "").strip()
    if not disconnect_command:
        return ""
    try:
        run_shell_command(
            disconnect_command,
            parse_int((vpn_state or {}).get("disconnect_timeout_seconds"), 30),
        )
        return "VPN disconnected."
    except Exception as exc:
        return f"VPN disconnect failed: {exc}"


def read_csv_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv_rows(csv_path, rows, fieldnames):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def normalize_text(value):
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return ""
    text = text.translate(PERSIAN_CHAR_MAP)
    return " ".join(text.split())


def load_employee_resolver():
    fields = ["name", "employee_name", "employee_number"]
    if frappe.get_meta("Employee").has_field("custom_source_person_id"):
        fields.append("custom_source_person_id")
    employees = frappe.get_all("Employee", fields=fields, limit_page_length=1000000)
    by_name = {}
    by_number = {}
    by_source_person_id = {}
    by_employee_name = defaultdict(list)

    for employee in employees:
        name = normalize_text(employee.get("name"))
        employee_number = normalize_text(employee.get("employee_number"))
        source_person_id = normalize_text(employee.get("custom_source_person_id"))
        employee_name = normalize_text(employee.get("employee_name"))
        by_name[name] = employee
        if employee_number:
            by_number[employee_number] = employee
        if source_person_id:
            by_source_person_id[source_person_id] = employee
        if employee_name:
            by_employee_name[employee_name].append(employee)

    return by_name, by_number, by_source_person_id, by_employee_name


def load_existing_checkins():
    existing_rows = frappe.get_all(
        "Employee Checkin",
        fields=["employee", "time", "log_type"],
        limit_page_length=1000000,
    )
    existing_keys = set()
    for row in existing_rows:
        existing_keys.add(
            (
                normalize_text(row.get("employee")),
                str(get_datetime(row.get("time"))),
                normalize_text(row.get("log_type")),
            )
        )
    return existing_keys


def resolve_employee(row, by_name, by_number, by_source_person_id, by_employee_name):
    employee_value = normalize_text(row.get("employee"))
    if employee_value in by_name:
        return by_name[employee_value]
    if employee_value in by_number:
        return by_number[employee_value]
    if employee_value in by_source_person_id:
        return by_source_person_id[employee_value]
    employee_name_value = normalize_text(row.get("employee_name"))
    if employee_name_value and len(by_employee_name.get(employee_name_value, [])) == 1:
        return by_employee_name[employee_name_value][0]
    return None


def build_checkin_doc(row, employee):
    if not employee:
        frappe.throw(
            "Employee not found for identifier: "
            f"{normalize_text(row.get('employee'))} / {normalize_text(row.get('employee_name'))}"
        )

    employee_name = normalize_text(employee.get("employee_name")) or normalize_text(row.get("employee_name"))
    timestamp = str(get_datetime(row.get("time")))
    log_type = normalize_text(row.get("log_type"))
    device_id = normalize_text(row.get("device_id"))
    skip_auto_attendance = 1 if parse_bool(row.get("skip_auto_attendance")) else 0

    doc = frappe.new_doc("Employee Checkin")
    doc.employee = employee.get("name")
    doc.employee_name = employee_name
    doc.time = timestamp
    doc.log_type = log_type
    doc.device_id = device_id
    doc.skip_auto_attendance = skip_auto_attendance
    doc.flags.ignore_permissions = True
    return doc, (doc.employee, timestamp, log_type)


@frappe.whitelist()
def import_employee_checkins(
    csv_path=DEFAULT_CSV_PATH,
    dry_run=1,
    batch_size=1000,
    skip_missing_employees=1,
    missing_csv_path=DEFAULT_MISSING_CSV_PATH,
    manage_vpn=0,
    vpn_config_path=DEFAULT_VPN_CONFIG_PATH,
):
    dry_run = parse_bool(dry_run)
    batch_size = int(batch_size)
    skip_missing_employees = parse_bool(skip_missing_employees)
    manage_vpn = parse_bool(manage_vpn)
    vpn_state = {
        "vpn_enabled": False,
        "vpn_connected": False,
        "vpn_config_path": vpn_config_path,
        "vpn_message": "VPN management not requested.",
        "disconnect_command": "",
    }
    result_payload = None

    if manage_vpn:
        vpn_state = connect_vpn(vpn_config_path)

    disconnect_status = ""
    try:
        if not os.path.exists(csv_path):
            frappe.throw(f"CSV file not found: {csv_path}")

        rows = read_csv_rows(csv_path)
        by_name, by_number, by_source_person_id, by_employee_name = load_employee_resolver()
        existing_keys = load_existing_checkins()

        created = 0
        skipped_existing = 0
        skipped_missing_employee = 0
        errors = 0
        results = []
        error_samples = []
        missing_rows = []

        for index, row in enumerate(rows, start=1):
            try:
                employee = resolve_employee(
                    row,
                    by_name,
                    by_number,
                    by_source_person_id,
                    by_employee_name,
                )
                if not employee:
                    missing_row = {
                        "row": index,
                        "employee": normalize_text(row.get("employee")),
                        "employee_name": normalize_text(row.get("employee_name")),
                        "time": normalize_text(row.get("time")),
                        "log_type": normalize_text(row.get("log_type")),
                        "device_id": normalize_text(row.get("device_id")),
                        "reason": "Employee not found in ERPNext",
                    }
                    missing_rows.append(missing_row)
                    if skip_missing_employees:
                        skipped_missing_employee += 1
                        if len(results) < 25:
                            results.append({**missing_row, "action": "skipped_missing_employee"})
                        continue
                    build_checkin_doc(row, employee)

                doc, checkin_key = build_checkin_doc(row, employee)

                if checkin_key in existing_keys:
                    skipped_existing += 1
                    if len(results) < 25:
                        results.append(
                            {
                                "row": index,
                                "employee": doc.employee,
                                "time": doc.time,
                                "log_type": doc.log_type,
                                "action": "skipped_existing",
                            }
                        )
                    continue

                if not dry_run:
                    doc.db_insert()
                    if created > 0 and created % batch_size == 0:
                        frappe.db.commit()

                existing_keys.add(checkin_key)
                created += 1

                if len(results) < 25:
                    results.append(
                        {
                            "row": index,
                            "employee": doc.employee,
                            "time": doc.time,
                            "log_type": doc.log_type,
                            "action": "create" if not dry_run else "would_create",
                        }
                    )
            except Exception as exc:
                errors += 1
                error_row = {
                    "row": index,
                    "employee": normalize_text(row.get("employee")),
                    "time": normalize_text(row.get("time")),
                    "log_type": normalize_text(row.get("log_type")),
                    "action": "error",
                    "error": str(exc),
                }
                if len(results) < 25:
                    results.append(error_row)
                if len(error_samples) < 25:
                    error_samples.append(error_row)

        if not dry_run:
            frappe.db.commit()

        if missing_csv_path:
            write_csv_rows(
                missing_csv_path,
                missing_rows,
                ["row", "employee", "employee_name", "time", "log_type", "device_id", "reason"],
            )

        result_payload = {
            "dry_run": dry_run,
            "csv_path": csv_path,
            "total_rows": len(rows),
            "created": created,
            "skipped_existing": skipped_existing,
            "skipped_missing_employee": skipped_missing_employee,
            "errors": errors,
            "missing_csv_path": missing_csv_path,
            "sample_results": results,
            "sample_errors": error_samples,
            "vpn_enabled": vpn_state.get("vpn_enabled"),
            "vpn_connected": vpn_state.get("vpn_connected"),
            "vpn_config_path": vpn_state.get("vpn_config_path"),
            "vpn_message": vpn_state.get("vpn_message"),
            "vpn_disconnect_status": disconnect_status,
        }
    finally:
        if manage_vpn and vpn_state.get("vpn_connected"):
            disconnect_status = disconnect_vpn(vpn_state)
            if result_payload is not None:
                result_payload["vpn_disconnect_status"] = disconnect_status

    return result_payload
