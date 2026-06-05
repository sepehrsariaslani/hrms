import frappe


WORKSPACE_LAYOUT = {
	"Human Resources": {
		"label": "Human Resources",
		"title": "Human Resources",
		"parent_page": "",
		"module": "HR",
		"icon": "hr",
		"sequence_id": 13,
		"public": 1,
		"is_hidden": 0,
	},
	"Recruitment": {
		"parent_page": "Human Resources",
		"module": "HR",
		"icon": "users",
		"sequence_id": 14,
	},
	"Leaves": {
		"parent_page": "Human Resources",
		"module": "HR",
		"icon": "non-profit",
		"sequence_id": 15,
	},
	"Performance": {
		"label": "Performance",
		"title": "Performance",
		"parent_page": "Human Resources",
		"module": "HR",
		"icon": "star",
		"sequence_id": 16,
	},
	"Tax & Benefits": {
		"parent_page": "Human Resources",
		"module": "Payroll",
		"icon": "money-coins-1",
		"sequence_id": 17,
	},
	"Salary Payout": {
		"parent_page": "Human Resources",
		"module": "Payroll",
		"icon": "accounting",
		"sequence_id": 18,
	},
	"Expense Claims": {
		"parent_page": "Human Resources",
		"module": "HR",
		"icon": "expenses",
		"sequence_id": 19,
	},
	"Employee Lifecycle": {
		"parent_page": "Human Resources",
		"module": "HR",
		"icon": "customer",
		"sequence_id": 20,
	},
	"Shift & Attendance": {
		"parent_page": "Employee Lifecycle",
		"module": "HR",
		"icon": "milestone",
		"sequence_id": 21,
	},
	"HR": {
		"label": "HR",
		"title": "HR",
		"parent_page": "",
		"module": "HR",
		"icon": "hr",
		"sequence_id": 22,
		"public": 1,
		"is_hidden": 0,
	},
	"Payroll": {
		"label": "Payroll",
		"title": "Payroll",
		"parent_page": "",
		"module": "Payroll",
		"icon": "money-coins-1",
		"sequence_id": 15,
		"public": 1,
		"is_hidden": 0,
	},
}


def execute():
	ensure_human_resources_workspace()
	apply_workspace_layout()


def ensure_human_resources_workspace():
	if frappe.db.exists("Workspace", "Human Resources"):
		return
	if not frappe.db.exists("Workspace", "HR"):
		return

	source = frappe.get_doc("Workspace", "HR")
	new_workspace = frappe.copy_doc(source)
	new_workspace.name = "Human Resources"
	new_workspace.label = "Human Resources"
	new_workspace.title = "Human Resources"
	new_workspace.parent_page = ""
	new_workspace.module = "HR"
	new_workspace.icon = "hr"
	new_workspace.sequence_id = 13
	new_workspace.public = 1
	new_workspace.is_hidden = 0
	new_workspace.insert(ignore_permissions=True)


def apply_workspace_layout():
	for workspace_name, field_map in WORKSPACE_LAYOUT.items():
		if not frappe.db.exists("Workspace", workspace_name):
			continue

		workspace = frappe.get_doc("Workspace", workspace_name)
		updated = False

		for fieldname, value in field_map.items():
			if fieldname == "parent_page":
				value = value or ""
			if workspace.get(fieldname) != value:
				workspace.set(fieldname, value)
				updated = True

		if updated:
			workspace.save(ignore_permissions=True)
