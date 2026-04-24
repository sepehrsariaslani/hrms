import json
import re

import frappe
from frappe import _
from frappe.query_builder import Order
from frappe.query_builder.functions import Sum
from frappe.utils import cint, flt, getdate, nowdate
from frappe.utils.file_manager import save_file

ALLOWED_PARTY_TYPES = {"Supplier", "Employee"}
SUPPORTED_PAYMENT_TYPES = {"Pay", "Internal Transfer"}
SUPPORTED_ENTRY_DOCTYPES = {"Payment Entry", "Journal Entry"}


@frappe.whitelist()
def get_imprest_context() -> dict:
    ensure_imprest_setup()
    employee = get_current_employee()
    allowed_accounts = get_allowed_accounts(employee.name)
    has_imprest = get_has_imprest(employee.name, allowed_accounts)

    default_account = next((row.account for row in allowed_accounts if cint(row.is_default)), None)
    if not default_account and allowed_accounts:
        default_account = allowed_accounts[0].account

    return {
        "employee": employee,
        "has_imprest": has_imprest,
        "default_account": default_account,
        "allowed_accounts": allowed_accounts,
        "company": employee.company,
    }


@frappe.whitelist()
def get_imprest_dashboard_stats(
    from_date: str | None = None,
    to_date: str | None = None,
    account: str | None = None,
    accounts: str | list[str] | None = None,
) -> dict:
    ensure_imprest_setup()
    employee = get_current_employee()
    allowed_accounts = get_allowed_accounts(employee.name)
    has_imprest = get_has_imprest(employee.name, allowed_accounts)

    if not has_imprest:
        return {
            "current_balance": 0,
            "total_incoming": 0,
            "total_outgoing": 0,
            "total_transfer": 0,
            "period_net": 0,
            "transaction_count": 0,
            "recent_transactions": [],
        }

    allowed_account_names = [row.account for row in allowed_accounts if row.account]
    account_filters = normalize_requested_accounts(
        allowed_accounts=allowed_account_names,
        account=account,
        accounts=accounts,
    )

    rows = get_imprest_rows(
        employee=employee.name,
        allowed_accounts=allowed_account_names,
        from_date=from_date,
        to_date=to_date,
        account_filters=account_filters,
        limit=200,
    )

    account_balances = get_account_balances(allowed_account_names)
    if account_filters:
        current_balance = sum(flt(account_balances.get(acc, 0)) for acc in account_filters)
    else:
        current_balance = sum(flt(account_balances.get(acc, 0)) for acc in allowed_account_names)

    allowed_set = set(allowed_account_names)
    total_incoming = 0
    total_outgoing = 0
    total_transfer = 0
    for row in rows:
        transaction_type = classify_transaction(row.payment_type, row.paid_from, row.paid_to, allowed_set)
        if transaction_type == "incoming":
            total_incoming += get_row_amount(row, transaction_type)
        elif transaction_type == "outgoing":
            total_outgoing += get_row_amount(row, transaction_type)
        else:
            total_transfer += get_row_amount(row, transaction_type)

    recent_transactions = [serialize_row(row, allowed_set, employee.name) for row in rows[:30]]

    return {
        "current_balance": current_balance,
        "total_incoming": total_incoming,
        "total_outgoing": total_outgoing,
        "total_transfer": total_transfer,
        "period_net": total_incoming - total_outgoing,
        "transaction_count": len(rows),
        "recent_transactions": recent_transactions,
    }


@frappe.whitelist()
def get_imprest_calendar_transactions(
    from_date: str,
    to_date: str,
    account: str | None = None,
    accounts: str | list[str] | None = None,
) -> list[dict]:
    ensure_imprest_setup()
    employee = get_current_employee()
    allowed_accounts = get_allowed_accounts(employee.name)
    has_imprest = get_has_imprest(employee.name, allowed_accounts)
    if not has_imprest:
        return []

    allowed_account_names = [row.account for row in allowed_accounts if row.account]
    account_filters = normalize_requested_accounts(
        allowed_accounts=allowed_account_names,
        account=account,
        accounts=accounts,
    )

    rows = get_imprest_rows(
        employee=employee.name,
        allowed_accounts=allowed_account_names,
        from_date=from_date,
        to_date=to_date,
        account_filters=account_filters,
        limit=800,
    )
    allowed_set = set(allowed_account_names)
    return [serialize_row(row, allowed_set, employee.name) for row in rows]


@frappe.whitelist()
def get_imprest_payment_entry_for_edit(name: str, doctype: str | None = None) -> dict:
    ensure_imprest_setup()
    employee = get_current_employee()
    allowed_accounts = get_allowed_accounts(employee.name)
    allowed_set = {acc.account for acc in allowed_accounts if acc.account}

    row = get_imprest_row(name, doctype)
    validate_imprest_entry_access(row, employee.name, allowed_set, require_owner=True)

    data = serialize_row(row, allowed_set, employee.name)
    data["attachments"] = get_attachments(name, data["doctype"])
    return data


@frappe.whitelist()
def get_imprest_transaction_detail(name: str, doctype: str | None = None) -> dict:
    ensure_imprest_setup()
    employee = get_current_employee()
    allowed_accounts = get_allowed_accounts(employee.name)
    allowed_set = {acc.account for acc in allowed_accounts if acc.account}

    row = get_imprest_row(name, doctype)
    validate_imprest_entry_access(row, employee.name, allowed_set, require_owner=False)

    data = serialize_row(row, allowed_set, employee.name)
    data["attachments"] = get_attachments(name, data["doctype"])
    data["gl_entries"] = get_gl_entries(data["doctype"], name)
    return data


@frappe.whitelist()
def get_company_cash_bank_accounts(search_text: str | None = None, limit: int | None = 200) -> list[dict]:
    ensure_imprest_setup()
    employee = get_current_employee()
    return get_company_accounts_for_employee(
        employee.company,
        search_text=search_text,
        limit=limit,
        account_types=["Cash", "Bank"],
    )


@frappe.whitelist()
def get_company_accounts(search_text: str | None = None, limit: int | None = 200) -> list[dict]:
    ensure_imprest_setup()
    employee = get_current_employee()
    return get_company_accounts_for_employee(employee.company, search_text=search_text, limit=limit)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_imprest_employees(
    doctype: str,
    txt: str,
    searchfield: str,
    start: int,
    page_len: int,
    filters: dict | str | None = None,
):
    ensure_imprest_setup()
    employee = get_current_employee()
    allowed_accounts = get_allowed_accounts(employee.name)
    if not get_has_imprest(employee.name, allowed_accounts):
        return []

    start = cint(start) or 0
    page_len = min(cint(page_len) or 20, 50)
    search_text = (txt or "").strip()
    like_text = f"%{search_text}%"

    return frappe.db.sql(
        """
        select
            name,
            employee_name
        from `tabEmployee`
        where status = 'Active'
          and company = %s
          and (%s = '' or name like %s or employee_name like %s)
        order by employee_name asc, name asc
        limit %s offset %s
        """,
        (
            employee.company,
            search_text,
            like_text,
            like_text,
            page_len,
            start,
        ),
    )


@frappe.whitelist()
def attach_imprest_image(
    name: str,
    file_name: str,
    file_content: str,
    doctype: str | None = None,
) -> dict:
    ensure_imprest_setup()
    employee = get_current_employee()
    allowed_accounts = get_allowed_accounts(employee.name)
    allowed_set = {acc.account for acc in allowed_accounts if acc.account}

    row = get_imprest_row(name, doctype)
    validate_imprest_entry_access(row, employee.name, allowed_set)

    if not file_name:
        frappe.throw(_("File name is required."))
    if not file_content:
        frappe.throw(_("File content is required."))

    base64_content = normalize_data_url(file_content)
    estimated_size = int(len(base64_content) * 0.75)
    if estimated_size > 5 * 1024 * 1024:
        frappe.throw(_("Each image must be smaller than 5 MB."))

    target_doctype = resolve_entry_doctype(name, doctype)
    original_max_file_size = frappe.conf.get("max_file_size")
    restore_max_file_size = False
    if isinstance(original_max_file_size, str):
        frappe.conf.max_file_size = parse_file_size_to_bytes(original_max_file_size)
        restore_max_file_size = True

    try:
        file_doc = save_file(
            fname=file_name,
            content=base64_content,
            dt=target_doctype,
            dn=name,
            folder="Home/Attachments",
            decode=True,
            is_private=1,
        )
    finally:
        if restore_max_file_size:
            frappe.conf.max_file_size = original_max_file_size

    return {
        "name": file_doc.name,
        "file_name": file_doc.file_name,
        "file_url": file_doc.file_url,
        "is_private": cint(file_doc.is_private),
    }


@frappe.whitelist()
def create_imprest_payment_entry(payload: str | dict | None = None) -> dict:
    ensure_imprest_setup()
    employee = get_current_employee()
    allowed_accounts = get_allowed_accounts(employee.name)
    allowed_account_names = [row.account for row in allowed_accounts if row.account]

    if not get_has_imprest(employee.name, allowed_accounts):
        frappe.throw(_("Imprest access is not enabled for this employee."), frappe.PermissionError)

    data = parse_payload(payload)
    doc = build_imprest_entry_doc(data, employee, allowed_account_names)
    doc.insert(ignore_permissions=True)
    doc.submit()

    entry = serialize_doc(doc, set(allowed_account_names))
    return {
        "entry": entry,
        "payment_entry": entry if doc.doctype == "Payment Entry" else None,
        "journal_entry": entry if doc.doctype == "Journal Entry" else None,
    }


@frappe.whitelist()
def update_imprest_payment_entry(name: str, payload: str | dict | None = None) -> dict:
    ensure_imprest_setup()
    employee = get_current_employee()
    allowed_accounts = get_allowed_accounts(employee.name)
    allowed_account_names = [row.account for row in allowed_accounts if row.account]
    allowed_set = set(allowed_account_names)

    data = parse_payload(payload)
    existing_doctype = resolve_entry_doctype(name, data.get("doctype"))

    existing_row = get_imprest_row(name, existing_doctype)
    validate_imprest_entry_access(existing_row, employee.name, allowed_set, require_owner=True)

    existing_doc = frappe.get_doc(existing_doctype, name)
    if existing_doc.docstatus != 1:
        frappe.throw(_("Only submitted documents can be edited from mobile app."))

    existing_doc.cancel()

    doc = build_imprest_entry_doc(data, employee, allowed_account_names)
    doc.insert(ignore_permissions=True)
    doc.submit()

    entry = serialize_doc(doc, allowed_set)
    return {
        "updated_from": name,
        "updated_from_doctype": existing_doctype,
        "entry": entry,
        "payment_entry": entry if doc.doctype == "Payment Entry" else None,
        "journal_entry": entry if doc.doctype == "Journal Entry" else None,
    }


@frappe.whitelist()
def cancel_imprest_entry(name: str, doctype: str | None = None) -> dict:
    ensure_imprest_setup()
    employee = get_current_employee()
    allowed_accounts = get_allowed_accounts(employee.name)
    allowed_set = {acc.account for acc in allowed_accounts if acc.account}

    row = get_imprest_row(name, doctype)
    validate_imprest_entry_access(row, employee.name, allowed_set, require_owner=True)

    entry_doctype = resolve_entry_doctype(name, doctype)
    doc = frappe.get_doc(entry_doctype, name)

    if doc.docstatus == 2:
        return {
            "name": doc.name,
            "doctype": entry_doctype,
            "docstatus": doc.docstatus,
            "cancelled": True,
            "already_cancelled": True,
        }

    if doc.docstatus != 1:
        frappe.throw(_("Only submitted documents can be cancelled from mobile app."))

    doc.cancel()
    return {
        "name": doc.name,
        "doctype": entry_doctype,
        "docstatus": doc.docstatus,
        "cancelled": True,
    }


def ensure_imprest_setup():
    if not frappe.db.exists("DocType", "Employee Imprest Account"):
        frappe.throw(_("Employee imprest setup is not installed yet."))

    if not frappe.db.has_column("Payment Entry", "imprest_employee"):
        frappe.throw(_("Payment Entry is missing imprest fields. Please run migrations."))

    if not frappe.db.has_column("Journal Entry", "imprest_employee"):
        frappe.throw(_("Journal Entry is missing imprest fields. Please run migrations."))


def parse_payload(payload: str | dict | None = None) -> dict:
    if not payload:
        return {}
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError as error:
            frappe.throw(_("Invalid payload: {0}").format(error))
    frappe.throw(_("Invalid payload format."))
    return {}


def get_current_employee() -> frappe._dict:
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user, "status": "Active"},
        ["name", "employee_name", "company", "user_id"],
        as_dict=True,
    )
    if not employee:
        frappe.throw(_("You are not linked to an active employee."), frappe.PermissionError)
    return employee


def get_has_imprest(employee: str, allowed_accounts: list[frappe._dict]) -> bool:
    if frappe.db.has_column("Employee", "has_imprest"):
        return bool(cint(frappe.db.get_value("Employee", employee, "has_imprest"))) or bool(
            allowed_accounts
        )
    return bool(allowed_accounts)


def get_allowed_accounts(employee: str) -> list[frappe._dict]:
    if not frappe.db.exists("DocType", "Employee Imprest Account"):
        return []

    rows = frappe.get_all(
        "Employee Imprest Account",
        filters={
            "parent": employee,
            "parenttype": "Employee",
            "is_active": 1,
        },
        fields=["account", "is_default", "idx"],
        order_by="idx asc",
        limit=0,
    )
    account_names = [row.account for row in rows if row.account]
    if not account_names:
        return []

    accounts = frappe.get_all(
        "Account",
        filters={"name": ["in", account_names]},
        fields=["name", "account_name", "company", "account_currency"],
        limit=0,
    )
    account_by_name = {row.name: row for row in accounts}
    balances = get_account_balances(account_names)

    result = []
    for row in rows:
        account_meta = account_by_name.get(row.account)
        if not account_meta:
            continue
        result.append(
            frappe._dict(
                {
                    "account": row.account,
                    "account_name": account_meta.account_name,
                    "company": account_meta.company,
                    "account_currency": account_meta.account_currency,
                    "is_default": cint(row.is_default),
                    "balance": flt(balances.get(row.account, 0)),
                }
            )
        )
    return result


def get_account_balances(account_names: list[str]) -> dict[str, float]:
    if not account_names:
        return {}

    GL = frappe.qb.DocType("GL Entry")
    rows = (
        frappe.qb.from_(GL)
        .select(GL.account, Sum(GL.debit - GL.credit).as_("balance"))
        .where((GL.account.isin(account_names)) & (GL.is_cancelled == 0))
        .groupby(GL.account)
    ).run(as_dict=True)

    return {row.account: flt(row.balance) for row in rows}


def validate_account_filter(account: str | None, allowed_accounts: list[str]) -> None:
    if account and account not in allowed_accounts:
        frappe.throw(_("Selected account is not allowed for this employee."), frappe.PermissionError)


def normalize_requested_accounts(
    allowed_accounts: list[str],
    account: str | None = None,
    accounts: str | list[str] | None = None,
) -> list[str] | None:
    requested: list[str] = []

    if accounts not in (None, ""):
        parsed = accounts
        if isinstance(accounts, str):
            raw = accounts.strip()
            if raw:
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = [part.strip() for part in raw.split(",") if part.strip()]
            else:
                parsed = []

        if isinstance(parsed, str):
            parsed = [parsed]

        if isinstance(parsed, (list, tuple, set)):
            requested = [str(acc).strip() for acc in parsed if str(acc).strip()]

    if not requested and account:
        requested = [str(account).strip()]

    deduped = []
    seen = set()
    for acc in requested:
        if acc and acc not in seen:
            deduped.append(acc)
            seen.add(acc)

    for acc in deduped:
        if acc not in allowed_accounts:
            frappe.throw(_("Selected account is not allowed for this employee."), frappe.PermissionError)

    return deduped or None


def get_company_accounts_for_employee(
    company: str,
    search_text: str | None = None,
    limit: int | None = 200,
    account_types: list[str] | None = None,
) -> list[dict]:
    limit = cint(limit) or 200
    limit = min(limit, 500)

    Account = frappe.qb.DocType("Account")
    condition = (Account.company == company) & (Account.is_group == 0)

    if account_types:
        condition = condition & Account.account_type.isin(account_types)

    if search_text:
        like_txt = f"%{search_text}%"
        condition = condition & ((Account.name.like(like_txt)) | (Account.account_name.like(like_txt)))

    rows = (
        frappe.qb.from_(Account)
        .select(
            Account.name,
            Account.account_name,
            Account.account_type,
            Account.root_type,
            Account.account_currency,
        )
        .where(condition)
        .orderby(Account.account_name, order=Order.asc)
        .limit(limit)
    ).run(as_dict=True)

    return rows


def get_imprest_rows(
    employee: str,
    allowed_accounts: list[str],
    from_date: str | None = None,
    to_date: str | None = None,
    account_filters: list[str] | None = None,
    limit: int | None = None,
) -> list[frappe._dict]:
    payment_rows = get_payment_rows(
        employee=employee,
        allowed_accounts=allowed_accounts,
        from_date=from_date,
        to_date=to_date,
        account_filters=account_filters,
        limit=limit,
    )
    journal_rows = get_journal_rows(
        employee=employee,
        allowed_accounts=allowed_accounts,
        from_date=from_date,
        to_date=to_date,
        account_filters=account_filters,
        limit=limit,
    )

    rows = payment_rows + journal_rows
    rows.sort(key=row_sort_key, reverse=True)
    return rows[:limit] if limit else rows


def row_sort_key(row: frappe._dict) -> tuple:
    posting_date = getdate(row.posting_date) if row.posting_date else getdate("1900-01-01")
    modified = str(row.modified or "")
    return posting_date, modified, row.name


def get_payment_rows(
    employee: str,
    allowed_accounts: list[str],
    from_date: str | None = None,
    to_date: str | None = None,
    account_filters: list[str] | None = None,
    limit: int | None = None,
) -> list[frappe._dict]:
    if not allowed_accounts:
        return []

    PE = frappe.qb.DocType("Payment Entry")
    condition = (PE.docstatus == 1) & (
        (PE.paid_from.isin(allowed_accounts)) | (PE.paid_to.isin(allowed_accounts))
    )

    if account_filters:
        condition = condition & ((PE.paid_from.isin(account_filters)) | (PE.paid_to.isin(account_filters)))
    if from_date:
        condition = condition & (PE.posting_date >= getdate(from_date))
    if to_date:
        condition = condition & (PE.posting_date <= getdate(to_date))

    query = (
        frappe.qb.from_(PE)
        .select(
            PE.name,
            PE.docstatus,
            PE.payment_type,
            PE.posting_date,
            PE.party_type,
            PE.party,
            PE.party_name,
            PE.paid_amount,
            PE.received_amount,
            PE.paid_from,
            PE.paid_to,
            PE.mode_of_payment,
            PE.reference_no,
            PE.remarks,
            PE.imprest_employee,
            PE.modified,
        )
        .where(condition)
        .orderby(PE.posting_date, order=Order.desc)
        .orderby(PE.modified, order=Order.desc)
    )

    if limit:
        query = query.limit(limit)

    rows = query.run(as_dict=True)
    for row in rows:
        row.doctype = "Payment Entry"
    return rows


def get_payment_row(name: str) -> frappe._dict:
    PE = frappe.qb.DocType("Payment Entry")
    rows = (
        frappe.qb.from_(PE)
        .select(
            PE.name,
            PE.docstatus,
            PE.payment_type,
            PE.posting_date,
            PE.party_type,
            PE.party,
            PE.party_name,
            PE.paid_amount,
            PE.received_amount,
            PE.paid_from,
            PE.paid_to,
            PE.mode_of_payment,
            PE.reference_no,
            PE.remarks,
            PE.imprest_employee,
            PE.modified,
        )
        .where(PE.name == name)
    ).run(as_dict=True)

    if not rows:
        frappe.throw(_("Payment Entry not found."))
    row = rows[0]
    row.doctype = "Payment Entry"
    return row


def get_journal_rows(
    employee: str,
    allowed_accounts: list[str],
    from_date: str | None = None,
    to_date: str | None = None,
    account_filters: list[str] | None = None,
    limit: int | None = None,
) -> list[frappe._dict]:
    if not allowed_accounts:
        return []

    allowed_placeholders = ", ".join(["%s"] * len(allowed_accounts))
    conditions = [
        "je.docstatus = 1",
        f"(credit.account in ({allowed_placeholders}) or debit.account in ({allowed_placeholders}))",
    ]
    params = [*allowed_accounts, *allowed_accounts]

    if account_filters:
        account_placeholders = ", ".join(["%s"] * len(account_filters))
        conditions.append(
            f"(credit.account in ({account_placeholders}) or debit.account in ({account_placeholders}))"
        )
        params.extend([*account_filters, *account_filters])
    if from_date:
        conditions.append("je.posting_date >= %s")
        params.append(getdate(from_date))
    if to_date:
        conditions.append("je.posting_date <= %s")
        params.append(getdate(to_date))

    limit_clause = ""
    if limit:
        limit_clause = " limit %s"
        params.append(cint(limit))

    rows = frappe.db.sql(
        f"""
        select
            je.name,
            je.docstatus,
            'Pay' as payment_type,
            je.posting_date,
            'Account' as party_type,
            debit.account as party,
            debit_account.account_name as party_name,
            ifnull(credit.credit_in_account_currency, je.total_credit) as paid_amount,
            ifnull(debit.debit_in_account_currency, je.total_debit) as received_amount,
            credit.account as paid_from,
            debit.account as paid_to,
            null as mode_of_payment,
            je.cheque_no as reference_no,
            je.user_remark as remarks,
            je.imprest_employee,
            je.modified
        from `tabJournal Entry` je
        left join `tabJournal Entry Account` credit
            on credit.parent = je.name
            and credit.parenttype = 'Journal Entry'
            and credit.docstatus < 2
            and credit.credit_in_account_currency > 0
        left join `tabJournal Entry Account` debit
            on debit.parent = je.name
            and debit.parenttype = 'Journal Entry'
            and debit.docstatus < 2
            and debit.debit_in_account_currency > 0
        left join `tabAccount` debit_account on debit_account.name = debit.account
        where {' and '.join(conditions)}
        order by je.posting_date desc, je.modified desc
        {limit_clause}
        """,
        tuple(params),
        as_dict=True,
    )

    for row in rows:
        row.doctype = "Journal Entry"
    return rows


def get_journal_row(name: str) -> frappe._dict:
    rows = frappe.db.sql(
        """
        select
            je.name,
            je.docstatus,
            'Pay' as payment_type,
            je.posting_date,
            'Account' as party_type,
            debit.account as party,
            debit_account.account_name as party_name,
            ifnull(credit.credit_in_account_currency, je.total_credit) as paid_amount,
            ifnull(debit.debit_in_account_currency, je.total_debit) as received_amount,
            credit.account as paid_from,
            debit.account as paid_to,
            null as mode_of_payment,
            je.cheque_no as reference_no,
            je.user_remark as remarks,
            je.imprest_employee,
            je.modified
        from `tabJournal Entry` je
        left join `tabJournal Entry Account` credit
            on credit.parent = je.name
            and credit.parenttype = 'Journal Entry'
            and credit.docstatus < 2
            and credit.credit_in_account_currency > 0
        left join `tabJournal Entry Account` debit
            on debit.parent = je.name
            and debit.parenttype = 'Journal Entry'
            and debit.docstatus < 2
            and debit.debit_in_account_currency > 0
        left join `tabAccount` debit_account on debit_account.name = debit.account
        where je.name = %s
        limit 1
        """,
        (name,),
        as_dict=True,
    )

    if not rows:
        frappe.throw(_("Journal Entry not found."))

    row = rows[0]
    row.doctype = "Journal Entry"
    return row


def resolve_entry_doctype(name: str, doctype: str | None = None) -> str:
    if doctype in SUPPORTED_ENTRY_DOCTYPES and frappe.db.exists(doctype, name):
        return doctype

    if frappe.db.exists("Payment Entry", name):
        return "Payment Entry"

    if frappe.db.exists("Journal Entry", name):
        return "Journal Entry"

    frappe.throw(_("Transaction not found."))
    return "Payment Entry"


def get_imprest_row(name: str, doctype: str | None = None) -> frappe._dict:
    entry_doctype = resolve_entry_doctype(name, doctype)
    if entry_doctype == "Payment Entry":
        return get_payment_row(name)
    if entry_doctype == "Journal Entry":
        return get_journal_row(name)
    frappe.throw(_("Unsupported transaction type."))
    return frappe._dict()


def validate_imprest_entry_access(
    row,
    employee: str,
    allowed_accounts: set[str],
    require_owner: bool = True,
):
    if require_owner and row.imprest_employee != employee:
        frappe.throw(_("You are not allowed to access this transaction."), frappe.PermissionError)

    entry_accounts = {row.paid_from, row.paid_to}
    entry_accounts = {account for account in entry_accounts if account}
    if not entry_accounts.intersection(allowed_accounts):
        frappe.throw(_("You are not allowed to access this account transaction."), frappe.PermissionError)


def build_imprest_entry_doc(data: dict, employee: frappe._dict, allowed_accounts: list[str]):
    if is_account_mode_payment(data):
        return build_journal_entry_doc(data, employee, allowed_accounts)
    return build_payment_entry_doc(data, employee, allowed_accounts)


def is_account_mode_payment(data: dict) -> bool:
    return data.get("payment_type") == "Pay" and data.get("party_type") == "Account"


def build_payment_entry_doc(data: dict, employee: frappe._dict, allowed_accounts: list[str]):
    allowed_set = set(allowed_accounts)
    payment_type = data.get("payment_type")
    if payment_type not in SUPPORTED_PAYMENT_TYPES:
        frappe.throw(_("Only Pay and Internal Transfer are allowed in imprest quick entry."))

    amount = flt(data.get("amount"))
    if amount <= 0:
        frappe.throw(_("Amount must be greater than zero."))

    paid_from = data.get("paid_from")
    if not paid_from or paid_from not in allowed_set:
        frappe.throw(_("Selected source account is not allowed."), frappe.PermissionError)
    validate_account_company(paid_from, employee.company)

    posting_date = getdate(data.get("posting_date") or nowdate())

    doc = frappe.new_doc("Payment Entry")
    doc.payment_type = payment_type
    doc.company = employee.company
    doc.posting_date = posting_date
    doc.paid_from = paid_from
    doc.paid_from_account_currency = frappe.db.get_value("Account", paid_from, "account_currency")
    doc.paid_amount = amount
    doc.imprest_employee = employee.name
    doc.mode_of_payment = data.get("mode_of_payment") or None
    doc.reference_no = data.get("reference_no") or None
    doc.reference_date = posting_date if doc.reference_no else None
    doc.remarks = data.get("remarks") or _("Imprest quick entry")

    if payment_type == "Internal Transfer":
        paid_to = data.get("paid_to")
        if not paid_to:
            frappe.throw(_("Destination account is required for transfer."))
        if not frappe.db.exists("Account", paid_to):
            frappe.throw(_("Selected destination account does not exist."))
        if paid_to == paid_from:
            frappe.throw(_("Source and destination accounts cannot be the same."))
        validate_account_company(paid_to, employee.company)
        validate_cash_bank_account(paid_to)

        doc.paid_to = paid_to
        doc.paid_to_account_currency = frappe.db.get_value("Account", paid_to, "account_currency")
        doc.received_amount = amount
    else:
        party_type = data.get("party_type")
        party = data.get("party")
        if party_type not in ALLOWED_PARTY_TYPES:
            frappe.throw(_("Party type is invalid."))
        if not party:
            frappe.throw(_("Party is required for payment."))
        if not frappe.db.exists(party_type, party):
            frappe.throw(_("Selected party does not exist."))

        doc.party_type = party_type
        doc.party = party
        doc.received_amount = amount
        doc.setup_party_account_field()

    doc.set_missing_values()
    doc.set_amounts()
    doc.flags.ignore_permissions = True
    return doc


def build_journal_entry_doc(data: dict, employee: frappe._dict, allowed_accounts: list[str]):
    allowed_set = set(allowed_accounts)
    amount = flt(data.get("amount"))
    if amount <= 0:
        frappe.throw(_("Amount must be greater than zero."))

    paid_from = data.get("paid_from")
    if not paid_from or paid_from not in allowed_set:
        frappe.throw(_("Selected source account is not allowed."), frappe.PermissionError)

    paid_to = data.get("party") or data.get("paid_to")
    if not paid_to:
        frappe.throw(_("Destination account is required for account payment."))
    if not frappe.db.exists("Account", paid_to):
        frappe.throw(_("Selected destination account does not exist."))
    if paid_to == paid_from:
        frappe.throw(_("Source and destination accounts cannot be the same."))

    posting_date = getdate(data.get("posting_date") or nowdate())

    validate_account_company(paid_from, employee.company)
    validate_account_company(paid_to, employee.company)
    validate_leaf_account(paid_to)

    company_currency = frappe.get_cached_value("Company", employee.company, "default_currency")
    validate_same_currency_account(paid_from, company_currency)
    validate_same_currency_account(paid_to, company_currency)

    doc = frappe.new_doc("Journal Entry")
    doc.company = employee.company
    doc.posting_date = posting_date
    doc.user_remark = data.get("remarks") or _("Imprest quick entry - account payment")
    doc.imprest_employee = employee.name
    doc.cheque_no = data.get("reference_no") or None
    if doc.cheque_no:
        doc.cheque_date = posting_date

    default_cost_center = frappe.get_cached_value("Company", employee.company, "cost_center")

    debit_row = {
        "account": paid_to,
        "debit_in_account_currency": amount,
        "credit_in_account_currency": 0,
    }
    credit_row = {
        "account": paid_from,
        "debit_in_account_currency": 0,
        "credit_in_account_currency": amount,
    }

    if default_cost_center:
        debit_row["cost_center"] = default_cost_center
        credit_row["cost_center"] = default_cost_center

    doc.append("accounts", debit_row)
    doc.append("accounts", credit_row)
    doc.flags.ignore_permissions = True
    return doc


def serialize_doc(doc, allowed_accounts: set[str] | None = None) -> dict:
    if doc.doctype == "Payment Entry":
        row = frappe._dict(
            {
                "name": doc.name,
                "doctype": "Payment Entry",
                "docstatus": doc.docstatus,
                "payment_type": doc.payment_type,
                "posting_date": doc.posting_date,
                "party_type": doc.party_type,
                "party": doc.party,
                "party_name": doc.party_name,
                "paid_amount": doc.paid_amount,
                "received_amount": doc.received_amount,
                "paid_from": doc.paid_from,
                "paid_to": doc.paid_to,
                "mode_of_payment": doc.mode_of_payment,
                "reference_no": doc.reference_no,
                "remarks": doc.remarks,
                "modified": doc.modified,
            }
        )
    elif doc.doctype == "Journal Entry":
        paid_from = None
        paid_to = None
        paid_amount = 0
        received_amount = 0
        for entry in doc.accounts:
            if flt(entry.credit_in_account_currency) > 0 and not paid_from:
                paid_from = entry.account
                paid_amount = flt(entry.credit_in_account_currency)
            if flt(entry.debit_in_account_currency) > 0 and not paid_to:
                paid_to = entry.account
                received_amount = flt(entry.debit_in_account_currency)

        row = frappe._dict(
            {
                "name": doc.name,
                "doctype": "Journal Entry",
                "docstatus": doc.docstatus,
                "payment_type": "Pay",
                "posting_date": doc.posting_date,
                "party_type": "Account",
                "party": paid_to,
                "party_name": get_account_name(paid_to),
                "paid_amount": paid_amount,
                "received_amount": received_amount,
                "paid_from": paid_from,
                "paid_to": paid_to,
                "mode_of_payment": None,
                "reference_no": doc.cheque_no,
                "remarks": doc.user_remark,
                "modified": doc.modified,
            }
        )
    else:
        frappe.throw(_("Unsupported transaction type."))

    effective_allowed = allowed_accounts or {row.paid_from, row.paid_to}
    employee_name = getattr(doc, "imprest_employee", None)
    return serialize_row(row, set(effective_allowed), employee_name)


def get_account_name(account: str | None) -> str | None:
    if not account:
        return None
    return frappe.db.get_value("Account", account, "account_name") or account


def validate_account_company(account: str, company: str):
    account_company = frappe.db.get_value("Account", account, "company")
    if account_company and account_company != company:
        frappe.throw(_("Selected account does not belong to employee company."), frappe.PermissionError)


def validate_leaf_account(account: str):
    is_group = cint(frappe.db.get_value("Account", account, "is_group"))
    if is_group:
        frappe.throw(_("Please select a ledger account, not an account group."))


def validate_same_currency_account(account: str, company_currency: str):
    account_currency = frappe.db.get_value("Account", account, "account_currency")
    if account_currency and account_currency != company_currency:
        frappe.throw(
            _("Account payment from mobile currently supports company currency accounts only."),
            frappe.ValidationError,
        )


def validate_cash_bank_account(account: str):
    account_type = frappe.db.get_value("Account", account, "account_type")
    if account_type not in {"Cash", "Bank"}:
        frappe.throw(_("Destination account must be a Cash/Bank account."))


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


def classify_transaction(
    payment_type: str,
    paid_from: str | None,
    paid_to: str | None,
    allowed_accounts: set[str],
):
    from_allowed = bool(paid_from and paid_from in allowed_accounts)
    to_allowed = bool(paid_to and paid_to in allowed_accounts)

    # Determine direction based on account activity first so Journal Entries and
    # cross-account rows are classified correctly for the employee's imprest accounts.
    if from_allowed and to_allowed:
        return "transfer"
    if from_allowed and not to_allowed:
        return "outgoing"
    if to_allowed and not from_allowed:
        return "incoming"

    if payment_type == "Receive":
        return "incoming"
    if payment_type == "Pay":
        return "outgoing"

    if payment_type == "Internal Transfer":
        if to_allowed:
            return "incoming"
        if from_allowed:
            return "outgoing"
    return "transfer"


def get_row_amount(row, transaction_type: str) -> float:
    if transaction_type == "incoming":
        return flt(row.received_amount or row.paid_amount)
    if transaction_type == "outgoing":
        return flt(row.paid_amount or row.received_amount)
    return flt(row.paid_amount or row.received_amount)


def serialize_row(row, allowed_accounts: set[str], employee: str | None = None) -> dict:
    transaction_type = classify_transaction(row.payment_type, row.paid_from, row.paid_to, allowed_accounts)
    amount = get_row_amount(row, transaction_type)
    return {
        "name": row.name,
        "doctype": row.doctype,
        "voucher_type": row.doctype,
        "voucher_no": row.name,
        "docstatus": row.docstatus,
        "payment_type": row.payment_type,
        "posting_date": str(row.posting_date),
        "party_type": row.party_type,
        "party": row.party,
        "party_name": row.party_name,
        "paid_amount": flt(row.paid_amount),
        "received_amount": flt(row.received_amount),
        "amount": amount,
        "paid_from": row.paid_from,
        "paid_to": row.paid_to,
        "mode_of_payment": row.mode_of_payment,
        "reference_no": row.reference_no,
        "remarks": row.remarks,
        "transaction_type": transaction_type,
        "is_receive": transaction_type == "incoming",
        "is_pay": transaction_type == "outgoing",
        "is_transfer": transaction_type == "transfer",
        "imprest_employee": row.imprest_employee,
        "can_edit": bool(employee and row.imprest_employee == employee),
    }


def get_attachments(docname: str, doctype: str = "Payment Entry") -> list[dict]:
    files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
            "is_folder": 0,
        },
        fields=["name", "file_name", "file_url", "is_private", "creation"],
        order_by="creation desc",
        limit=0,
    )
    return files


def get_gl_entries(doctype: str, docname: str) -> list[dict]:
    entries = frappe.get_all(
        "GL Entry",
        filters={
            "voucher_type": doctype,
            "voucher_no": docname,
            "is_cancelled": 0,
        },
        fields=[
            "name",
            "account",
            "debit",
            "credit",
            "party_type",
            "party",
            "remarks",
            "posting_date",
        ],
        order_by="debit desc, credit desc, creation asc",
        limit=0,
    )

    if not entries:
        return []

    account_names = {entry.account for entry in entries if entry.account}
    account_map = {}
    if account_names:
        accounts = frappe.get_all(
            "Account",
            filters={"name": ["in", list(account_names)]},
            fields=["name", "account_name"],
            limit=0,
        )
        account_map = {acc.name: acc.account_name for acc in accounts}

    for entry in entries:
        entry["account_name"] = account_map.get(entry.account) or entry.account
    return entries
