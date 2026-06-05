import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_imprest_custom_fields()
	create_payment_entry_index()


def create_imprest_custom_fields():
	create_custom_fields(
		{
			"Employee": [
				{
					"fieldname": "has_imprest",
					"fieldtype": "Check",
					"label": "Has Imprest",
					"default": "0",
					"insert_after": "expense_approver",
				},
				{
					"fieldname": "imprest_accounts",
					"fieldtype": "Table",
					"label": "Imprest Accounts",
					"options": "Employee Imprest Account",
					"depends_on": "eval:doc.has_imprest==1",
					"insert_after": "has_imprest",
				},
			],
			"Payment Entry": [
				{
					"fieldname": "imprest_employee",
					"fieldtype": "Link",
					"label": "Imprest Employee",
					"options": "Employee",
					"insert_after": "party",
					"in_list_view": 1,
					"in_standard_filter": 1,
				},
			],
		},
		ignore_validate=True,
		update=True,
	)


def create_payment_entry_index():
	if not frappe.db.has_column("Payment Entry", "imprest_employee"):
		return

	existing = frappe.db.sql(
		"""
		show index from `tabPayment Entry`
		where Key_name = 'idx_imprest_employee'
		"""
	)
	if existing:
		return

	frappe.db.sql(
		"""
		alter table `tabPayment Entry`
		add index `idx_imprest_employee` (`imprest_employee`)
		"""
	)
