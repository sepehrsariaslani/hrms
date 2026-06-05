import os
from datetime import timedelta

import jdatetime
import pandas as pd
import pytds

server = "192.168.150.26"
database = "EOS"
password = "sa@123"
user = "winkart"
port = 1433

yesterday_jalali = jdatetime.date.today() - timedelta(days=1)
last_7_days_jalali = [yesterday_jalali - timedelta(days=offset) for offset in range(7)]

# ClockDmp dates are stored in Jalali YYYY/MM/DD format, e.g. 1405/01/13.
yesterday_jalali_str = yesterday_jalali.strftime("%Y/%m/%d")
last_7_days_jalali_str = [date_value.strftime("%Y/%m/%d") for date_value in last_7_days_jalali]

# Always save outputs next to this script, even if it is executed elsewhere.
output_dir = os.path.dirname(os.path.abspath(__file__))
yesterday_attendance_csv_path = os.path.join(output_dir, "Yesterday_Attendance.csv")
yesterday_attendance_summary_csv_path = os.path.join(output_dir, "Yesterday_Attendance_Summary.csv")
last_7_days_attendance_csv_path = os.path.join(output_dir, "Last_7_Days_Attendance.csv")
last_7_days_attendance_summary_csv_path = os.path.join(output_dir, "Last_7_Days_Attendance_Summary.csv")
latest_available_attendance_csv_path = os.path.join(output_dir, "Latest_Available_Attendance.csv")
latest_available_attendance_summary_csv_path = os.path.join(
    output_dir, "Latest_Available_Attendance_Summary.csv"
)
last_7_available_attendance_csv_path = os.path.join(
    output_dir, "Last_7_Available_Days_Attendance.csv"
)
last_7_available_attendance_summary_csv_path = os.path.join(
    output_dir, "Last_7_Available_Days_Attendance_Summary.csv"
)
yesterday_events_csv_path = os.path.join(output_dir, "Yesterday_Clock_Events.csv")
yesterday_summary_csv_path = os.path.join(output_dir, "Yesterday_Clock_Events_Summary.csv")
last_7_days_events_csv_path = os.path.join(output_dir, "Last_7_Days_Clock_Events.csv")
last_7_days_summary_csv_path = os.path.join(output_dir, "Last_7_Days_Clock_Events_Summary.csv")
database_inventory_csv_path = os.path.join(output_dir, "EOS_Database_Inventory.csv")
latest_available_events_csv_path = os.path.join(output_dir, "Latest_Available_Clock_Events.csv")
latest_available_summary_csv_path = os.path.join(
    output_dir, "Latest_Available_Clock_Events_Summary.csv"
)
last_7_available_events_csv_path = os.path.join(
    output_dir, "Last_7_Available_Days_Clock_Events.csv"
)
last_7_available_summary_csv_path = os.path.join(
    output_dir, "Last_7_Available_Days_Clock_Events_Summary.csv"
)
employee_master_csv_path = os.path.join(output_dir, "Employee_Import_Master.csv")
employee_device_map_csv_path = os.path.join(output_dir, "Employee_Device_Code_Map.csv")


def get_connection():
    return pytds.connect(
        server=server,
        database=database,
        user=user,
        password=password,
        port=port,
    )


def fetch_dataframe(connection, query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description] if cursor.description else []
    return pd.DataFrame(rows, columns=columns)


def clean_dataframe(df):
    cleaned_df = df.copy()
    for column in cleaned_df.columns:
        cleaned_df[column] = cleaned_df[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
    return cleaned_df


def save_dataframe(df, csv_path):
    cleaned_df = clean_dataframe(df)
    cleaned_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Saved to: {csv_path}")


def format_connection_error(exc):
    return (
        "Cannot connect to SQL Server.\n"
        f"Server: {server}:{port}\n"
        "Check that VPN is connected and the server is reachable from this Mac.\n"
        f"Original error: {exc}"
    )


def join_unique_values(values):
    seen = set()
    ordered_values = []
    for value in values:
        if pd.isna(value):
            continue
        value_text = str(value).strip()
        if not value_text or value_text in seen:
            continue
        seen.add(value_text)
        ordered_values.append(value_text)
    return " | ".join(ordered_values)


def split_full_name(full_name):
    name_text = str(full_name or "").strip()
    if not name_text:
        return "", ""
    name_parts = name_text.split()
    if len(name_parts) == 1:
        return name_parts[0], ""
    return name_parts[0], " ".join(name_parts[1:])


def get_database_year(database_name):
    database_text = str(database_name or "").strip()
    if database_text.startswith("EOS_"):
        year_text = database_text.split("_", 1)[1]
        if year_text.isdigit():
            return year_text
    return ""


def normalize_jalali_date(date_value, database_name=""):
    date_text = str(date_value or "").strip()
    if not date_text:
        return ""

    parts = [part.strip() for part in date_text.split("/") if part.strip()]
    if len(parts) == 3:
        year_text, month_text, day_text = parts
        return f"{year_text.zfill(4)}/{month_text.zfill(2)}/{day_text.zfill(2)}"

    if len(parts) == 2:
        year_text = get_database_year(database_name)
        if year_text:
            month_text, day_text = parts
            return f"{year_text}/{month_text.zfill(2)}/{day_text.zfill(2)}"

    return date_text


def to_ioinfo_mmdd(date_value):
    date_text = str(date_value or "").strip()
    if not date_text:
        return ""

    parts = [part.strip() for part in date_text.split("/") if part.strip()]
    if len(parts) == 3:
        return f"{parts[1].zfill(2)}/{parts[2].zfill(2)}"
    if len(parts) == 2:
        return f"{parts[0].zfill(2)}/{parts[1].zfill(2)}"
    return date_text


def jalali_date_sort_key(date_value, database_name=""):
    normalized_date = normalize_jalali_date(date_value, database_name)
    parts = normalized_date.split("/")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return (0, 0, 0)
    return tuple(int(part) for part in parts)


def choose_earliest_date(*date_candidates):
    valid_candidates = [date for date in date_candidates if str(date or "").strip()]
    if not valid_candidates:
        return ""
    return min(valid_candidates, key=jalali_date_sort_key)


def choose_latest_date(*date_candidates):
    valid_candidates = [date for date in date_candidates if str(date or "").strip()]
    if not valid_candidates:
        return ""
    return max(valid_candidates, key=jalali_date_sort_key)


def prepare_today_events(df):
    if df.empty:
        return df

    prepared_df = clean_dataframe(df)
    prepared_df["Punch_Date"] = prepared_df["Punch_Date"].fillna("").astype(str).str.strip()
    prepared_df["Punch_Time"] = prepared_df["Punch_Time"].fillna("").astype(str).str.strip()
    prepared_df["Punch_DateTime"] = (
        prepared_df["Punch_Date"] + " " + prepared_df["Punch_Time"]
    ).str.strip()

    ordered_columns = [
        "Person_ID",
        "Full_Name",
        "Branch_Code",
        "Employee_Code",
        "Machine_No",
        "Punch_Date",
        "Punch_Time",
        "Punch_DateTime",
        "IO_Type",
        "Record_No",
        "Transferred",
    ]
    prepared_df = prepared_df[ordered_columns]
    prepared_df = prepared_df.sort_values(
        by=["Full_Name", "Branch_Code", "Employee_Code", "Machine_No", "Punch_Date", "Punch_Time"],
        kind="stable",
    ).reset_index(drop=True)
    return prepared_df


def build_today_summary(df):
    if df.empty:
        return pd.DataFrame()

    summary_df = (
        df.groupby(
            ["Person_ID", "Full_Name", "Branch_Code", "Employee_Code", "Machine_No"],
            dropna=False,
            sort=False,
        )
        .agg(
            Punch_Count=("Punch_DateTime", "size"),
            First_Punch=("Punch_DateTime", "first"),
            Last_Punch=("Punch_DateTime", "last"),
            Punch_Times=("Punch_Time", join_unique_values),
        )
        .reset_index()
    )

    summary_df = summary_df.sort_values(
        by=["Full_Name", "Branch_Code", "Employee_Code", "Machine_No"],
        kind="stable",
    ).reset_index(drop=True)
    return summary_df


def prepare_attendance_dataframe(df):
    if df.empty:
        return df

    prepared_df = clean_dataframe(df)
    for column in [
        "Person_ID",
        "Full_Name",
        "Source_Database",
        "In_Date",
        "In_Time",
        "Out_Date",
        "Out_Time",
    ]:
        if column not in prepared_df.columns:
            prepared_df[column] = ""

    prepared_df["In_Date"] = prepared_df["In_Date"].fillna("").astype(str).str.strip()
    prepared_df["In_Time"] = prepared_df["In_Time"].fillna("").astype(str).str.strip()
    prepared_df["Out_Date"] = prepared_df["Out_Date"].fillna("").astype(str).str.strip()
    prepared_df["Out_Time"] = prepared_df["Out_Time"].fillna("").astype(str).str.strip()
    prepared_df["In_DateTime"] = (
        prepared_df["In_Date"] + " " + prepared_df["In_Time"]
    ).str.strip()
    prepared_df["Out_DateTime"] = (
        prepared_df["Out_Date"] + " " + prepared_df["Out_Time"]
    ).str.strip()

    ordered_columns = [
        "Person_ID",
        "Full_Name",
        "Source_Database",
        "In_Date",
        "In_Time",
        "In_DateTime",
        "Out_Date",
        "Out_Time",
        "Out_DateTime",
    ]
    prepared_df = prepared_df[ordered_columns]
    prepared_df = prepared_df.sort_values(
        by=["In_Date", "In_Time", "Full_Name", "Person_ID"],
        ascending=[False, True, True, True],
        kind="stable",
    ).reset_index(drop=True)
    return prepared_df


def build_attendance_summary(df):
    if df.empty:
        return pd.DataFrame()

    summary_df = (
        df.groupby(["Person_ID", "Full_Name", "Source_Database"], dropna=False, sort=False)
        .agg(
            Attendance_Count=("In_DateTime", "size"),
            First_In=("In_DateTime", "first"),
            Last_Out=("Out_DateTime", "last"),
            In_Times=("In_Time", join_unique_values),
            Out_Times=("Out_Time", join_unique_values),
            Dates=("In_Date", join_unique_values),
        )
        .reset_index()
    )
    return summary_df.sort_values(
        by=["Full_Name", "Person_ID", "Source_Database"], kind="stable"
    ).reset_index(drop=True)


def build_in_clause_params(values):
    placeholders = ", ".join(["%s"] * len(values))
    return placeholders, values


def quote_sql_name(name):
    return f"[{str(name).replace(']', ']]')}]"


def fetch_eos_databases(connection):
    query = """
    SELECT name
    FROM master.sys.databases
    WHERE name = %s OR name LIKE %s
    ORDER BY name
    """
    df_databases = fetch_dataframe(connection, query, ["EOS", "EOS[_]%"])
    if df_databases.empty or "name" not in df_databases.columns:
        return []

    return [
        str(value).strip()
        for value in df_databases["name"].tolist()
        if value is not None and str(value).strip()
    ]


def table_exists(connection, database_name, table_name):
    quoted_database_name = quote_sql_name(database_name)
    query = f"""
    SELECT 1 AS table_exists
    FROM {quoted_database_name}.INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = %s
    """
    df_exists = fetch_dataframe(connection, query, [table_name])
    return not df_exists.empty


def fetch_recent_dates(connection, database_name, table_name, date_column, limit_count=7):
    quoted_database_name = quote_sql_name(database_name)
    quoted_table_name = quote_sql_name(table_name)
    quoted_date_column = quote_sql_name(date_column)
    query = f"""
    SELECT TOP {int(limit_count)}
        CAST({quoted_date_column} AS VARCHAR(50)) AS [Date_Value],
        COUNT(*) AS [Row_Count]
    FROM {quoted_database_name}.dbo.{quoted_table_name}
    WHERE NULLIF(LTRIM(RTRIM(CAST({quoted_date_column} AS VARCHAR(50)))), '') IS NOT NULL
    GROUP BY {quoted_date_column}
    ORDER BY {quoted_date_column} DESC
    """
    return clean_dataframe(fetch_dataframe(connection, query))


def fetch_attendance_records(connection, ioinfo_database_name, person_database_name, date_values):
    ioinfo_date_values = [to_ioinfo_mmdd(value) for value in date_values if to_ioinfo_mmdd(value)]
    if not ioinfo_date_values:
        return pd.DataFrame()
    placeholders, params = build_in_clause_params(ioinfo_date_values)
    quoted_ioinfo_database_name = quote_sql_name(ioinfo_database_name)
    quoted_person_database_name = quote_sql_name(person_database_name)
    query = f"""
    SELECT
        CAST(i.PERNO AS VARCHAR(50)) AS [Person_ID],
        LTRIM(RTRIM(
            ISNULL(LTRIM(RTRIM(p.FIRSTNAME)), '') +
            CASE
                WHEN ISNULL(LTRIM(RTRIM(p.LASTNAME)), '') = '' THEN ''
                ELSE ' ' + LTRIM(RTRIM(p.LASTNAME))
            END
        )) AS [Full_Name],
        %s AS [Source_Database],
        CAST(i.BEGINDATE AS VARCHAR(50)) AS [In_Date],
        CAST(i.BEGINTIME AS VARCHAR(50)) AS [In_Time],
        CAST(i.ENDDATE AS VARCHAR(50)) AS [Out_Date],
        CAST(i.ENDTIME AS VARCHAR(50)) AS [Out_Time]
    FROM {quoted_ioinfo_database_name}.dbo.IOInfo i
    LEFT JOIN {quoted_person_database_name}.dbo.Person p ON i.PERNO = p.PERNO
    WHERE i.BEGINDATE IN ({placeholders}) OR i.ENDDATE IN ({placeholders})
    ORDER BY i.BEGINDATE DESC, i.BEGINTIME, p.FIRSTNAME, p.LASTNAME, i.PERNO
    """
    attendance_params = [ioinfo_database_name, *params, *params]
    return prepare_attendance_dataframe(fetch_dataframe(connection, query, attendance_params))


def fetch_all_persons(connection, person_database_name):
    quoted_person_database_name = quote_sql_name(person_database_name)
    query = f"""
    SELECT
        CAST(p.PERNO AS VARCHAR(50)) AS [Person_ID],
        LTRIM(RTRIM(ISNULL(p.FIRSTNAME, ''))) AS [First_Name],
        LTRIM(RTRIM(ISNULL(p.LASTNAME, ''))) AS [Last_Name],
        LTRIM(RTRIM(
            ISNULL(LTRIM(RTRIM(p.FIRSTNAME)), '') +
            CASE
                WHEN ISNULL(LTRIM(RTRIM(p.LASTNAME)), '') = '' THEN ''
                ELSE ' ' + LTRIM(RTRIM(p.LASTNAME))
            END
        )) AS [Full_Name]
    FROM {quoted_person_database_name}.dbo.Person p
    ORDER BY p.PERNO
    """
    df_persons = clean_dataframe(fetch_dataframe(connection, query))
    if df_persons.empty:
        return df_persons

    df_persons["Person_ID"] = df_persons["Person_ID"].fillna("").astype(str).str.strip()
    df_persons = df_persons[df_persons["Person_ID"] != ""].reset_index(drop=True)
    return df_persons


def fetch_employee_device_map(connection, clock_database_name, person_database_name):
    quoted_clock_database_name = quote_sql_name(clock_database_name)
    quoted_person_database_name = quote_sql_name(person_database_name)
    query = f"""
    SELECT
        CAST(c.PERNO AS VARCHAR(50)) AS [Person_ID],
        LTRIM(RTRIM(
            ISNULL(LTRIM(RTRIM(p.FIRSTNAME)), '') +
            CASE
                WHEN ISNULL(LTRIM(RTRIM(p.LASTNAME)), '') = '' THEN ''
                ELSE ' ' + LTRIM(RTRIM(p.LASTNAME))
            END
        )) AS [Full_Name],
        CAST(c.ComCode AS VARCHAR(50)) AS [Branch_Code],
        CAST(c.MASHINNO AS VARCHAR(50)) AS [Machine_No],
        CAST(c.KARTNO AS VARCHAR(50)) AS [Employee_Code],
        MIN(CAST(c.CLOCKDATE AS VARCHAR(50))) AS [First_Punch_Date],
        MAX(CAST(c.CLOCKDATE AS VARCHAR(50))) AS [Last_Punch_Date],
        COUNT(*) AS [Punch_Count]
    FROM {quoted_clock_database_name}.dbo.ClockDmp c
    LEFT JOIN {quoted_person_database_name}.dbo.Person p ON c.PERNO = p.PERNO
    WHERE c.PERNO IS NOT NULL
    GROUP BY
        c.PERNO,
        p.FIRSTNAME,
        p.LASTNAME,
        c.ComCode,
        c.MASHINNO,
        c.KARTNO
    ORDER BY p.FIRSTNAME, p.LASTNAME, c.MASHINNO, c.KARTNO
    """
    df_device_map = clean_dataframe(fetch_dataframe(connection, query))
    if df_device_map.empty:
        return df_device_map

    for column in [
        "Person_ID",
        "Full_Name",
        "Branch_Code",
        "Machine_No",
        "Employee_Code",
        "First_Punch_Date",
        "Last_Punch_Date",
    ]:
        df_device_map[column] = df_device_map[column].fillna("").astype(str).str.strip()

    df_device_map["Punch_Count"] = pd.to_numeric(
        df_device_map["Punch_Count"], errors="coerce"
    ).fillna(0).astype(int)
    return df_device_map


def fetch_employee_membership(connection, ioinfo_database_names):
    membership_rows = []
    for database_name in ioinfo_database_names:
        quoted_database_name = quote_sql_name(database_name)
        query = f"""
        SELECT
            CAST(i.PERNO AS VARCHAR(50)) AS [Person_ID],
            MIN(CAST(i.BEGINDATE AS VARCHAR(50))) AS [First_In_Date],
            MAX(CAST(i.BEGINDATE AS VARCHAR(50))) AS [Last_In_Date],
            COUNT(*) AS [Attendance_Count]
        FROM {quoted_database_name}.dbo.IOInfo i
        WHERE i.PERNO IS NOT NULL
          AND NULLIF(LTRIM(RTRIM(CAST(i.BEGINDATE AS VARCHAR(50)))), '') IS NOT NULL
        GROUP BY i.PERNO
        """
        df_year = clean_dataframe(fetch_dataframe(connection, query))
        if df_year.empty:
            continue

        df_year["Source_Database"] = database_name
        membership_rows.append(df_year)

    if not membership_rows:
        return pd.DataFrame()

    combined_rows = {}
    for df_year in membership_rows:
        for row in df_year.to_dict("records"):
            person_id = str(row.get("Person_ID", "") or "").strip()
            if not person_id:
                continue

            first_date = normalize_jalali_date(
                row.get("First_In_Date", ""),
                row.get("Source_Database", ""),
            )
            last_date = normalize_jalali_date(
                row.get("Last_In_Date", ""),
                row.get("Source_Database", ""),
            )
            attendance_count = int(pd.to_numeric(row.get("Attendance_Count", 0), errors="coerce") or 0)
            source_database = str(row.get("Source_Database", "") or "").strip()

            if person_id not in combined_rows:
                combined_rows[person_id] = {
                    "Person_ID": person_id,
                    "Membership_Date": first_date,
                    "Membership_Source_Database": source_database,
                    "Latest_Attendance_Date": last_date,
                    "Attendance_Source_Databases": [source_database] if source_database else [],
                    "Total_Attendance_Records": attendance_count,
                }
                continue

            current_row = combined_rows[person_id]
            current_membership_date = current_row["Membership_Date"]
            chosen_membership_date = choose_earliest_date(current_membership_date, first_date)
            if chosen_membership_date != current_membership_date:
                current_row["Membership_Date"] = chosen_membership_date
                current_row["Membership_Source_Database"] = source_database

            current_row["Latest_Attendance_Date"] = choose_latest_date(
                current_row["Latest_Attendance_Date"],
                last_date,
            )
            current_row["Total_Attendance_Records"] += attendance_count
            if source_database and source_database not in current_row["Attendance_Source_Databases"]:
                current_row["Attendance_Source_Databases"].append(source_database)

    membership_df = pd.DataFrame(combined_rows.values())
    if membership_df.empty:
        return membership_df

    membership_df["Attendance_Source_Databases"] = membership_df[
        "Attendance_Source_Databases"
    ].map(lambda value: " | ".join(value))
    membership_df = membership_df.sort_values(by=["Membership_Date", "Person_ID"]).reset_index(drop=True)
    return membership_df


def build_device_map_text(group_df):
    ordered_group = group_df.sort_values(
        by=["Punch_Count", "Machine_No", "Employee_Code", "Branch_Code"],
        ascending=[False, True, True, True],
        kind="stable",
    )
    parts = []
    for row in ordered_group.to_dict("records"):
        branch_code = str(row.get("Branch_Code", "") or "").strip()
        machine_no = str(row.get("Machine_No", "") or "").strip()
        employee_code = str(row.get("Employee_Code", "") or "").strip()
        first_date = str(row.get("First_Punch_Date", "") or "").strip()
        last_date = str(row.get("Last_Punch_Date", "") or "").strip()
        punch_count = int(pd.to_numeric(row.get("Punch_Count", 0), errors="coerce") or 0)
        parts.append(
            f"branch {branch_code} / machine {machine_no} / code {employee_code} / "
            f"first {first_date} / last {last_date} / punches {punch_count}"
        )
    return " || ".join(parts)


def build_employee_master(df_persons, df_membership, df_device_map):
    master_df = df_persons.copy()
    if master_df.empty:
        return master_df

    if not df_membership.empty:
        master_df = master_df.merge(df_membership, on="Person_ID", how="left")
    if not df_device_map.empty:
        device_summary_rows = []
        for person_id, group_df in df_device_map.groupby("Person_ID", dropna=False, sort=False):
            ordered_group = group_df.sort_values(
                by=["Punch_Count", "Last_Punch_Date", "Machine_No", "Employee_Code"],
                ascending=[False, False, True, True],
                kind="stable",
            ).reset_index(drop=True)
            top_row = ordered_group.iloc[0]
            device_summary_rows.append(
                {
                    "Person_ID": str(person_id).strip(),
                    "Primary_Branch_Code": str(top_row["Branch_Code"]).strip(),
                    "Primary_Machine_No": str(top_row["Machine_No"]).strip(),
                    "Primary_Employee_Code": str(top_row["Employee_Code"]).strip(),
                    "Branch_Codes": join_unique_values(ordered_group["Branch_Code"]),
                    "Machine_Nos": join_unique_values(ordered_group["Machine_No"]),
                    "Employee_Codes": join_unique_values(ordered_group["Employee_Code"]),
                    "Device_Map_Detail": build_device_map_text(ordered_group),
                    "Device_Map_Count": len(ordered_group),
                    "Total_Clock_Punches": int(ordered_group["Punch_Count"].sum()),
                }
            )

        device_summary_df = pd.DataFrame(device_summary_rows)
        master_df = master_df.merge(device_summary_df, on="Person_ID", how="left")

    split_name_df = master_df["Full_Name"].map(split_full_name)
    master_df["Import_First_Name"] = split_name_df.map(lambda value: value[0])
    master_df["Import_Last_Name"] = split_name_df.map(lambda value: value[1])
    master_df["Employee_Number"] = master_df["Person_ID"]
    master_df["Employee_Name"] = master_df["Full_Name"]
    master_df["Date_Of_Joining"] = master_df.get("Membership_Date", "")
    master_df["Attendance_Device_ID"] = master_df.get("Primary_Employee_Code", "")
    master_df["Branch"] = master_df.get("Primary_Branch_Code", "")

    ordered_columns = [
        "Employee_Number",
        "Employee_Name",
        "Import_First_Name",
        "Import_Last_Name",
        "Person_ID",
        "Full_Name",
        "Date_Of_Joining",
        "Membership_Date",
        "Membership_Source_Database",
        "Latest_Attendance_Date",
        "Attendance_Source_Databases",
        "Attendance_Device_ID",
        "Primary_Employee_Code",
        "Primary_Machine_No",
        "Branch",
        "Primary_Branch_Code",
        "Branch_Codes",
        "Machine_Nos",
        "Employee_Codes",
        "Device_Map_Count",
        "Total_Clock_Punches",
        "Device_Map_Detail",
        "Total_Attendance_Records",
    ]

    for column in ordered_columns:
        if column not in master_df.columns:
            master_df[column] = ""

    master_df = master_df[ordered_columns].sort_values(
        by=["Employee_Name", "Employee_Number"], kind="stable"
    ).reset_index(drop=True)
    return clean_dataframe(master_df)


def build_database_inventory(connection):
    inventory_rows = []
    for database_name in fetch_eos_databases(connection):
        row = {
            "Database_Name": database_name,
            "Has_ClockDmp": 0,
            "Has_Person": 0,
            "Has_IOInfo": 0,
            "Latest_ClockDmp_Date": "",
            "Latest_ClockDmp_Row_Count": "",
            "Latest_IOInfo_BeginDate": "",
            "Latest_IOInfo_Row_Count": "",
        }

        try:
            row["Has_ClockDmp"] = int(table_exists(connection, database_name, "ClockDmp"))
            row["Has_Person"] = int(table_exists(connection, database_name, "Person"))
            row["Has_IOInfo"] = int(table_exists(connection, database_name, "IOInfo"))

            if row["Has_ClockDmp"]:
                df_clock_dates = fetch_recent_dates(
                    connection,
                    database_name,
                    "ClockDmp",
                    "CLOCKDATE",
                    limit_count=1,
                )
                if not df_clock_dates.empty:
                    row["Latest_ClockDmp_Date"] = df_clock_dates.iloc[0]["Date_Value"]
                    row["Latest_ClockDmp_Row_Count"] = df_clock_dates.iloc[0]["Row_Count"]

            if row["Has_IOInfo"]:
                df_io_dates = fetch_recent_dates(
                    connection,
                    database_name,
                    "IOInfo",
                    "BEGINDATE",
                    limit_count=1,
                )
                if not df_io_dates.empty:
                    row["Latest_IOInfo_BeginDate"] = df_io_dates.iloc[0]["Date_Value"]
                    row["Latest_IOInfo_Row_Count"] = df_io_dates.iloc[0]["Row_Count"]
        except Exception as exc:
            row["Inspect_Error"] = str(exc)

        inventory_rows.append(row)

    return clean_dataframe(pd.DataFrame(inventory_rows))


def pick_best_source_database(inventory_df, date_column, required_flag_column):
    if inventory_df.empty:
        return None

    working_df = inventory_df.copy()
    if required_flag_column in working_df.columns:
        working_df = working_df[working_df[required_flag_column] == 1]

    if working_df.empty or date_column not in working_df.columns:
        return None

    working_df = working_df.copy()
    working_df[date_column] = working_df.apply(
        lambda row: normalize_jalali_date(row.get(date_column, ""), row.get("Database_Name", "")),
        axis=1,
    )
    working_df = working_df[working_df[date_column].astype(str).str.strip() != ""]
    if working_df.empty:
        return None

    working_df["__sort_key"] = working_df[date_column].map(jalali_date_sort_key)
    working_df = working_df.sort_values(
        by=["__sort_key", "Database_Name"],
        ascending=[False, True],
        kind="stable",
    )
    return working_df.iloc[0]["Database_Name"]


def list_ioinfo_databases(inventory_df):
    if inventory_df.empty or "Has_IOInfo" not in inventory_df.columns:
        return []

    working_df = inventory_df[inventory_df["Has_IOInfo"] == 1].copy()
    if working_df.empty:
        return []

    working_df["__db_year"] = working_df["Database_Name"].map(get_database_year)
    working_df = working_df.sort_values(
        by=["__db_year", "Database_Name"],
        ascending=[True, True],
        kind="stable",
    )
    return working_df["Database_Name"].astype(str).tolist()


def fetch_period_events(connection, clock_database_name, person_database_name, date_values):
    placeholders, params = build_in_clause_params(date_values)
    quoted_clock_database_name = quote_sql_name(clock_database_name)
    quoted_person_database_name = quote_sql_name(person_database_name)
    query = f"""
    SELECT
        CAST(c.PERNO AS VARCHAR(50)) AS [Person_ID],
        LTRIM(RTRIM(
            ISNULL(LTRIM(RTRIM(p.FIRSTNAME)), '') +
            CASE
                WHEN ISNULL(LTRIM(RTRIM(p.LASTNAME)), '') = '' THEN ''
                ELSE ' ' + LTRIM(RTRIM(p.LASTNAME))
            END
        )) AS [Full_Name],
        CAST(c.ComCode AS VARCHAR(50)) AS [Branch_Code],
        CAST(c.KARTNO AS VARCHAR(50)) AS [Employee_Code],
        CAST(c.MASHINNO AS VARCHAR(50)) AS [Machine_No],
        CAST(c.CLOCKDATE AS VARCHAR(50)) AS [Punch_Date],
        CAST(c.CLOCKTIME AS VARCHAR(50)) AS [Punch_Time],
        CAST(c.IO_TYPE AS VARCHAR(50)) AS [IO_Type],
        CAST(c.REC AS VARCHAR(50)) AS [Record_No],
        CAST(c.TRANSFERED AS VARCHAR(50)) AS [Transferred]
    FROM {quoted_clock_database_name}.dbo.ClockDmp c
    LEFT JOIN {quoted_person_database_name}.dbo.Person p ON c.PERNO = p.PERNO
    WHERE c.CLOCKDATE IN ({placeholders})
    ORDER BY
        c.CLOCKDATE DESC,
        LTRIM(RTRIM(ISNULL(p.FIRSTNAME, ''))),
        LTRIM(RTRIM(ISNULL(p.LASTNAME, ''))),
        c.ComCode,
        c.KARTNO,
        c.MASHINNO,
        c.CLOCKTIME
    """
    return prepare_today_events(fetch_dataframe(connection, query, params))


def fetch_latest_available_dates(connection, clock_database_name, limit_count=7):
    quoted_clock_database_name = quote_sql_name(clock_database_name)
    query = f"""
    SELECT TOP {int(limit_count)}
        CAST(c.CLOCKDATE AS VARCHAR(50)) AS [Clock_Date]
    FROM {quoted_clock_database_name}.dbo.ClockDmp c
    WHERE NULLIF(LTRIM(RTRIM(CAST(c.CLOCKDATE AS VARCHAR(50)))), '') IS NOT NULL
    GROUP BY c.CLOCKDATE
    ORDER BY c.CLOCKDATE DESC
    """
    df_dates = fetch_dataframe(connection, query)
    if df_dates.empty or "Clock_Date" not in df_dates.columns:
        return []

    return [
        str(value).strip()
        for value in df_dates["Clock_Date"].tolist()
        if value is not None and str(value).strip()
    ]


def main():
    connection = None
    try:
        print("Connecting to SQL Server via pure python...")
        connection = get_connection()
        print(f"Output directory: {output_dir}")
        print("\nInspecting EOS databases...")

        df_inventory = build_database_inventory(connection)
        if df_inventory.empty:
            print("No EOS databases found or accessible.")
            return

        print(df_inventory.to_string(index=False))
        save_dataframe(df_inventory, database_inventory_csv_path)

        ioinfo_database_names = list_ioinfo_databases(df_inventory)
        clock_database_name = pick_best_source_database(
            df_inventory,
            "Latest_ClockDmp_Date",
            "Has_ClockDmp",
        )
        ioinfo_database_name = pick_best_source_database(
            df_inventory,
            "Latest_IOInfo_BeginDate",
            "Has_IOInfo",
        )
        person_database_name = pick_best_source_database(
            df_inventory,
            "Latest_ClockDmp_Date",
            "Has_Person",
        ) or "EOS"

        print(f"\nSelected ClockDmp database: {clock_database_name}")
        print(f"Selected IOInfo database: {ioinfo_database_name}")
        print(f"Selected Person database: {person_database_name}")
        print(f"All IOInfo databases: {', '.join(ioinfo_database_names)}")

        print("\nBuilding employee master export...")
        df_persons = fetch_all_persons(connection, person_database_name)
        df_membership = fetch_employee_membership(connection, ioinfo_database_names)
        df_device_map = (
            fetch_employee_device_map(connection, clock_database_name, person_database_name)
            if clock_database_name
            else pd.DataFrame()
        )

        if not df_device_map.empty:
            save_dataframe(df_device_map, employee_device_map_csv_path)

        if not df_persons.empty:
            df_employee_master = build_employee_master(df_persons, df_membership, df_device_map)
            if not df_employee_master.empty:
                print(df_employee_master.head(20).to_string(index=False))
                save_dataframe(df_employee_master, employee_master_csv_path)

        if ioinfo_database_name:
            print(f"\nFetching yesterday attendance from {ioinfo_database_name}...")
            df_yesterday_attendance = fetch_attendance_records(
                connection,
                ioinfo_database_name,
                person_database_name,
                [yesterday_jalali_str],
            )
            if df_yesterday_attendance.empty:
                print(f"No attendance records found for yesterday ({yesterday_jalali_str}).")
            else:
                print(f"Success! Found {len(df_yesterday_attendance)} attendance rows for yesterday.")
                print(df_yesterday_attendance.head(20).to_string(index=False))
                save_dataframe(df_yesterday_attendance, yesterday_attendance_csv_path)

                df_yesterday_attendance_summary = build_attendance_summary(df_yesterday_attendance)
                if not df_yesterday_attendance_summary.empty:
                    print("\nYesterday attendance summary preview:")
                    print(df_yesterday_attendance_summary.head(20).to_string(index=False))
                    save_dataframe(
                        df_yesterday_attendance_summary,
                        yesterday_attendance_summary_csv_path,
                    )

            print(f"\nFetching last 7 days attendance from {ioinfo_database_name}...")
            df_last_7_days_attendance = fetch_attendance_records(
                connection,
                ioinfo_database_name,
                person_database_name,
                last_7_days_jalali_str,
            )
            if df_last_7_days_attendance.empty:
                print(
                    "No attendance records found for the last 7 days ending yesterday "
                    f"({', '.join(last_7_days_jalali_str)})."
                )
            else:
                print(
                    f"Success! Found {len(df_last_7_days_attendance)} attendance rows for the last 7 days."
                )
                print(df_last_7_days_attendance.head(20).to_string(index=False))
                save_dataframe(df_last_7_days_attendance, last_7_days_attendance_csv_path)

                df_last_7_days_attendance_summary = build_attendance_summary(
                    df_last_7_days_attendance
                )
                if not df_last_7_days_attendance_summary.empty:
                    print("\nLast 7 days attendance summary preview:")
                    print(df_last_7_days_attendance_summary.head(20).to_string(index=False))
                    save_dataframe(
                        df_last_7_days_attendance_summary,
                        last_7_days_attendance_summary_csv_path,
                    )

            latest_attendance_dates_df = fetch_recent_dates(
                connection,
                ioinfo_database_name,
                "IOInfo",
                "BEGINDATE",
                limit_count=7,
            )
            latest_attendance_dates = (
                latest_attendance_dates_df["Date_Value"].tolist()
                if not latest_attendance_dates_df.empty
                else []
            )
            latest_attendance_dates = [
                str(value).strip() for value in latest_attendance_dates if str(value).strip()
            ]
            if latest_attendance_dates:
                print(f"\nLatest available attendance dates found in {ioinfo_database_name}.dbo.IOInfo:")
                print(", ".join(latest_attendance_dates))

                df_latest_available_attendance = fetch_attendance_records(
                    connection,
                    ioinfo_database_name,
                    person_database_name,
                    [latest_attendance_dates[0]],
                )
                if not df_latest_available_attendance.empty:
                    save_dataframe(
                        df_latest_available_attendance,
                        latest_available_attendance_csv_path,
                    )
                    df_latest_available_attendance_summary = build_attendance_summary(
                        df_latest_available_attendance
                    )
                    if not df_latest_available_attendance_summary.empty:
                        save_dataframe(
                            df_latest_available_attendance_summary,
                            latest_available_attendance_summary_csv_path,
                        )

                df_last_7_available_attendance = fetch_attendance_records(
                    connection,
                    ioinfo_database_name,
                    person_database_name,
                    latest_attendance_dates,
                )
                if not df_last_7_available_attendance.empty:
                    save_dataframe(
                        df_last_7_available_attendance,
                        last_7_available_attendance_csv_path,
                    )
                    df_last_7_available_attendance_summary = build_attendance_summary(
                        df_last_7_available_attendance
                    )
                    if not df_last_7_available_attendance_summary.empty:
                        save_dataframe(
                            df_last_7_available_attendance_summary,
                            last_7_available_attendance_summary_csv_path,
                        )

        if clock_database_name:
            print(f"Fetching yesterday's records for Jalali date: {yesterday_jalali_str}")
            print(
                "Fetching last 7 days ending yesterday for Jalali dates: "
                + ", ".join(last_7_days_jalali_str)
            )

            df_yesterday_events = fetch_period_events(
                connection,
                clock_database_name,
                person_database_name,
                [yesterday_jalali_str],
            )
            if df_yesterday_events.empty:
                print(f"No clock records found for yesterday ({yesterday_jalali_str}).")
            else:
                print(f"Success! Found {len(df_yesterday_events)} records for yesterday.")
                print(df_yesterday_events.head(20).to_string(index=False))
                save_dataframe(df_yesterday_events, yesterday_events_csv_path)

                df_yesterday_summary = build_today_summary(df_yesterday_events)
                if not df_yesterday_summary.empty:
                    print("\nYesterday summary preview:")
                    print(df_yesterday_summary.head(20).to_string(index=False))
                    save_dataframe(df_yesterday_summary, yesterday_summary_csv_path)

            df_last_7_days_events = fetch_period_events(
                connection,
                clock_database_name,
                person_database_name,
                last_7_days_jalali_str,
            )
            if df_last_7_days_events.empty:
                print(
                    "No clock records found for the last 7 days ending yesterday "
                    f"({', '.join(last_7_days_jalali_str)})."
                )
            else:
                print(f"\nSuccess! Found {len(df_last_7_days_events)} records for the last 7 days.")
                print(df_last_7_days_events.head(20).to_string(index=False))
                save_dataframe(df_last_7_days_events, last_7_days_events_csv_path)

                df_last_7_days_summary = build_today_summary(df_last_7_days_events)
                if not df_last_7_days_summary.empty:
                    print("\nLast 7 days summary preview:")
                    print(df_last_7_days_summary.head(20).to_string(index=False))
                    save_dataframe(df_last_7_days_summary, last_7_days_summary_csv_path)

            latest_available_dates = fetch_latest_available_dates(
                connection,
                clock_database_name,
                limit_count=7,
            )
            if latest_available_dates:
                print(f"\nLatest available dates found in {clock_database_name}.dbo.ClockDmp:")
                print(", ".join(latest_available_dates))

                latest_available_date = latest_available_dates[0]
                df_latest_available_events = fetch_period_events(
                    connection,
                    clock_database_name,
                    person_database_name,
                    [latest_available_date],
                )
                if not df_latest_available_events.empty:
                    print(
                        f"\nSuccess! Found {len(df_latest_available_events)} records for latest available date "
                        f"({latest_available_date})."
                    )
                    print(df_latest_available_events.head(20).to_string(index=False))
                    save_dataframe(df_latest_available_events, latest_available_events_csv_path)

                    df_latest_available_summary = build_today_summary(df_latest_available_events)
                    if not df_latest_available_summary.empty:
                        print("\nLatest available summary preview:")
                        print(df_latest_available_summary.head(20).to_string(index=False))
                        save_dataframe(df_latest_available_summary, latest_available_summary_csv_path)

                df_last_7_available_events = fetch_period_events(
                    connection,
                    clock_database_name,
                    person_database_name,
                    latest_available_dates,
                )
                if not df_last_7_available_events.empty:
                    print(
                        f"\nSuccess! Found {len(df_last_7_available_events)} records for the latest "
                        f"{len(latest_available_dates)} available date(s)."
                    )
                    print(df_last_7_available_events.head(20).to_string(index=False))
                    save_dataframe(df_last_7_available_events, last_7_available_events_csv_path)

                    df_last_7_available_summary = build_today_summary(df_last_7_available_events)
                    if not df_last_7_available_summary.empty:
                        print("\nLast 7 available days summary preview:")
                        print(df_last_7_available_summary.head(20).to_string(index=False))
                        save_dataframe(
                            df_last_7_available_summary,
                            last_7_available_summary_csv_path,
                        )
        else:
            print("No EOS database with ClockDmp data was found; clock event exports were skipped.")
    except Exception as exc:
        print(f"Query error: {format_connection_error(exc)}")
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
