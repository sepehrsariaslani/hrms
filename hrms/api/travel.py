import json
import re

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import flt, now_datetime, nowdate
from frappe.utils.file_manager import save_file

FLOW_TYPE_OPTIONS = ["برنامه‌ریزی‌شده", "بدون برنامه‌ریزی"]
MISSION_TYPE_OPTIONS = ["روزانه", "ساعتی"]
TRAVEL_STATUS_OPTIONS = [
    "در انتظار تایید برنامه سفر",
    "تایید برنامه سفر",
    "در حال انجام سفر",
    "در انتظار تایید نهایی سرپرست",
    "نیازمند اصلاح",
    "تایید نهایی سرپرست",
    "ردشده",
]

FINAL_APPROVED_STATUS = "تایید نهایی سرپرست"

SETTLEMENT_TYPE_COMPANY_DEBT = "company_debt"
SETTLEMENT_TYPE_EMPLOYEE_DEBT = "employee_debt"
SETTLEMENT_TYPE_BALANCED = "balanced"

EXPENSE_TYPE_FA_LABELS = {
    "travel": "هزینه سفر",
    "travel expense": "هزینه سفر",
    "transport": "هزینه رفت‌وآمد",
    "transportation": "هزینه رفت‌وآمد",
    "taxi": "هزینه تاکسی",
    "airfare": "بلیط هواپیما",
    "flight": "بلیط هواپیما",
    "hotel": "اقامت",
    "lodging": "اقامت",
    "accommodation": "اقامت",
    "food": "پذیرایی",
    "meal": "پذیرایی",
    "per diem": "فوق‌العاده روزانه",
    "daily allowance": "فوق‌العاده روزانه",
    "fuel": "سوخت",
    "parking": "پارکینگ",
    "toll": "عوارض",
    "communication": "ارتباطات",
    "internet": "اینترنت",
    "phone": "تلفن",
    "misc": "سایر",
    "miscellaneous": "سایر",
    "other": "سایر",
}

CUSTOM_FIELDS = {
    "Travel Request": [
        {
            "fieldname": "mission_title",
            "label": "Mission Title",
            "fieldtype": "Data",
            "insert_after": "description",
        },
        {
            "fieldname": "mission_destination",
            "label": "Mission Destination",
            "fieldtype": "Data",
            "insert_after": "mission_title",
        },
        {
            "fieldname": "mission_purpose_text",
            "label": "Mission Purpose",
            "fieldtype": "Small Text",
            "insert_after": "mission_destination",
        },
        {
            "fieldname": "mission_notes",
            "label": "Mission Notes",
            "fieldtype": "Small Text",
            "insert_after": "mission_purpose_text",
        },
        {
            "fieldname": "mission_flow_type",
            "label": "Mission Flow Type",
            "fieldtype": "Select",
            "options": "\n" + "\n".join(FLOW_TYPE_OPTIONS),
            "default": "بدون برنامه‌ریزی",
            "insert_after": "mission_notes",
        },
        {
            "fieldname": "mission_type",
            "label": "Mission Type",
            "fieldtype": "Select",
            "options": "\n" + "\n".join(MISSION_TYPE_OPTIONS),
            "default": "روزانه",
            "insert_after": "mission_flow_type",
        },
        {
            "fieldname": "mission_start_date",
            "label": "Mission Start Date",
            "fieldtype": "Date",
            "insert_after": "mission_type",
        },
        {
            "fieldname": "mission_end_date",
            "label": "Mission End Date",
            "fieldtype": "Date",
            "insert_after": "mission_start_date",
        },
        {
            "fieldname": "mission_hourly_date",
            "label": "Mission Hourly Date",
            "fieldtype": "Date",
            "insert_after": "mission_end_date",
        },
        {
            "fieldname": "mission_hourly_from_time",
            "label": "Mission Hourly From Time",
            "fieldtype": "Time",
            "insert_after": "mission_hourly_date",
        },
        {
            "fieldname": "mission_hourly_to_time",
            "label": "Mission Hourly To Time",
            "fieldtype": "Time",
            "insert_after": "mission_hourly_from_time",
        },
        {
            "fieldname": "requested_advance_amount",
            "label": "Requested Advance Amount",
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "insert_after": "mission_hourly_to_time",
        },
        {
            "fieldname": "mission_total_expense",
            "label": "Mission Total Expense",
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "read_only": 1,
            "insert_after": "requested_advance_amount",
        },
        {
            "fieldname": "travel_status",
            "label": "Travel Status",
            "fieldtype": "Select",
            "options": "\n" + "\n".join(TRAVEL_STATUS_OPTIONS),
            "default": "در حال انجام سفر",
            "insert_after": "mission_total_expense",
        },
        {
            "fieldname": "supervisor_employee",
            "label": "Supervisor Employee",
            "fieldtype": "Link",
            "options": "Employee",
            "read_only": 1,
            "insert_after": "travel_status",
        },
        {
            "fieldname": "completed_on",
            "label": "Completed On",
            "fieldtype": "Datetime",
            "read_only": 1,
            "insert_after": "supervisor_employee",
        },
        {
            "fieldname": "approved_on",
            "label": "Approved On",
            "fieldtype": "Datetime",
            "read_only": 1,
            "insert_after": "completed_on",
        },
        {
            "fieldname": "settlement_type",
            "label": "Settlement Type",
            "fieldtype": "Select",
            "options": "\ncompany_debt\nemployee_debt\nbalanced",
            "read_only": 1,
            "insert_after": "approved_on",
        },
        {
            "fieldname": "settlement_amount",
            "label": "Settlement Amount",
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "read_only": 1,
            "insert_after": "settlement_type",
        },
        {
            "fieldname": "settlement_note",
            "label": "Settlement Note",
            "fieldtype": "Small Text",
            "read_only": 1,
            "insert_after": "settlement_amount",
        },
        {
            "fieldname": "linked_expense_claim",
            "label": "Linked Expense Claim",
            "fieldtype": "Link",
            "options": "Expense Claim",
            "read_only": 1,
            "insert_after": "settlement_note",
        },
    ],
    "Travel Request Costing": [
        {
            "fieldname": "expense_date",
            "label": "Expense Date",
            "fieldtype": "Date",
            "insert_after": "expense_type",
        },
        {
            "fieldname": "expense_client_id",
            "label": "Expense Client ID",
            "fieldtype": "Data",
            "read_only": 1,
            "hidden": 1,
            "insert_after": "expense_date",
        },
        {
            "fieldname": "receipt_file",
            "label": "Expense Receipt",
            "fieldtype": "Link",
            "options": "File",
            "insert_after": "expense_client_id",
        },
    ],
    "Expense Claim": [
        {
            "fieldname": "travel_request_ref",
            "label": "Travel Request",
            "fieldtype": "Link",
            "options": "Travel Request",
            "read_only": 1,
            "insert_after": "vehicle_log",
        }
    ],
}


@frappe.whitelist()
def get_travel_expense_types() -> list[dict]:
    ensure_travel_setup()
    employee = get_current_employee()

    rows = frappe.get_all(
        "Expense Claim Type",
        fields=["name", "expense_type", "description"],
        order_by="expense_type asc",
    )

    options = []
    for row in rows:
        default_account = frappe.db.get_value(
            "Expense Claim Account",
            {"parent": row.name, "company": employee.company},
            "default_account",
        )
        options.append(
            {
                "name": row.name,
                "label": localize_expense_type_label(row.expense_type or row.name),
                "description": row.description or "",
                "default_account": default_account,
            }
        )

    return options


@frappe.whitelist()
def get_travel_requests(limit: int | str = 50, for_approval: int | str = 0) -> list[dict]:
    ensure_travel_setup()
    employee = get_current_employee()

    limit_count = max(1, min(int(limit or 50), 200))
    for_approval_flag = int(for_approval or 0)

    filters = {"supervisor_employee": employee.name} if for_approval_flag else {"employee": employee.name}
    names = frappe.get_all(
        "Travel Request",
        filters=filters,
        fields=["name"],
        order_by="modified desc",
        limit_page_length=limit_count,
        ignore_permissions=True,
    )

    rows = []
    for row in names:
        doc = frappe.get_doc("Travel Request", row.name)
        if not can_access_travel(doc, employee):
            continue
        rows.append(serialize_travel_request(doc, employee))

    return rows


@frappe.whitelist()
def get_travel_request_detail(name: str) -> dict:
    ensure_travel_setup()
    employee = get_current_employee()
    doc = frappe.get_doc("Travel Request", name)
    enforce_access(doc, employee)
    return serialize_travel_request(doc, employee)


@frappe.whitelist()
def attach_travel_expense_image(
    name: str,
    expense_id: str,
    file_name: str,
    file_content: str,
) -> dict:
    ensure_travel_setup()
    employee = get_current_employee()
    doc = frappe.get_doc("Travel Request", name)
    enforce_access(doc, employee)

    if not file_name:
        frappe.throw(_("نام فایل الزامی است."))
    if not file_content:
        frappe.throw(_("محتوای فایل الزامی است."))

    costing = find_costing_row_by_identifier(doc, expense_id)
    if not costing:
        frappe.throw(_("هزینه انتخاب‌شده برای این سفر پیدا نشد."))

    base64_content = normalize_data_url(file_content)
    estimated_size = int(len(base64_content) * 0.75)
    if estimated_size > 5 * 1024 * 1024:
        frappe.throw(_("حجم هر تصویر باید کمتر از ۵ مگابایت باشد."))

    original_max_file_size = frappe.conf.get("max_file_size")
    restore_max_file_size = False
    if isinstance(original_max_file_size, str):
        frappe.conf.max_file_size = parse_file_size_to_bytes(original_max_file_size)
        restore_max_file_size = True

    try:
        file_doc = save_file(
            fname=file_name,
            content=base64_content,
            dt="Travel Request",
            dn=doc.name,
            folder="Home/Attachments",
            decode=True,
            is_private=1,
        )
    finally:
        if restore_max_file_size:
            frappe.conf.max_file_size = original_max_file_size

    costing.receipt_file = file_doc.name
    doc.save(ignore_permissions=True)

    return {
        "expense_id": costing.expense_client_id or costing.name,
        "file_name": file_doc.file_name,
        "file_url": file_doc.file_url,
        "receipt_file": file_doc.name,
    }


@frappe.whitelist()
def upsert_travel_request(payload: str | dict | None = None) -> dict:
    ensure_travel_setup()
    employee = get_current_employee()
    data = parse_payload(payload)

    name = data.get("id") or data.get("name")
    if name:
        doc = frappe.get_doc("Travel Request", name)
        enforce_access(doc, employee)
        if doc.travel_status == FINAL_APPROVED_STATUS:
            frappe.throw(_("درخواست سفر تایید نهایی شده و قابل ویرایش نیست."))
    else:
        doc = frappe.new_doc("Travel Request")
        doc.employee = employee.name
        doc.company = employee.company

    if doc.employee != employee.name and not is_supervisor_of(doc.employee, employee.name):
        frappe.throw(_("فقط می‌توانید درخواست سفر خودتان را ویرایش کنید."), frappe.PermissionError)

    apply_payload_to_doc(doc, data, employee)

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    doc.reload()
    return serialize_travel_request(doc, employee)


@frappe.whitelist()
def apply_travel_action(name: str, action: str, payload: str | dict | None = None) -> dict:
    ensure_travel_setup()
    employee = get_current_employee()
    doc = frappe.get_doc("Travel Request", name)
    enforce_access(doc, employee)

    action_key = (action or "").strip().lower()
    if not action_key:
        frappe.throw(_("نوع عملیات مشخص نشده است."))

    status = normalize_status(doc.travel_status)

    if action_key == "approve_plan":
        ensure_supervisor(doc, employee)
        ensure_status(status, ["در انتظار تایید برنامه سفر"])
        doc.travel_status = "تایید برنامه سفر"
    elif action_key == "reject_plan":
        ensure_supervisor(doc, employee)
        ensure_status(status, ["در انتظار تایید برنامه سفر"])
        doc.travel_status = "ردشده"
    elif action_key == "start_trip":
        ensure_owner(doc, employee)
        ensure_status(status, ["تایید برنامه سفر", "در حال انجام سفر"])
        doc.travel_status = "در حال انجام سفر"
    elif action_key == "complete_trip":
        ensure_owner(doc, employee)
        ensure_status(status, ["در حال انجام سفر"])
        doc.travel_status = "در انتظار تایید نهایی سرپرست"
        doc.completed_on = now_datetime()
    elif action_key == "resubmit_after_edit":
        ensure_owner(doc, employee)
        ensure_status(status, ["نیازمند اصلاح"])
        doc.travel_status = "در انتظار تایید نهایی سرپرست"
    elif action_key == "send_for_correction":
        ensure_supervisor(doc, employee)
        ensure_status(status, ["در انتظار تایید نهایی سرپرست"])
        doc.travel_status = "نیازمند اصلاح"
    elif action_key == "reject_final":
        ensure_supervisor(doc, employee)
        ensure_status(status, ["در انتظار تایید نهایی سرپرست"])
        doc.travel_status = "ردشده"
    elif action_key == "approve_final":
        ensure_supervisor(doc, employee)
        ensure_status(status, ["در انتظار تایید نهایی سرپرست"])
        doc.travel_status = FINAL_APPROVED_STATUS
        doc.approved_on = now_datetime()
        apply_settlement(doc)
        claim_name = ensure_expense_claim_from_travel(doc, employee)
        if claim_name:
            doc.linked_expense_claim = claim_name
    else:
        frappe.throw(_("عملیات سفر پشتیبانی نمی‌شود: {0}").format(action))

    doc.save(ignore_permissions=True)
    doc.reload()
    return serialize_travel_request(doc, employee)


def ensure_travel_setup():
    if not frappe.db.exists("DocType", "Travel Request"):
        frappe.throw(_("داکتایپ Travel Request نصب یا فعال نیست."))
    create_custom_fields(CUSTOM_FIELDS, update=True)


def parse_payload(payload: str | dict | None = None) -> dict:
    if not payload:
        return {}
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError as error:
            frappe.throw(_("داده ارسالی نامعتبر است: {0}").format(error))
    frappe.throw(_("فرمت داده ارسالی معتبر نیست."))
    return {}


def get_current_employee() -> frappe._dict:
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user, "status": "Active"},
        ["name", "employee_name", "company", "reports_to", "user_id"],
        as_dict=True,
    )
    if not employee:
        frappe.throw(_("حساب شما به کارمند فعال متصل نیست."), frappe.PermissionError)
    return employee


def is_supervisor_of(employee_name: str, supervisor_employee_name: str) -> bool:
    reports_to = frappe.db.get_value("Employee", employee_name, "reports_to")
    return bool(reports_to and reports_to == supervisor_employee_name)


def can_access_travel(doc, employee: frappe._dict) -> bool:
    return doc.employee == employee.name or doc.supervisor_employee == employee.name


def enforce_access(doc, employee: frappe._dict):
    if can_access_travel(doc, employee):
        return
    frappe.throw(_("اجازه دسترسی به این درخواست سفر را ندارید."), frappe.PermissionError)


def ensure_owner(doc, employee: frappe._dict):
    if doc.employee == employee.name:
        return
    frappe.throw(_("فقط ثبت‌کننده سفر می‌تواند این عملیات را انجام دهد."), frappe.PermissionError)


def ensure_supervisor(doc, employee: frappe._dict):
    if doc.supervisor_employee == employee.name:
        return
    frappe.throw(_("فقط سرپرست مستقیم می‌تواند این عملیات را انجام دهد."), frappe.PermissionError)


def ensure_status(current_status: str, allowed_statuses: list[str]):
    if current_status in allowed_statuses:
        return
    frappe.throw(
        _("این عملیات در وضعیت فعلی مجاز نیست ({0}).").format(current_status),
        frappe.ValidationError,
    )


def normalize_flow_type(value: str | None) -> str:
    candidate = (value or "").strip()
    if candidate in FLOW_TYPE_OPTIONS:
        return candidate
    return "بدون برنامه‌ریزی"


def normalize_mission_type(value: str | None) -> str:
    candidate = (value or "").strip()
    if candidate in MISSION_TYPE_OPTIONS:
        return candidate
    return "روزانه"


def normalize_status(value: str | None) -> str:
    candidate = (value or "").strip()
    if candidate in TRAVEL_STATUS_OPTIONS:
        return candidate
    return "در حال انجام سفر"


def localize_expense_type_label(value: str | None) -> str:
    candidate = (value or "").strip()
    if not candidate:
        return ""

    if re.search(r"[؀-ۿ]", candidate):
        return candidate

    normalized = re.sub(r"[\s_-]+", " ", candidate).strip().lower()
    if normalized in EXPENSE_TYPE_FA_LABELS:
        return EXPENSE_TYPE_FA_LABELS[normalized]

    for key, label in EXPENSE_TYPE_FA_LABELS.items():
        if key in normalized:
            return label

    return candidate


def normalize_data_url(content: str) -> str:
    if "," in content and content.startswith("data:"):
        return content.split(",", 1)[1]
    return content


def parse_file_size_to_bytes(value) -> int:
    if value is None:
        return 10 * 1024 * 1024

    if isinstance(value, (int, float)):
        return max(int(value), 1)

    text = str(value).strip().lower()
    if not text:
        return 10 * 1024 * 1024

    if text.isdigit():
        return max(int(text), 1)

    normalized = text.replace(" ", "")
    match = re.match(r"^(\d+(?:\.\d+)?)([kmgt]?b?)$", normalized)
    if not match:
        return 10 * 1024 * 1024

    number = float(match.group(1))
    unit = match.group(2)
    multipliers = {
        "": 1,
        "b": 1,
        "k": 1024,
        "kb": 1024,
        "m": 1024**2,
        "mb": 1024**2,
        "g": 1024**3,
        "gb": 1024**3,
        "t": 1024**4,
        "tb": 1024**4,
    }
    return max(int(number * multipliers.get(unit, 1)), 1)


def find_costing_row_by_identifier(doc, expense_id: str):
    target = (expense_id or "").strip()
    if not target:
        return None

    for row in doc.costings or []:
        if row.name == target or (row.expense_client_id and row.expense_client_id == target):
            return row

    return None


def get_default_purpose_of_travel() -> str:
    existing = frappe.get_all("Purpose of Travel", fields=["name"], limit=1)
    if existing:
        return existing[0].name

    doc = frappe.new_doc("Purpose of Travel")
    doc.purpose_of_travel = "ماموریت کاری"
    doc.insert(ignore_permissions=True)
    return doc.name


def resolve_expense_claim_type(raw_value: str | None, company: str) -> str:
    candidate = (raw_value or "").strip()
    if candidate and frappe.db.exists("Expense Claim Type", candidate):
        return candidate

    if candidate:
        by_title = frappe.db.get_value("Expense Claim Type", {"expense_type": candidate}, "name")
        if by_title:
            return by_title

    by_company = frappe.db.get_value(
        "Expense Claim Account",
        {"company": company},
        "parent",
        order_by="idx asc",
    )
    if by_company:
        return by_company

    first_type = frappe.db.get_value("Expense Claim Type", {}, "name")
    if first_type:
        return first_type

    frappe.throw(_("هیچ نوع هزینه‌ای در Expense Claim Type تعریف نشده است."))
    return ""


def ensure_expense_claim_types_fa() -> dict:
    """Translate core Expense Claim Types to Persian and add common travel-related types."""
    translations = {
        "Calls": "تماس و ارتباطات",
        "Food": "غذا و پذیرایی",
        "Medical": "هزینه درمانی",
        "Others": "سایر هزینه ها",
        "Travel": "سفر و ایاب و ذهاب",
    }

    required_types = [
        "اقامت و هتل",
        "بلیط هواپیما",
        "بلیط قطار",
        "بلیط اتوبوس",
        "تاکسی و حمل و نقل شهری",
        "سوخت خودرو",
        "عوارض و پارکینگ",
        "اینترنت و داده",
    ]

    template_accounts = {}
    travel_template = frappe.db.get_value("Expense Claim Type", "Travel", "name")
    template_docs = [travel_template] if travel_template else []

    if not template_docs:
        template_docs = [row.name for row in frappe.get_all("Expense Claim Type", fields=["name"], limit=20)]

    for docname in template_docs:
        if not docname or not frappe.db.exists("Expense Claim Type", docname):
            continue
        doc = frappe.get_doc("Expense Claim Type", docname)
        for row in doc.accounts or []:
            if row.company and row.default_account and row.company not in template_accounts:
                template_accounts[row.company] = row.default_account

    translated = []
    for docname, fa_title in translations.items():
        if not frappe.db.exists("Expense Claim Type", docname):
            continue
        current_title = frappe.db.get_value("Expense Claim Type", docname, "expense_type")
        if current_title != fa_title:
            frappe.db.set_value("Expense Claim Type", docname, "expense_type", fa_title)
            translated.append(docname)

    created = []
    for fa_title in required_types:
        if frappe.db.exists("Expense Claim Type", {"expense_type": fa_title}):
            continue

        doc = frappe.new_doc("Expense Claim Type")
        doc.expense_type = fa_title
        for company, account in template_accounts.items():
            doc.append(
                "accounts",
                {
                    "company": company,
                    "default_account": account,
                },
            )
        doc.insert(ignore_permissions=True)
        created.append(doc.name)

    return {
        "translated": translated,
        "created": created,
        "template_accounts": template_accounts,
    }


def apply_payload_to_doc(doc, data: dict, current_employee: frappe._dict):
    flow_type = normalize_flow_type(data.get("flow_type") or data.get("mission_flow_type") or doc.mission_flow_type)
    mission_type = normalize_mission_type(data.get("mission_type") or doc.mission_type)

    if doc.is_new():
        doc.travel_status = (
            "در انتظار تایید برنامه سفر" if flow_type == "برنامه‌ریزی‌شده" else "در حال انجام سفر"
        )

    doc.purpose_of_travel = get_default_purpose_of_travel()
    doc.mission_title = (data.get("title") or doc.mission_title or "").strip()
    doc.mission_destination = (data.get("destination") or doc.mission_destination or "").strip()
    doc.mission_purpose_text = (data.get("purpose") or doc.mission_purpose_text or "").strip()
    doc.mission_notes = (data.get("notes") or doc.mission_notes or "").strip()
    doc.description = doc.mission_notes

    doc.mission_flow_type = flow_type
    doc.mission_type = mission_type

    start_date = data.get("start_date") or doc.mission_start_date or nowdate()
    end_date = data.get("end_date") or doc.mission_end_date or start_date

    if mission_type == "ساعتی":
        hourly_date = data.get("hourly_date") or doc.mission_hourly_date or start_date
        doc.mission_hourly_date = hourly_date
        doc.mission_hourly_from_time = data.get("hourly_from_time") or doc.mission_hourly_from_time
        doc.mission_hourly_to_time = data.get("hourly_to_time") or doc.mission_hourly_to_time
        start_date = hourly_date
        end_date = hourly_date
    else:
        doc.mission_hourly_date = ""
        doc.mission_hourly_from_time = ""
        doc.mission_hourly_to_time = ""

    doc.mission_start_date = start_date
    doc.mission_end_date = end_date

    doc.travel_type = "Domestic"
    doc.travel_funding = "Require Full Funding"
    doc.requested_advance_amount = flt(data.get("mission_allowance") or doc.requested_advance_amount or 0)

    if not doc.supervisor_employee:
        doc.supervisor_employee = frappe.db.get_value("Employee", doc.employee, "reports_to")

    expenses = data.get("expenses")
    if isinstance(expenses, list):
        existing_costings = {}
        for row in doc.costings or []:
            key = row.expense_client_id or row.name
            if key:
                existing_costings[key] = row

        doc.set("costings", [])
        for index, entry in enumerate(expenses):
            amount = flt((entry or {}).get("amount"))
            description = ((entry or {}).get("description") or "").strip()
            category = (entry or {}).get("category")
            expense_id = ((entry or {}).get("id") or "").strip() or f"exp-{index + 1}"
            if amount <= 0 and not description and not category:
                continue

            previous = existing_costings.get(expense_id)
            expense_type = resolve_expense_claim_type(category, doc.company)
            costing = doc.append("costings", {})
            costing.expense_client_id = expense_id
            costing.expense_type = expense_type
            costing.expense_date = (entry or {}).get("date") or doc.mission_start_date or nowdate()
            costing.total_amount = amount
            costing.funded_amount = amount
            costing.sponsored_amount = 0
            costing.comments = description
            costing.receipt_file = (entry or {}).get("receipt_file") or (previous.receipt_file if previous else "")

    doc.mission_total_expense = sum(flt(row.total_amount) for row in (doc.costings or []))
    apply_settlement(doc)


def apply_settlement(doc):
    if normalize_status(doc.travel_status) != FINAL_APPROVED_STATUS:
        doc.settlement_type = ""
        doc.settlement_amount = 0
        doc.settlement_note = ""
        return

    requested = flt(doc.requested_advance_amount)
    total_expense = flt(doc.mission_total_expense)
    diff = total_expense - requested

    if diff > 0:
        doc.settlement_type = SETTLEMENT_TYPE_COMPANY_DEBT
        doc.settlement_amount = diff
        doc.settlement_note = _("شرکت بابت این ماموریت به کارمند {0} بدهکار است.").format(diff)
    elif diff < 0:
        doc.settlement_type = SETTLEMENT_TYPE_EMPLOYEE_DEBT
        doc.settlement_amount = abs(diff)
        doc.settlement_note = _("کارمند بابت این ماموریت به شرکت {0} بدهکار است.").format(abs(diff))
    else:
        doc.settlement_type = SETTLEMENT_TYPE_BALANCED
        doc.settlement_amount = 0
        doc.settlement_note = _("هزینه ماموریت با مبلغ دریافتی برابر است.")


def ensure_expense_claim_from_travel(travel_doc, supervisor_employee: frappe._dict) -> str:
    if travel_doc.linked_expense_claim and frappe.db.exists("Expense Claim", travel_doc.linked_expense_claim):
        return travel_doc.linked_expense_claim

    expenses = [row for row in (travel_doc.costings or []) if flt(row.total_amount) > 0]
    if not expenses:
        return ""

    payable_account = frappe.db.get_value(
        "Company", travel_doc.company, "default_expense_claim_payable_account"
    )
    if not payable_account:
        frappe.throw(
            _("برای شرکت {0} باید حساب پیش‌فرض پرداخت هزینه ماموریت تعریف شود.").format(travel_doc.company)
        )

    supervisor_user = frappe.db.get_value("Employee", supervisor_employee.name, "user_id") or frappe.session.user

    claim = frappe.new_doc("Expense Claim")
    claim.employee = travel_doc.employee
    claim.company = travel_doc.company
    claim.posting_date = nowdate()
    claim.expense_approver = supervisor_user
    claim.approval_status = "Approved"
    claim.payable_account = payable_account
    claim.remark = _("به‌صورت خودکار از درخواست سفر {0} ایجاد شد").format(travel_doc.name)
    if frappe.db.has_column("Expense Claim", "travel_request_ref"):
        claim.travel_request_ref = travel_doc.name

    for row in expenses:
        expense_type = resolve_expense_claim_type(row.expense_type, travel_doc.company)
        amount = flt(row.total_amount)
        claim.append(
            "expenses",
            {
                "expense_date": row.expense_date or travel_doc.mission_start_date or nowdate(),
                "expense_type": expense_type,
                "description": row.comments or travel_doc.mission_title,
                "amount": amount,
                "sanctioned_amount": amount,
            },
        )

    claim.flags.ignore_permissions = True
    claim.insert(ignore_permissions=True)
    claim.submit()
    return claim.name


def build_settlement_message(travel_doc) -> str:
    if normalize_status(travel_doc.travel_status) != FINAL_APPROVED_STATUS:
        return ""

    if travel_doc.settlement_note:
        return travel_doc.settlement_note

    settlement_type = (travel_doc.settlement_type or "").strip()
    amount = flt(travel_doc.settlement_amount)

    if settlement_type == SETTLEMENT_TYPE_COMPANY_DEBT:
        return _("شرکت بابت این ماموریت به کارمند {0} بدهکار است.").format(amount)
    if settlement_type == SETTLEMENT_TYPE_EMPLOYEE_DEBT:
        return _("کارمند بابت این ماموریت به شرکت {0} بدهکار است.").format(amount)
    if settlement_type == SETTLEMENT_TYPE_BALANCED:
        return _("هزینه ماموریت با مبلغ دریافتی برابر است.")

    return ""


def serialize_travel_request(travel_doc, current_employee: frappe._dict) -> dict:
    expenses = []
    total_expense = 0

    for row in (travel_doc.costings or []):
        amount = flt(row.total_amount)
        total_expense += amount
        receipt_file = row.receipt_file or ""
        receipt_file_url = ""
        if receipt_file:
            receipt_file_url = frappe.db.get_value("File", receipt_file, "file_url") or ""

        expenses.append(
            {
                "id": row.expense_client_id or row.name,
                "date": row.expense_date or travel_doc.mission_start_date or nowdate(),
                "category": row.expense_type,
                "description": row.comments or "",
                "amount": amount,
                "receipt_file": receipt_file,
                "receipt_file_url": receipt_file_url,
            }
        )

    status = normalize_status(travel_doc.travel_status)

    return {
        "id": travel_doc.name,
        "name": travel_doc.name,
        "doctype": "Travel Request",
        "title": travel_doc.mission_title or travel_doc.name,
        "destination": travel_doc.mission_destination or "",
        "purpose": travel_doc.mission_purpose_text or "",
        "notes": travel_doc.mission_notes or "",
        "flow_type": normalize_flow_type(travel_doc.mission_flow_type),
        "mission_type": normalize_mission_type(travel_doc.mission_type),
        "start_date": travel_doc.mission_start_date,
        "end_date": travel_doc.mission_end_date,
        "hourly_date": travel_doc.mission_hourly_date,
        "hourly_from_time": travel_doc.mission_hourly_from_time,
        "hourly_to_time": travel_doc.mission_hourly_to_time,
        "status": status,
        "mission_allowance": flt(travel_doc.requested_advance_amount),
        "total_expense": total_expense,
        "expenses": expenses,
        "employee": travel_doc.employee,
        "employee_name": travel_doc.employee_name,
        "supervisor_employee": travel_doc.supervisor_employee,
        "is_planned": normalize_flow_type(travel_doc.mission_flow_type) == "برنامه‌ریزی‌شده",
        "can_review": travel_doc.supervisor_employee == current_employee.name,
        "linked_expense_claim": travel_doc.linked_expense_claim,
        "settlement_type": travel_doc.settlement_type,
        "settlement_amount": flt(travel_doc.settlement_amount),
        "settlement_message": build_settlement_message(travel_doc),
        "created_at": travel_doc.creation,
        "updated_at": travel_doc.modified,
    }
