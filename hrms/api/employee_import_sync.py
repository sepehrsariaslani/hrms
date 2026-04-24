import csv
import os
from datetime import timedelta

import frappe
import jdatetime
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import getdate, today

from hrms.utils.attendance_device_mapping import (
    append_employee_device_mapping,
    ensure_employee_device_mapping_setup,
    resolve_employee_by_attendance_device_id,
)

DEFAULT_CSV_PATH = (
    "/Users/sepehr/Downloads/frappe-bench/apps/hrms/hrms/api/Employee_Import_Master.csv"
)
DEFAULT_DAYS_TO_MARK_LEFT = 30
DEFAULT_COMPANY = None
AUTO_CREATE_BRANCHES = True

# Fill these only if you need explicit routing by branch code.
BRANCH_CODE_TO_BRANCH = {}
BRANCH_CODE_TO_COMPANY = {}

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

EMPLOYEE_CUSTOM_FIELDS = {
    "Employee": [
        {
            "fieldname": "custom_source_person_id",
            "label": "Source Person ID",
            "fieldtype": "Data",
            "insert_after": "attendance_device_id",
            "read_only": 1,
            "in_list_view": 1,
        },
        {
            "fieldname": "custom_membership_date_jalali",
            "label": "Membership Date Jalali",
            "fieldtype": "Data",
            "insert_after": "custom_source_person_id",
            "read_only": 1,
        },
        {
            "fieldname": "custom_membership_date_gregorian",
            "label": "Membership Date Gregorian",
            "fieldtype": "Date",
            "insert_after": "custom_membership_date_jalali",
            "read_only": 1,
        },
        {
            "fieldname": "custom_latest_attendance_date_jalali",
            "label": "Latest Attendance Date Jalali",
            "fieldtype": "Data",
            "insert_after": "custom_membership_date_gregorian",
            "read_only": 1,
        },
        {
            "fieldname": "custom_latest_attendance_date_gregorian",
            "label": "Latest Attendance Date Gregorian",
            "fieldtype": "Date",
            "insert_after": "custom_latest_attendance_date_jalali",
            "read_only": 1,
        },
        {
            "fieldname": "custom_attendance_source_databases",
            "label": "Attendance Source Databases",
            "fieldtype": "Small Text",
            "insert_after": "custom_latest_attendance_date_gregorian",
            "read_only": 1,
        },
        {
            "fieldname": "custom_branch_codes",
            "label": "Branch Codes",
            "fieldtype": "Small Text",
            "insert_after": "custom_attendance_source_databases",
            "read_only": 1,
        },
        {
            "fieldname": "custom_machine_nos",
            "label": "Machine Numbers",
            "fieldtype": "Small Text",
            "insert_after": "custom_branch_codes",
            "read_only": 1,
        },
        {
            "fieldname": "custom_employee_codes",
            "label": "Employee Codes",
            "fieldtype": "Small Text",
            "insert_after": "custom_machine_nos",
            "read_only": 1,
        },
        {
            "fieldname": "custom_device_map_detail",
            "label": "Device Map Detail",
            "fieldtype": "Long Text",
            "insert_after": "custom_employee_codes",
            "read_only": 1,
        },
        {
            "fieldname": "custom_total_attendance_records",
            "label": "Total Attendance Records",
            "fieldtype": "Int",
            "insert_after": "custom_device_map_detail",
            "read_only": 1,
        },
        {
            "fieldname": "custom_total_clock_punches",
            "label": "Total Clock Punches",
            "fieldtype": "Int",
            "insert_after": "custom_total_attendance_records",
            "read_only": 1,
        },
    ]
}


def normalize_text(value):
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return ""
    text = text.translate(PERSIAN_CHAR_MAP)
    return " ".join(text.split())


def normalize_code(value):
    text = normalize_text(value)
    if not text:
        return ""
    if text.endswith(".0"):
        maybe_int = text[:-2]
        if maybe_int.isdigit():
            return maybe_int
    return text


def split_codes(value):
    return [normalize_code(code) for code in str(value or "").split("|") if normalize_code(code)]


def build_attendance_device_entries(row):
    entries = []
    seen = set()

    def add_entry(code, device_hint=None, location=None):
        code = normalize_code(code)
        device_hint = normalize_code(device_hint)
        location = normalize_code(location)
        if not code:
            return
        key = (code, device_hint, location)
        if key in seen:
            return
        seen.add(key)
        entries.append(
            {
                "attendance_device_id": code,
                "device_id": device_hint,
                "location": location,
            }
        )

    primary_device_code = normalize_code(
        row.get("Attendance_Device_ID") or row.get("Primary_Employee_Code")
    )
    primary_machine = normalize_code(row.get("Machine_No") or row.get("Primary_Machine_No"))
    primary_branch = normalize_code(row.get("Primary_Branch_Code") or row.get("Branch"))
    add_entry(primary_device_code, primary_machine or primary_branch, location=primary_branch)

    employee_codes = split_codes(row.get("Employee_Codes"))
    machine_nos = split_codes(row.get("Machine_Nos"))
    branch_codes = split_codes(row.get("Branch_Codes"))
    for index, code in enumerate(employee_codes):
        machine_no = machine_nos[index] if index < len(machine_nos) else ""
        branch_code = branch_codes[index] if index < len(branch_codes) else ""
        add_entry(code, machine_no or branch_code, location=branch_code)

    return entries


def jalali_to_gregorian_iso(date_text):
    normalized = normalize_text(date_text)
    if not normalized:
        return None

    parts = normalized.split("/")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None

    year, month, day = [int(part) for part in parts]
    try:
        return jdatetime.date(year, month, day).togregorian().isoformat()
    except ValueError:
        return None


def parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def ensure_employee_custom_fields():
    create_custom_fields(EMPLOYEE_CUSTOM_FIELDS, update=True)
    ensure_employee_device_mapping_setup(hide_legacy_field=True)
    frappe.clear_cache(doctype="Employee")


def get_default_company():
    if DEFAULT_COMPANY:
        return DEFAULT_COMPANY

    companies = frappe.get_all("Company", pluck="name")
    if len(companies) == 1:
        return companies[0]

    user_default_company = frappe.defaults.get_user_default("Company")
    if user_default_company:
        return user_default_company

    return None


def resolve_branch_name(branch_code, auto_create_branches=False):
    branch_code = normalize_code(branch_code)
    if not branch_code:
        return None

    branch_name = BRANCH_CODE_TO_BRANCH.get(branch_code, branch_code)

    if frappe.db.exists("Branch", branch_name):
        return branch_name

    existing_branch = frappe.db.get_value("Branch", {"branch": branch_name}, "name")
    if existing_branch:
        return existing_branch

    if auto_create_branches:
        branch_doc = frappe.get_doc({"doctype": "Branch", "branch": branch_name})
        branch_doc.insert(ignore_permissions=True)
        return branch_doc.name

    return None


def resolve_company(row, existing_company=None, company_override=None):
    if company_override:
        return company_override
    branch_code = normalize_code(row.get("Primary_Branch_Code") or row.get("Branch"))
    if branch_code and branch_code in BRANCH_CODE_TO_COMPANY:
        return BRANCH_CODE_TO_COMPANY[branch_code]
    if existing_company:
        return existing_company
    return get_default_company()


def get_employee_by_source(row):
    person_id = normalize_code(row.get("Person_ID") or row.get("Employee_Number"))
    device_id = normalize_code(row.get("Attendance_Device_ID") or row.get("Primary_Employee_Code"))
    machine_hint = normalize_code(row.get("Machine_No") or row.get("Primary_Machine_No"))
    branch_hint = normalize_code(row.get("Primary_Branch_Code") or row.get("Branch"))

    if person_id:
        by_custom_person_id = frappe.db.get_value(
            "Employee", {"custom_source_person_id": person_id}, "name"
        )
        if by_custom_person_id:
            return frappe.get_doc("Employee", by_custom_person_id)

        by_employee_number = frappe.db.get_value("Employee", {"employee_number": person_id}, "name")
        if by_employee_number:
            return frappe.get_doc("Employee", by_employee_number)

    if device_id:
        by_table, _, _ = resolve_employee_by_attendance_device_id(
            device_id, device_id=machine_hint or branch_hint
        )
        if by_table:
            return frappe.get_doc("Employee", by_table)
        by_table_fallback, _, _ = resolve_employee_by_attendance_device_id(device_id)
        if by_table_fallback:
            return frappe.get_doc("Employee", by_table_fallback)

    employee_name = normalize_text(row.get("Employee_Name") or row.get("Full_Name"))
    if employee_name:
        by_name = frappe.db.get_value("Employee", {"employee_name": employee_name}, "name")
        if by_name:
            return frappe.get_doc("Employee", by_name)

    return None


def set_attendance_device_id(employee_doc, attendance_device_entries, messages, company_name=None):
    if not attendance_device_entries:
        return

    for entry in attendance_device_entries:
        device_code = normalize_code(entry.get("attendance_device_id"))
        device_hint = normalize_code(entry.get("device_id"))
        location_hint = normalize_code(entry.get("location"))
        if not device_code:
            continue

        existing_employee, _, conflicts = resolve_employee_by_attendance_device_id(
            device_code, device_id=device_hint
        )
        if conflicts:
            messages.append(
                f"attendance_device_id {device_code} with device {device_hint or '-'} is mapped to multiple employees: {', '.join(conflicts)}"
            )
            continue
        if existing_employee and existing_employee != employee_doc.name:
            messages.append(
                f"attendance_device_id {device_code} already belongs to {existing_employee}; skipped for {employee_doc.name}."
            )
            continue

        append_employee_device_mapping(
            employee_doc,
            device_code,
            device_hint,
            company=company_name,
            location=location_hint,
        )


def compute_status_and_relieving_date(latest_attendance_jalali, days_to_mark_left):
    latest_attendance_gregorian = jalali_to_gregorian_iso(latest_attendance_jalali)
    if not latest_attendance_gregorian:
        return "Active", None

    latest_date = getdate(latest_attendance_gregorian)
    today_date = getdate(today())
    if latest_date <= today_date - timedelta(days=days_to_mark_left):
        return "Left", latest_attendance_gregorian

    return "Active", None


def load_employee_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def build_employee_payload(
    row, employee_doc, auto_create_branches, days_to_mark_left, company_override=None
):
    person_id = normalize_code(row.get("Person_ID") or row.get("Employee_Number"))
    employee_name = normalize_text(row.get("Employee_Name") or row.get("Full_Name"))
    first_name = normalize_text(row.get("Import_First_Name"))
    last_name = normalize_text(row.get("Import_Last_Name"))
    date_of_joining_jalali = normalize_text(row.get("Date_Of_Joining") or row.get("Membership_Date"))
    latest_attendance_jalali = normalize_text(row.get("Latest_Attendance_Date"))
    date_of_joining_gregorian = jalali_to_gregorian_iso(date_of_joining_jalali)
    latest_attendance_gregorian = jalali_to_gregorian_iso(latest_attendance_jalali)
    attendance_device_entries = build_attendance_device_entries(row)
    branch_code = normalize_code(row.get("Primary_Branch_Code") or row.get("Branch"))
    branch_name = resolve_branch_name(branch_code, auto_create_branches=auto_create_branches)
    company_name = resolve_company(
        row,
        existing_company=getattr(employee_doc, "company", None),
        company_override=company_override,
    )
    status, relieving_date = compute_status_and_relieving_date(
        latest_attendance_jalali, days_to_mark_left
    )
    messages = []

    if date_of_joining_gregorian and employee_doc.get("date_of_birth"):
        if getdate(date_of_joining_gregorian) <= getdate(employee_doc.date_of_birth):
            messages.append(
                "date_of_joining was earlier than date_of_birth; kept it empty to avoid validation error."
            )
            date_of_joining_gregorian = None

    payload = {
        "employee_number": person_id,
        "first_name": first_name or employee_name,
        "last_name": last_name,
        "employee_name": employee_name or "Unknown Employee",
        "date_of_joining": date_of_joining_gregorian,
        "company": company_name,
        "branch": branch_name,
        "status": status,
        "relieving_date": relieving_date,
        "custom_source_person_id": person_id,
        "custom_membership_date_jalali": date_of_joining_jalali,
        "custom_membership_date_gregorian": date_of_joining_gregorian,
        "custom_latest_attendance_date_jalali": latest_attendance_jalali,
        "custom_latest_attendance_date_gregorian": latest_attendance_gregorian,
        "custom_attendance_source_databases": normalize_text(row.get("Attendance_Source_Databases")),
        "custom_branch_codes": normalize_text(row.get("Branch_Codes")),
        "custom_machine_nos": normalize_text(row.get("Machine_Nos")),
        "custom_employee_codes": normalize_text(row.get("Employee_Codes")),
        "custom_device_map_detail": normalize_text(row.get("Device_Map_Detail")),
        "custom_total_attendance_records": int(float(row.get("Total_Attendance_Records") or 0)),
        "custom_total_clock_punches": int(float(row.get("Total_Clock_Punches") or 0)),
    }

    return payload, attendance_device_entries, messages


def apply_payload(employee_doc, payload, attendance_device_entries, messages):
    for fieldname, value in payload.items():
        if value in (None, ""):
            if fieldname in {"relieving_date", "branch"} and employee_doc.get(fieldname):
                employee_doc.set(fieldname, None)
            elif fieldname == "status" and not employee_doc.get(fieldname):
                employee_doc.set(fieldname, "Active")
            continue
        employee_doc.set(fieldname, value)

    set_attendance_device_id(
        employee_doc,
        attendance_device_entries,
        messages,
        company_name=payload.get("company"),
    )

    if employee_doc.status != "Left":
        employee_doc.relieving_date = None


def get_or_create_employee_doc(row):
    employee_doc = get_employee_by_source(row)
    if employee_doc:
        return employee_doc, False

    employee_doc = frappe.new_doc("Employee")
    employee_doc.naming_series = "HR-EMP-"
    return employee_doc, True


def sync_employee_master(
    csv_path=DEFAULT_CSV_PATH,
    dry_run=1,
    auto_create_branches=1,
    days_to_mark_left=DEFAULT_DAYS_TO_MARK_LEFT,
    company=None,
):
    dry_run = parse_bool(dry_run)
    auto_create_branches = parse_bool(auto_create_branches)
    days_to_mark_left = int(days_to_mark_left)

    if not os.path.exists(csv_path):
        frappe.throw(f"CSV file not found: {csv_path}")

    ensure_employee_custom_fields()
    rows = load_employee_rows(csv_path)

    created = 0
    updated = 0
    left_count = 0
    skipped = 0
    results = []

    for index, row in enumerate(rows, start=1):
        messages = []
        try:
            employee_doc, is_new = get_or_create_employee_doc(row)
            payload, attendance_device_entries, payload_messages = build_employee_payload(
                row,
                employee_doc,
                auto_create_branches=auto_create_branches and not dry_run,
                days_to_mark_left=days_to_mark_left,
                company_override=company,
            )
            messages.extend(payload_messages)

            if not payload.get("company") and is_new and not employee_doc.get("company"):
                skipped += 1
                results.append(
                    {
                        "row": index,
                        "employee_number": normalize_code(row.get("Employee_Number")),
                        "employee_name": normalize_text(row.get("Employee_Name")),
                        "action": "skipped",
                        "messages": ["Company could not be resolved for this employee."],
                    }
                )
                continue

            apply_payload(employee_doc, payload, attendance_device_entries, messages)
            employee_doc.flags.ignore_permissions = True
            employee_doc.flags.ignore_mandatory = True

            if not dry_run:
                if is_new:
                    employee_doc.insert(ignore_permissions=True, ignore_mandatory=True)
                    created += 1
                else:
                    employee_doc.save(ignore_permissions=True)
                    updated += 1
            else:
                if is_new:
                    created += 1
                else:
                    updated += 1

            if employee_doc.status == "Left":
                left_count += 1

            results.append(
                {
                    "row": index,
                    "employee_number": payload.get("employee_number"),
                    "employee_name": payload.get("employee_name"),
                    "employee": getattr(employee_doc, "name", None),
                    "action": "create" if is_new else "update",
                    "status": employee_doc.status,
                    "relieving_date": employee_doc.relieving_date,
                    "messages": messages,
                }
            )
        except Exception as exc:
            skipped += 1
            results.append(
                {
                    "row": index,
                    "employee_number": normalize_code(row.get("Employee_Number")),
                    "employee_name": normalize_text(row.get("Employee_Name")),
                    "action": "error",
                    "messages": [str(exc)],
                }
            )

    if not dry_run:
        frappe.db.commit()

    return {
        "dry_run": dry_run,
        "csv_path": csv_path,
        "created": created,
        "updated": updated,
        "left_marked": left_count,
        "skipped": skipped,
        "sample_results": results[:25],
    }


@frappe.whitelist()
def dry_run_employee_master_sync(csv_path=DEFAULT_CSV_PATH):
    return sync_employee_master(csv_path=csv_path, dry_run=1)


@frappe.whitelist()
def apply_employee_master_sync(csv_path=DEFAULT_CSV_PATH):
    return sync_employee_master(csv_path=csv_path, dry_run=0)
