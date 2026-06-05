import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(
        {
            "Journal Entry": [
                {
                    "fieldname": "imprest_employee",
                    "fieldtype": "Link",
                    "label": "Imprest Employee",
                    "options": "Employee",
                    "insert_after": "finance_book",
                    "in_list_view": 1,
                    "in_standard_filter": 1,
                }
            ]
        },
        ignore_validate=True,
        update=True,
    )

    if not frappe.db.has_column("Journal Entry", "imprest_employee"):
        return

    existing = frappe.db.sql(
        """
        show index from `tabJournal Entry`
        where Key_name = 'idx_imprest_employee'
        """
    )
    if existing:
        return

    frappe.db.sql(
        """
        alter table `tabJournal Entry`
        add index `idx_imprest_employee` (`imprest_employee`)
        """
    )
