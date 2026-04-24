import argparse
import csv
import json
import os
import sys
from collections import defaultdict

import jdatetime
import pytds

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def find_bench_path(start_dir):
    current_dir = os.path.abspath(start_dir)
    while current_dir and current_dir != os.path.dirname(current_dir):
        if os.path.isdir(os.path.join(current_dir, "sites")) and os.path.isdir(
            os.path.join(current_dir, "apps")
        ):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    return os.path.abspath(os.path.join(start_dir, "..", "..", "..", ".."))


BENCH_PATH = find_bench_path(CURRENT_DIR)
SITES_PATH = os.path.join(BENCH_PATH, "sites")
LOGS_PATH = os.path.join(BENCH_PATH, "logs")

# Make direct `python employee_checkin_export.py` execution behave like bench context.
os.makedirs(LOGS_PATH, exist_ok=True)
os.chdir(BENCH_PATH)
if BENCH_PATH not in sys.path:
    sys.path.insert(0, BENCH_PATH)
if os.path.join(BENCH_PATH, "apps") not in sys.path:
    sys.path.insert(0, os.path.join(BENCH_PATH, "apps"))

import frappe
from hrms.utils.attendance_device_mapping import get_employee_mapping_rows

SQL_SERVER = "192.168.150.26"
SQL_DATABASE = "EOS"
SQL_USER = "winkart"
SQL_PASSWORD = "sa@123"
SQL_PORT = 1433
LOCAL_CLOCKDMP_FALLBACK_CSV = "/Users/sepehr/Downloads/frappe-bench/EOS_ClockDmp_Pretty.csv"

OUTPUT_DIR = "/Users/sepehr/Downloads/frappe-bench/apps/hrms/hrms/api"
EMPLOYEE_MASTER_CSV = os.path.join(OUTPUT_DIR, "Employee_Import_Master.csv")
CHECKIN_IMPORT_CSV = os.path.join(OUTPUT_DIR, "Employee_Checkin_Import.csv")
CHECKIN_SOURCE_CSV = os.path.join(OUTPUT_DIR, "Employee_Checkin_Source_All.csv")
CHECKIN_UNMAPPED_CSV = os.path.join(OUTPUT_DIR, "Employee_Checkin_Unmapped.csv")
ATTENDANCE_SUMMARY_CSV = os.path.join(OUTPUT_DIR, "Employee_Attendance_Daily_Summary.csv")
SOURCE_DATABASE_SUMMARY_CSV = os.path.join(OUTPUT_DIR, "Employee_Checkin_Source_Database_Summary.csv")

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


def write_csv(rows, csv_path, fieldnames):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def quote_sql_name(name):
    return f"[{str(name).replace(']', ']]')}]"


def get_database_year(database_name):
    database_text = normalize_text(database_name)
    if database_text.startswith("EOS_"):
        year_text = database_text.split("_", 1)[1]
        if year_text.isdigit():
            return year_text
    return ""


def normalize_jalali_date(date_value, database_name=""):
    date_text = normalize_text(date_value)
    if not date_text:
        return ""

    parts = [part.strip() for part in date_text.split("/") if part.strip()]
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        return f"{parts[0].zfill(4)}/{parts[1].zfill(2)}/{parts[2].zfill(2)}"

    if len(parts) == 2 and all(part.isdigit() for part in parts):
        db_year = get_database_year(database_name)
        if db_year:
            return f"{db_year}/{parts[0].zfill(2)}/{parts[1].zfill(2)}"

    return date_text


def jalali_to_gregorian_datetime(date_text, time_text, database_name=""):
    normalized_date = normalize_jalali_date(date_text, database_name)
    normalized_time = normalize_text(time_text)
    if not normalized_date or not normalized_time:
        return ""

    date_parts = normalized_date.split("/")
    time_parts = normalized_time.split(":")
    if len(date_parts) != 3 or len(time_parts) < 2:
        return ""

    try:
        year, month, day = [int(part) for part in date_parts]
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2]) if len(time_parts) > 2 else 0
        return str(
            jdatetime.datetime(year, month, day, hour, minute, second).togregorian().replace(
                microsecond=0
            )
        )
    except ValueError:
        return ""


def get_sql_connection():
    return pytds.connect(
        server=SQL_SERVER,
        database=SQL_DATABASE,
        user=SQL_USER,
        password=SQL_PASSWORD,
        port=SQL_PORT,
    )


def fetch_rows(connection, query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description] if cursor.description else []
    return [dict(zip(columns, row)) for row in rows]


def fetch_eos_databases(connection):
    query = """
    SELECT name
    FROM master.sys.databases
    WHERE name = %s OR name LIKE %s
    ORDER BY name
    """
    rows = fetch_rows(connection, query, ["EOS", "EOS[_]%"])
    return [normalize_text(row.get("name")) for row in rows if normalize_text(row.get("name"))]


def get_table_columns(connection, database_name, table_name):
    query = f"""
    SELECT COLUMN_NAME
    FROM {quote_sql_name(database_name)}.INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = %s
    ORDER BY ORDINAL_POSITION
    """
    rows = fetch_rows(connection, query, [table_name])
    return [normalize_text(row.get("COLUMN_NAME")).upper() for row in rows]


def table_exists(connection, database_name, table_name):
    query = f"""
    SELECT 1 AS present
    FROM {quote_sql_name(database_name)}.INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = %s
    """
    return bool(fetch_rows(connection, query, [table_name]))


def build_optional_select(columns_upper, alias, candidate_columns):
    selected_column = next((column for column in candidate_columns if column.upper() in columns_upper), None)
    if selected_column:
        return f"CAST(i.{quote_sql_name(selected_column)} AS VARCHAR(50)) AS [{alias}]"
    return f"CAST('' AS VARCHAR(50)) AS [{alias}]"


def fetch_person_name_map(connection, person_database_name="EOS"):
    query = f"""
    SELECT
        CAST(p.PERNO AS VARCHAR(50)) AS [Person_ID],
        LTRIM(RTRIM(
            ISNULL(LTRIM(RTRIM(p.FIRSTNAME)), '') +
            CASE
                WHEN ISNULL(LTRIM(RTRIM(p.LASTNAME)), '') = '' THEN ''
                ELSE ' ' + LTRIM(RTRIM(p.LASTNAME))
            END
        )) AS [Full_Name]
    FROM {quote_sql_name(person_database_name)}.dbo.Person p
    """
    rows = fetch_rows(connection, query)
    return {
        normalize_code(row.get("Person_ID")): normalize_text(row.get("Full_Name"))
        for row in rows
        if normalize_code(row.get("Person_ID"))
    }


def fetch_clockdmp_index_from_sql(connection):
    if not table_exists(connection, "EOS", "ClockDmp"):
        return {}

    query = """
    SELECT
        CAST(c.PERNO AS VARCHAR(50)) AS [Person_ID],
        CAST(c.KARTNO AS VARCHAR(50)) AS [Employee_Code],
        CAST(c.ComCode AS VARCHAR(50)) AS [Branch_Code],
        CAST(c.MASHINNO AS VARCHAR(50)) AS [Machine_No],
        CAST(c.CLOCKDATE AS VARCHAR(50)) AS [Punch_Date],
        CAST(c.CLOCKTIME AS VARCHAR(50)) AS [Punch_Time],
        CAST(c.REC AS VARCHAR(50)) AS [Record_No]
    FROM EOS.dbo.ClockDmp c
    WHERE NULLIF(LTRIM(RTRIM(CAST(c.CLOCKDATE AS VARCHAR(50)))), '') IS NOT NULL
      AND NULLIF(LTRIM(RTRIM(CAST(c.CLOCKTIME AS VARCHAR(50)))), '') IS NOT NULL
    """
    index = {}
    for row in fetch_rows(connection, query):
        key = (
            normalize_code(row.get("Person_ID")),
            normalize_jalali_date(row.get("Punch_Date"), "EOS"),
            normalize_text(row.get("Punch_Time")),
        )
        if not all(key):
            continue
        index[key] = {
            "Employee_Code": normalize_code(row.get("Employee_Code")),
            "Branch_Code": normalize_code(row.get("Branch_Code")),
            "Machine_No": normalize_code(row.get("Machine_No")),
            "Record_No": normalize_code(row.get("Record_No")),
        }
    return index


def fetch_clockdmp_index_from_csv():
    if not os.path.exists(LOCAL_CLOCKDMP_FALLBACK_CSV):
        return {}

    index = {}
    with open(LOCAL_CLOCKDMP_FALLBACK_CSV, newline="", encoding="utf-8-sig") as csv_file:
        for row in csv.DictReader(csv_file):
            key = (
                normalize_code(row.get("Person_ID")),
                normalize_jalali_date(row.get("Clock_Date"), "EOS"),
                normalize_text(row.get("Clock_Time")),
            )
            if not all(key):
                continue
            index[key] = {
                "Employee_Code": normalize_code(row.get("Card_No")),
                "Branch_Code": normalize_code(row.get("Company_Code")),
                "Machine_No": normalize_code(row.get("Machine_No")),
                "Record_No": normalize_code(row.get("Record_No")),
            }
    return index


def fetch_clockdmp_index(connection=None):
    if connection is not None:
        try:
            return fetch_clockdmp_index_from_sql(connection)
        except Exception:
            pass
    return fetch_clockdmp_index_from_csv()


def fetch_ioinfo_logs(connection, database_name, person_name_map):
    columns_upper = get_table_columns(connection, database_name, "IOInfo")
    quoted_database_name = quote_sql_name(database_name)

    select_parts = [
        "CAST(i.PERNO AS VARCHAR(50)) AS [Person_ID]",
        "CAST(i.BEGINDATE AS VARCHAR(50)) AS [Begin_Date]",
        "CAST(i.BEGINTIME AS VARCHAR(50)) AS [Begin_Time]",
        "CAST(i.ENDDATE AS VARCHAR(50)) AS [End_Date]",
        "CAST(i.ENDTIME AS VARCHAR(50)) AS [End_Time]",
        build_optional_select(columns_upper, "Begin_Employee_Code", ["BEGINKARTNO", "KARTNO", "CARDNO", "CARD_NO"]),
        build_optional_select(columns_upper, "End_Employee_Code", ["ENDKARTNO", "KARTNO", "CARDNO", "CARD_NO"]),
        build_optional_select(columns_upper, "Begin_Branch_Code", ["BEGINCOMCODE", "COMCODE", "COMPANY_CODE", "BRANCH_CODE"]),
        build_optional_select(columns_upper, "End_Branch_Code", ["ENDCOMCODE", "COMCODE", "COMPANY_CODE", "BRANCH_CODE"]),
        build_optional_select(columns_upper, "Begin_Machine_No", ["BEGINMASHINNO", "MASHINNO", "MACHINE_NO", "MACHINENO"]),
        build_optional_select(columns_upper, "End_Machine_No", ["ENDMASHINNO", "MASHINNO", "MACHINE_NO", "MACHINENO"]),
    ]

    query = f"""
    SELECT
        {", ".join(select_parts)}
    FROM {quoted_database_name}.dbo.IOInfo i
    WHERE i.PERNO IS NOT NULL
      AND (
        NULLIF(LTRIM(RTRIM(CAST(i.BEGINDATE AS VARCHAR(50)))), '') IS NOT NULL
        OR NULLIF(LTRIM(RTRIM(CAST(i.ENDDATE AS VARCHAR(50)))), '') IS NOT NULL
      )
    """

    source_rows = []
    for row in fetch_rows(connection, query):
        person_id = normalize_code(row.get("Person_ID"))
        full_name = person_name_map.get(person_id, "")

        log_specs = [
            (
                "IN",
                row.get("Begin_Date"),
                row.get("Begin_Time"),
                row.get("Begin_Employee_Code"),
                row.get("Begin_Branch_Code"),
                row.get("Begin_Machine_No"),
            ),
            (
                "OUT",
                row.get("End_Date"),
                row.get("End_Time"),
                row.get("End_Employee_Code"),
                row.get("End_Branch_Code"),
                row.get("End_Machine_No"),
            ),
        ]

        for log_type, punch_date, punch_time, employee_code, branch_code, machine_no in log_specs:
            normalized_date = normalize_jalali_date(punch_date, database_name)
            normalized_time = normalize_text(punch_time)
            if not normalized_date or not normalized_time:
                continue

            source_rows.append(
                {
                    "Source_Table": "IOInfo",
                    "Source_Database": database_name,
                    "Person_ID": person_id,
                    "Full_Name": full_name,
                    "Employee_Code": normalize_code(employee_code),
                    "Branch_Code": normalize_code(branch_code),
                    "Machine_No": normalize_code(machine_no),
                    "Punch_Date": normalized_date,
                    "Punch_Time": normalized_time,
                    "Raw_IO_Type": log_type,
                    "Source_Log_Type": log_type,
                    "Record_No": "",
                }
            )

    return source_rows


def fetch_complete_source_logs():
    connection = None
    try:
        connection = get_sql_connection()
        eos_databases = fetch_eos_databases(connection)
        ioinfo_databases = [
            database_name
            for database_name in eos_databases
            if database_name.startswith("EOS_") and table_exists(connection, database_name, "IOInfo")
        ]
        person_name_map = fetch_person_name_map(connection, "EOS")
        clockdmp_index = fetch_clockdmp_index(connection)

        source_rows = []
        for database_name in sorted(ioinfo_databases):
            source_rows.extend(fetch_ioinfo_logs(connection, database_name, person_name_map))

        for row in source_rows:
            enrichment = clockdmp_index.get(
                (
                    normalize_code(row.get("Person_ID")),
                    normalize_jalali_date(row.get("Punch_Date"), row.get("Source_Database")),
                    normalize_text(row.get("Punch_Time")),
                )
            )
            if enrichment:
                if not row.get("Employee_Code"):
                    row["Employee_Code"] = enrichment.get("Employee_Code", "")
                if not row.get("Branch_Code"):
                    row["Branch_Code"] = enrichment.get("Branch_Code", "")
                if not row.get("Machine_No"):
                    row["Machine_No"] = enrichment.get("Machine_No", "")
                if not row.get("Record_No"):
                    row["Record_No"] = enrichment.get("Record_No", "")

        return source_rows, sorted(ioinfo_databases), True
    except Exception:
        clockdmp_index = fetch_clockdmp_index_from_csv()
        fallback_rows = []
        for (person_id, punch_date, punch_time), enrichment in clockdmp_index.items():
            fallback_rows.append(
                {
                    "Source_Table": "ClockDmpFallbackCSV",
                    "Source_Database": "EOS",
                    "Person_ID": person_id,
                    "Full_Name": "",
                    "Employee_Code": enrichment.get("Employee_Code", ""),
                    "Branch_Code": enrichment.get("Branch_Code", ""),
                    "Machine_No": enrichment.get("Machine_No", ""),
                    "Punch_Date": punch_date,
                    "Punch_Time": punch_time,
                    "Raw_IO_Type": "",
                    "Source_Log_Type": "",
                    "Record_No": enrichment.get("Record_No", ""),
                }
            )
        return fallback_rows, ["EOS"], False
    finally:
        if connection is not None:
            connection.close()


def build_employee_index(employees, mapping_rows=None):
    by_person_id = {}
    by_device_code = defaultdict(list)
    by_name = defaultdict(list)
    mapping_by_employee = defaultdict(list)

    for row in mapping_rows or []:
        mapping_by_employee[row.get("parent")].append(
            {
                "attendance_device_id": normalize_code(row.get("attendance_device_id")),
                "device_id": normalize_code(row.get("device_id")),
            }
        )

    for employee in employees:
        employee_name = normalize_text(employee.get("employee_name"))
        employee_number = normalize_code(employee.get("employee_number"))
        source_person_id = normalize_code(employee.get("custom_source_person_id"))
        attendance_device_id = normalize_code(employee.get("attendance_device_id"))
        custom_employee_codes = normalize_text(employee.get("custom_employee_codes"))

        if employee_number:
            by_person_id[employee_number] = employee
        if source_person_id:
            by_person_id[source_person_id] = employee
        if attendance_device_id:
            by_device_code[attendance_device_id].append(employee)
        for mapping in mapping_by_employee.get(employee.get("name"), []):
            if mapping["attendance_device_id"]:
                by_device_code[mapping["attendance_device_id"]].append(employee)
        if custom_employee_codes:
            for code in [normalize_code(code) for code in custom_employee_codes.split("|")]:
                if code:
                    by_device_code[code].append(employee)
        if employee_name:
            by_name[employee_name].append(employee)

    return by_person_id, by_device_code, by_name


def load_employee_index():
    fields = [
        "name",
        "employee_name",
        "employee_number",
        "attendance_device_id",
        "custom_source_person_id",
        "custom_employee_codes",
    ]
    employees = frappe.get_all("Employee", fields=fields, limit_page_length=100000)
    mapping_rows = get_employee_mapping_rows()
    return build_employee_index(employees, mapping_rows=mapping_rows)


def load_employee_index_from_master_csv(csv_path=EMPLOYEE_MASTER_CSV):
    employees = []
    for row in read_csv_rows(csv_path):
        employees.append(
            {
                "name": normalize_text(row.get("Employee_Number")) or normalize_text(row.get("Person_ID")),
                "employee_name": normalize_text(row.get("Employee_Name") or row.get("Full_Name")),
                "employee_number": normalize_code(row.get("Employee_Number") or row.get("Person_ID")),
                "attendance_device_id": normalize_code(
                    row.get("Attendance_Device_ID") or row.get("Primary_Employee_Code")
                ),
                "custom_source_person_id": normalize_code(row.get("Person_ID") or row.get("Employee_Number")),
                "custom_employee_codes": normalize_text(row.get("Employee_Codes")),
            }
        )
    return build_employee_index(employees)


def choose_employee_for_log(log_row, by_person_id, by_device_code, by_name):
    person_id = normalize_code(log_row.get("Person_ID"))
    employee_code = normalize_code(log_row.get("Employee_Code"))
    full_name = normalize_text(log_row.get("Full_Name"))

    if person_id and person_id in by_person_id:
        return by_person_id[person_id], "person_id"

    if employee_code and employee_code in by_device_code:
        unique_matches = {}
        for employee in by_device_code[employee_code]:
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

        if full_name:
            name_matches = [
                employee
                for employee in matches
                if normalize_text(employee.get("employee_name")) == full_name
            ]
            if len(name_matches) == 1:
                return name_matches[0], "employee_code+name"

    if full_name and full_name in by_name and len(by_name[full_name]) == 1:
        return by_name[full_name][0], "full_name"

    return None, ""


def assign_fallback_log_types(mapped_rows):
    grouped_rows = defaultdict(list)
    for row in mapped_rows:
        if row["log_type"]:
            continue
        grouped_rows[(row["employee"], row["Punch_Date"])].append(row)

    for rows in grouped_rows.values():
        rows.sort(key=lambda item: (item["Gregorian_Time"], item["Record_No"]))
        for index, row in enumerate(rows):
            row["log_type"] = "IN" if index % 2 == 0 else "OUT"


def build_attendance_summary_rows(mapped_rows):
    grouped_rows = defaultdict(list)
    for row in mapped_rows:
        grouped_rows[(row["employee"], row["Punch_Date"])].append(row)

    summary_rows = []
    for (_, punch_date), rows in grouped_rows.items():
        rows.sort(key=lambda item: (item["Gregorian_Time"], item["Record_No"], item["log_type"]))
        employee_row = rows[0]
        in_logs = [row["Gregorian_Time"] for row in rows if row["log_type"] == "IN"]
        out_logs = [row["Gregorian_Time"] for row in rows if row["log_type"] == "OUT"]
        summary_rows.append(
            {
                "employee": employee_row["employee"],
                "employee_name": employee_row["employee_name"],
                "attendance_date_jalali": punch_date,
                "attendance_date_gregorian": rows[0]["Gregorian_Time"].split(" ")[0],
                "first_in": in_logs[0] if in_logs else "",
                "last_out": out_logs[-1] if out_logs else "",
                "punch_count": len(rows),
                "device_ids": " | ".join(sorted({row["device_id"] for row in rows if row["device_id"]})),
                "source_codes": " | ".join(
                    sorted({row["source_employee_code"] for row in rows if row["source_employee_code"]})
                ),
                "source_databases": " | ".join(
                    sorted({row["source_database"] for row in rows if row["source_database"]})
                ),
            }
        )
    return summary_rows


def build_source_database_summary_rows(source_rows):
    grouped_counts = defaultdict(int)
    for row in source_rows:
        grouped_counts[(row["Source_Database"], row["Source_Table"])] += 1

    summary_rows = []
    for (database_name, table_name), row_count in sorted(grouped_counts.items()):
        summary_rows.append(
            {
                "source_database": database_name,
                "source_table": table_name,
                "row_count": row_count,
            }
        )
    return summary_rows


def _export_employee_checkins_with_index(by_person_id, by_device_code, by_name):
    source_logs, source_databases, live_sql_used = fetch_complete_source_logs()

    source_rows = []
    mapped_rows = []
    unmapped_rows = []
    seen_import_keys = set()

    for log_row in source_logs:
        employee_doc, match_rule = choose_employee_for_log(log_row, by_person_id, by_device_code, by_name)
        gregorian_time = jalali_to_gregorian_datetime(
            log_row.get("Punch_Date"),
            log_row.get("Punch_Time"),
            log_row.get("Source_Database"),
        )
        source_row = {
            "Source_Table": normalize_text(log_row.get("Source_Table")),
            "Source_Database": normalize_text(log_row.get("Source_Database")),
            "Person_ID": normalize_code(log_row.get("Person_ID")),
            "Full_Name": normalize_text(log_row.get("Full_Name")),
            "Employee_Code": normalize_code(log_row.get("Employee_Code")),
            "Branch_Code": normalize_code(log_row.get("Branch_Code")),
            "Machine_No": normalize_code(log_row.get("Machine_No")),
            "Punch_Date": normalize_jalali_date(
                log_row.get("Punch_Date"),
                log_row.get("Source_Database"),
            ),
            "Punch_Time": normalize_text(log_row.get("Punch_Time")),
            "Gregorian_Time": gregorian_time,
            "Raw_IO_Type": normalize_text(log_row.get("Raw_IO_Type")),
            "Source_Log_Type": normalize_text(log_row.get("Source_Log_Type")),
            "Record_No": normalize_code(log_row.get("Record_No")),
            "Matched_Employee": employee_doc.get("name") if employee_doc else "",
            "Matched_Employee_Name": normalize_text(employee_doc.get("employee_name")) if employee_doc else "",
            "Match_Rule": match_rule,
        }
        source_rows.append(source_row)

        if not employee_doc or not gregorian_time:
            unmapped_row = dict(source_row)
            unmapped_row["Unmapped_Reason"] = (
                "No Employee match found" if not employee_doc else "Invalid Jalali datetime"
            )
            unmapped_rows.append(unmapped_row)
            continue

        mapped_rows.append(
            {
                "employee": employee_doc.get("name"),
                "employee_name": normalize_text(employee_doc.get("employee_name")),
                "time": gregorian_time,
                "log_type": normalize_text(source_row["Source_Log_Type"]),
                "device_id": (
                    f"machine:{source_row['Machine_No']}|branch:{source_row['Branch_Code']}"
                    if source_row["Machine_No"] or source_row["Branch_Code"]
                    else f"db:{source_row['Source_Database']}"
                ),
                "skip_auto_attendance": 0,
                "Punch_Date": source_row["Punch_Date"],
                "Record_No": source_row["Record_No"],
                "Gregorian_Time": gregorian_time,
                "source_employee_code": source_row["Employee_Code"],
                "source_person_id": source_row["Person_ID"],
                "source_database": source_row["Source_Database"],
                "source_table": source_row["Source_Table"],
            }
        )

    assign_fallback_log_types(mapped_rows)

    import_rows = []
    detailed_mapped_rows = []
    for row in mapped_rows:
        import_key = (row["employee"], row["time"], row["log_type"])
        if import_key in seen_import_keys:
            continue
        seen_import_keys.add(import_key)

        import_rows.append(
            {
                "employee": row["employee"],
                "employee_name": row["employee_name"],
                "time": row["time"],
                "log_type": row["log_type"],
                "device_id": row["device_id"],
                "skip_auto_attendance": row["skip_auto_attendance"],
            }
        )
        detailed_mapped_rows.append(row)

    attendance_summary_rows = build_attendance_summary_rows(detailed_mapped_rows)
    source_database_summary_rows = build_source_database_summary_rows(source_rows)

    write_csv(
        source_rows,
        CHECKIN_SOURCE_CSV,
        [
            "Source_Table",
            "Source_Database",
            "Person_ID",
            "Full_Name",
            "Employee_Code",
            "Branch_Code",
            "Machine_No",
            "Punch_Date",
            "Punch_Time",
            "Gregorian_Time",
            "Raw_IO_Type",
            "Source_Log_Type",
            "Record_No",
            "Matched_Employee",
            "Matched_Employee_Name",
            "Match_Rule",
        ],
    )
    write_csv(
        import_rows,
        CHECKIN_IMPORT_CSV,
        ["employee", "employee_name", "time", "log_type", "device_id", "skip_auto_attendance"],
    )
    write_csv(
        unmapped_rows,
        CHECKIN_UNMAPPED_CSV,
        [
            "Source_Table",
            "Source_Database",
            "Person_ID",
            "Full_Name",
            "Employee_Code",
            "Branch_Code",
            "Machine_No",
            "Punch_Date",
            "Punch_Time",
            "Gregorian_Time",
            "Raw_IO_Type",
            "Source_Log_Type",
            "Record_No",
            "Matched_Employee",
            "Matched_Employee_Name",
            "Match_Rule",
            "Unmapped_Reason",
        ],
    )
    write_csv(
        attendance_summary_rows,
        ATTENDANCE_SUMMARY_CSV,
        [
            "employee",
            "employee_name",
            "attendance_date_jalali",
            "attendance_date_gregorian",
            "first_in",
            "last_out",
            "punch_count",
            "device_ids",
            "source_codes",
            "source_databases",
        ],
    )
    write_csv(
        source_database_summary_rows,
        SOURCE_DATABASE_SUMMARY_CSV,
        ["source_database", "source_table", "row_count"],
    )

    return {
        "live_sql_used": live_sql_used,
        "source_databases": source_databases,
        "source_log_count": len(source_rows),
        "mapped_log_count": len(detailed_mapped_rows),
        "import_row_count": len(import_rows),
        "unmapped_log_count": len(unmapped_rows),
        "attendance_summary_count": len(attendance_summary_rows),
        "files": {
            "source": CHECKIN_SOURCE_CSV,
            "import": CHECKIN_IMPORT_CSV,
            "unmapped": CHECKIN_UNMAPPED_CSV,
            "attendance_summary": ATTENDANCE_SUMMARY_CSV,
            "source_database_summary": SOURCE_DATABASE_SUMMARY_CSV,
        },
    }


@frappe.whitelist()
def export_employee_checkins_csv():
    by_person_id, by_device_code, by_name = load_employee_index()
    return _export_employee_checkins_with_index(by_person_id, by_device_code, by_name)


def export_employee_checkins_csv_from_master_csv(csv_path=EMPLOYEE_MASTER_CSV):
    by_person_id, by_device_code, by_name = load_employee_index_from_master_csv(csv_path)
    result = _export_employee_checkins_with_index(by_person_id, by_device_code, by_name)
    result["employee_index_source"] = csv_path
    return result


def main():
    parser = argparse.ArgumentParser(description="Export Employee Checkin CSV files.")
    parser.add_argument("--site", default="dehati", help="Frappe site name, default: dehati")
    parser.add_argument(
        "--master-csv",
        default=EMPLOYEE_MASTER_CSV,
        help="Master employee CSV path for standalone extraction mode.",
    )
    parser.add_argument(
        "--use-frappe",
        action="store_true",
        help="Use Employee records from ERPNext instead of the master CSV.",
    )
    args = parser.parse_args()

    if args.use_frappe:
        os.chdir(BENCH_PATH)
        frappe.init(site=args.site, sites_path=SITES_PATH)
        frappe.connect()
        try:
            result = export_employee_checkins_csv()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        finally:
            frappe.destroy()
        return

    result = export_employee_checkins_csv_from_master_csv(args.master_csv)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
