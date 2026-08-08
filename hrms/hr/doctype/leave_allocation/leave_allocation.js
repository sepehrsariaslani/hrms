// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// nosemgrep: frappe-semgrep-rules.rules.frappe-cur-frm-usage
cur_frm.add_fetch("employee", "employee_name", "employee_name");

frappe.ui.form.on("Leave Allocation", {
	setup: function (frm) {
		frm.trigger("set_indicator");
	},
	onload: function (frm) {
		// Ignore cancellation of doctype on cancel all.
		frm.ignore_doctypes_on_cancel_all = ["Leave Ledger Entry"];

		if (!frm.doc.from_date) frm.set_value("from_date", frappe.datetime.get_today());

		frm.set_query("employee", function () {
			return {
				query: "erpnext.controllers.queries.employee_query",
			};
		});
		frm.set_query("leave_type", function () {
			return {
				filters: {
					is_lwp: 0,
				},
			};
		});
	},

	refresh: function (frm) {
		hrms.leave_utils.add_view_ledger_button(frm);

		if (frm.doc.docstatus === 1 && !frm.doc.expired) {
			var valid_expiry = moment(frappe.datetime.get_today()).isBetween(
				frm.doc.from_date,
				frm.doc.to_date,
			);
			if (valid_expiry) {
				// expire current allocation
				frm.add_custom_button(
					__("Expire Allocation"),
					function () {
						frappe.confirm("Are you sure you want to expire this allocation?", () => {
							frm.trigger("expire_allocation");
						});
					},
					__("Actions"),
				);
				frm.add_custom_button(
					__("Adjust Allocation"),
					function () {
						const dialog = new frappe.ui.Dialog({
							title: "Leave Adjustment",
							fields: [
								{
									label: "Adjustment Type",
									fieldname: "adjustment_type",
									fieldtype: "Select",
									options: "Allocate\nReduce",
									reqd: 1,
								},
								{
									label: "Leaves To Adjust",
									fieldname: "leaves_to_adjust",
									fieldtype: "Float",
									reqd: 1,
								},
								{
									label: "Posting Date (Jalali or Gregorian)",
									fieldname: "posting_date",
									fieldtype: "Data",
									reqd: 1,
									default: getAdjustmentPostingDateDefault(),
								},
								{
									label: "Reason for Adjustment",
									fieldname: "reason_for_adjustment",
									fieldtype: "Small Text",
								},
							],
							primary_action_label: "Adjust Leaves",
							primary_action(values) {
								values.posting_date =
									normalizeAdjustmentPostingDate(values.posting_date) ||
									values.posting_date;
								values.reason_for_adjustment = values.reason_for_adjustment || "";
								frappe.call({
									method: "create_leave_adjustment",
									doc: frm.doc,
									args: values,
									callback: function (r) {
										if (!r.exc) {
											frm.reload_doc();
										}
									},
									always: function (r) {
										dialog.hide();
									},
								});
							},
						});
						dialog.show();
					},
					__("Actions"),
				);
			}
		}
		frm.trigger("set_indicator");
		frm.trigger("toggle_retry_button");
	},

	expire_allocation: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry.expire_allocation",
			args: {
				allocation: frm.doc,
				expiry_date: frappe.datetime.get_today(),
			},
			freeze: true,
			callback: function (r) {
				if (!r.exc) {
					frappe.msgprint(__("Allocation Expired!"));
				}
				frm.refresh();
			},
		});
	},

	employee: function (frm) {
		frm.trigger("calculate_total_leaves_allocated");
	},

	leave_type: function (frm) {
		frm.trigger("leave_policy");
		frm.trigger("calculate_total_leaves_allocated");
	},

	carry_forward: function (frm) {
		frm.trigger("calculate_total_leaves_allocated");
	},

	unused_leaves: function (frm) {
		frm.set_value(
			"total_leaves_allocated",
			flt(frm.doc.unused_leaves) + flt(frm.doc.new_leaves_allocated),
		);
	},

	new_leaves_allocated: function (frm) {
		frm.set_value(
			"total_leaves_allocated",
			flt(frm.doc.unused_leaves) + flt(frm.doc.new_leaves_allocated),
		);
	},

	leave_policy: function (frm) {
		if (frm.doc.leave_policy && frm.doc.leave_type) {
			frappe.db.get_value(
				"Leave Policy Detail",
				{
					parent: frm.doc.leave_policy,
					leave_type: frm.doc.leave_type,
				},
				"annual_allocation",
				(r) => {
					if (r && !r.exc)
						frm.set_value("new_leaves_allocated", flt(r.annual_allocation));
				},
				"Leave Policy",
			);
		}
	},

	toggle_retry_button: function (frm) {
		const earned_leave_schedule = frm.doc.earned_leave_schedule || [];
		let toggle_button =
			earned_leave_schedule.some((row) => row.attempted && row.failed) && frm.perm[0]?.write;
		frm.toggle_display("retry_failed_allocations", toggle_button);
	},

	retry_failed_allocations: function (frm) {
		let failed_allocations = (frm.doc.earned_leave_schedule || []).filter(
			(row) => row.attempted && row.failed,
		);

		frappe.call({
			method: "retry_failed_allocations",
			doc: frm.doc,
			args: { failed_allocations },
			freeze: true,
			freeze_message: __("Retrying allocations"),
			callback: function (r) {
				frappe.show_alert({
					message: __("Retry Successful"),
					indicator: "green",
				});
				frm.reload_doc();
				frm.refresh_field("retry_failed_allocations");
			},
		});
	},
	set_indicator: function (frm) {
		const df = frappe.meta.get_docfield(
			"Earned Leave Schedule",
			"allocation_date",
			frm.doc.name,
		);
		df.formatter = function (value, df, options, row) {
			const formattedValue = formatScheduleAllocationDate(value);
			if (row.attempted && row.failed) {
				return `<span class="indicator red">${formattedValue}</span>`;
			} else if (row.attempted && row.is_allocated) {
				return `<span class="indicator green">${formattedValue}</span>`;
			} else {
				return formattedValue;
			}
		};
		frm.refresh_field("earned_leave_schedule");
	},

	calculate_total_leaves_allocated: function (frm) {
		if (cint(frm.doc.carry_forward) == 1 && frm.doc.leave_type && frm.doc.employee) {
			return frappe.call({
				method: "set_total_leaves_allocated",
				doc: frm.doc,
				callback: function () {
					frm.refresh_fields();
				},
			});
		} else if (cint(frm.doc.carry_forward) == 0) {
			frm.set_value("unused_leaves", 0);
			frm.set_value("total_leaves_allocated", flt(frm.doc.new_leaves_allocated));
		}
	},
});

function getAdjustmentPostingDateDefault() {
	const today = frappe.datetime.get_today();
	if (typeof window.gregorianToPersian === "function") {
		return window.gregorianToPersian(today);
	}
	return today;
}

function normalizeAdjustmentPostingDate(value) {
	if (!value) return null;
	const normalized = String(value)
		.trim()
		.replace(/[۰-۹]/g, (digit) => "۰۱۲۳۴۵۶۷۸۹".indexOf(digit))
		.replace(/[٠-٩]/g, (digit) => "٠١٢٣٤٥٦٧٨٩".indexOf(digit))
		.replace(/-/g, "/");
	const year = cint((normalized.split("/")[0] || "").trim());
	if (year >= 1300 && year <= 1600 && typeof window.persianToGregorian === "function") {
		const converted = window.persianToGregorian(normalized);
		return converted ? converted.split(" ")[0] : null;
	}
	return value;
}

function formatScheduleAllocationDate(value) {
	if (!value) return value;
	if (typeof window.gregorianToPersian === "function") {
		const converted = window.gregorianToPersian(value);
		if (converted) return converted;
	}
	return value;
}

frappe.tour["Leave Allocation"] = [
	{
		fieldname: "employee",
		title: "Employee",
		description: __("Select the Employee for which you want to allocate leaves."),
	},
	{
		fieldname: "leave_type",
		title: "Leave Type",
		description: __(
			"Select the Leave Type like Sick leave, Privilege Leave, Casual Leave, etc.",
		),
	},
	{
		fieldname: "from_date",
		title: "From Date",
		description: __("Select the date from which this Leave Allocation will be valid."),
	},
	{
		fieldname: "to_date",
		title: "To Date",
		description: __("Select the date after which this Leave Allocation will expire."),
	},
	{
		fieldname: "new_leaves_allocated",
		title: "New Leaves Allocated",
		description: __("Enter the number of leaves you want to allocate for the period."),
	},
];
