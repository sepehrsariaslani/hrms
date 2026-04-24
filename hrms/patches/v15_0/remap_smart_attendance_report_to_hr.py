import frappe


def execute():
	if not frappe.db.exists("Report", "Smart Attendance Report"):
		return

	frappe.db.set_value(
		"Report",
		"Smart Attendance Report",
		{
			"module": "HR",
			"report_name": "گزارش حضور و غیاب هوشمند",
			"ref_doctype": "Employee Checkin",
			"is_standard": "Yes",
		},
	)
