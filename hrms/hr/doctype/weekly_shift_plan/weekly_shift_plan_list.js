frappe.listview_settings["Weekly Shift Plan"] = {
	add_fields: ["status", "week_start_date", "week_end_date", "employee_name", "total_hours"],
	get_indicator(doc) {
		if (doc.status === "Approved") return [__("Approved"), "green", "status,=,Approved"];
		if (doc.status === "Rejected") return [__("Rejected"), "red", "status,=,Rejected"];
		if (doc.status === "Submitted") return [__("Submitted"), "blue", "status,=,Submitted"];
		if (doc.status === "Replaced") return [__("Replaced"), "orange", "status,=,Replaced"];
		return [__("Draft"), "gray", "status,=,Draft"];
	},
};
