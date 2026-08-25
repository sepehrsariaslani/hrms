// Copyright (c) 2026, Iran Utilities
// For license information, please see license.txt

frappe.query_reports["Employee Seniority Base Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("شرکت"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "employee_status",
			label: __("وضعیت کارمند"),
			fieldtype: "Select",
			options: "\nActive\nInactive\nSuspended\nLeft\nOn Leave",
			default: "Active",
		},
	],
};
