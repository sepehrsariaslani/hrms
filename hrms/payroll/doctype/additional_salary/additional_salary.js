// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Additional Salary", {
	setup: function (frm) {
		frm.add_fetch(
			"salary_component",
			"deduct_full_tax_on_selected_payroll_date",
			"deduct_full_tax_on_selected_payroll_date",
		);

		frm.set_query("employee", function () {
			return {
				filters: {
					company: frm.doc.company,
					status: ["!=", "Inactive"],
				},
			};
		});
	},

	onload: function (frm) {
		frm.trigger("set_component_query");
		frm.trigger("toggle_amount_source");
	},

	employee: function (frm) {
		if (frm.doc.employee) {
			frappe.run_serially([
				() => frm.trigger("get_employee_currency"),
				() => frm.trigger("set_company"),
			]);
		} else {
			frm.set_value("company", null);
		}
	},

	set_company: function (frm) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Employee",
				fieldname: "company",
				filters: {
					name: frm.doc.employee,
				},
			},
			callback: function (data) {
				if (data.message) {
					frm.set_value("company", data.message.company);
					frm.trigger("refresh_hourly_amount");
				}
			},
		});
	},

	company: function (frm) {
		frm.trigger("set_component_query");
		frm.trigger("refresh_hourly_amount");
	},

	set_component_query: function (frm) {
		if (!frm.doc.company) return;

		frm.set_query("salary_component", function () {
			return {
				filters: {
					disabled: 0,
				},
			};
		});
	},

	get_employee_currency: function (frm) {
		frappe.call({
			method: "hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment.get_employee_currency",
			args: {
				employee: frm.doc.employee,
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value("currency", r.message);
					frm.refresh_fields();
				}
			},
		});
	},

	salary_component: function (frm) {
		frm.trigger("set_default_hour_rate_type");
		if (!frm.doc.ref_doctype) {
			frm.trigger("get_salary_component_amount");
		}
	},

	amount_calculation_type: function (frm) {
		frm.trigger("toggle_amount_source");
	},

	hour_rate_type: function (frm) {
		frm.trigger("refresh_hourly_amount");
	},

	hours: function (frm) {
		frm.trigger("refresh_hourly_amount");
	},

	payroll_date: function (frm) {
		frm.trigger("refresh_hourly_amount");
	},

	from_date: function (frm) {
		frm.trigger("refresh_hourly_amount");
	},

	to_date: function (frm) {
		frm.trigger("refresh_hourly_amount");
	},

	get_salary_component_amount: function (frm) {
		if (frm.doc.amount_calculation_type === "Hours") {
			frm.trigger("refresh_hourly_amount");
			return;
		}

		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Salary Component",
				fieldname: "amount",
				filters: {
					name: frm.doc.salary_component,
				},
			},
			callback: function (data) {
				if (data.message) {
					frm.set_value("amount", data.message.amount);
				}
			},
		});
	},

	set_default_hour_rate_type: function (frm) {
		if (frm.doc.amount_calculation_type !== "Hours" || !frm.doc.type) return;

		const default_rate_type =
			frm.doc.type === "Deduction" ? "Ordinary Hour Rate" : "Overtime Hour Rate";
		if (frm.doc.hour_rate_type !== default_rate_type) {
			frm.set_value("hour_rate_type", default_rate_type);
		}
	},

	toggle_amount_source: function (frm) {
		const is_hourly = frm.doc.amount_calculation_type === "Hours";
		frm.toggle_enable("amount", !is_hourly);
		if (is_hourly) {
			frm.trigger("set_default_hour_rate_type");
			frm.trigger("refresh_hourly_amount");
		}
	},

	refresh_hourly_amount: function (frm) {
		if (frm.doc.amount_calculation_type !== "Hours") return;
		if (!frm.doc.employee || !frm.doc.company) return;

		const reference_date = frm.doc.payroll_date || frm.doc.from_date || frm.doc.to_date;
		if (!reference_date) return;

		frappe.call({
			method: "hrms.payroll.doctype.additional_salary.additional_salary.get_hourly_additional_salary_details",
			args: {
				employee: frm.doc.employee,
				company: frm.doc.company,
				reference_date,
				hour_rate_type: frm.doc.hour_rate_type,
				hours: frm.doc.hours || 0,
			},
			callback: function (r) {
				if (!r.message) return;
				frm.set_value("hour_rate", r.message.hour_rate || 0);
				frm.set_value("amount", r.message.amount || 0);
			},
		});
	},
});
